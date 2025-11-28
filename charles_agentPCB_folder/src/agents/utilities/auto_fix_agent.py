"""
Auto-Fix Agent
Suggests parts to fix design validation issues with intelligent matching
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from requests.exceptions import Timeout as RequestsTimeout

from utils.part_database import search_parts, get_all_parts

# Add development_demo/utils to path for config access
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from utils.config import load_config
except ImportError:
    load_config = None


class AutoFixAgent:
    """Suggests parts to fix design validation issues with intelligent matching."""
    
    def __init__(self):
        """Initialize with LLM configuration for intelligent fixes."""
        if load_config:
            try:
                config = load_config()
                self.api_key = config.get("api_key")
                self.endpoint = config.get("endpoint")
                self.model = config.get("model")
                self.temperature = config.get("temperature", 0.2)
                # Only use config if it's for xAI
                if config.get("provider", "xai").lower() == "xai":
                    self.api_key = config.get("api_key") or os.getenv("XAI_API_KEY")
                    self.endpoint = config.get("endpoint") or "https://api.x.ai/v1/chat/completions"
                    self.model = config.get("model") or os.getenv("XAI_MODEL", "grok-3")
                    self.temperature = config.get("temperature") or float(os.getenv("XAI_TEMPERATURE", "0.2"))
                    self.provider = "xai"
                else:
                    # Force xAI
                    self.api_key = os.getenv("XAI_API_KEY")
                    self.endpoint = "https://api.x.ai/v1/chat/completions"
                    self.model = os.getenv("XAI_MODEL", "grok-3")
                    self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.2"))
                    self.provider = "xai"
            except Exception:
                # Fallback to environment - always xAI
                self.api_key = os.getenv("XAI_API_KEY")
                self.endpoint = "https://api.x.ai/v1/chat/completions"
                self.model = os.getenv("XAI_MODEL", "grok-3")
                self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.2"))
                self.provider = "xai"
        else:
            # Read from environment - always xAI
            self.api_key = os.getenv("XAI_API_KEY")
            self.endpoint = "https://api.x.ai/v1/chat/completions"
            self.model = os.getenv("XAI_MODEL", "grok-3")
            self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.2"))
            self.provider = "xai"
        
        if self.api_key:
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        else:
            self.headers = None
    
    def suggest_fixes(
        self,
        validation_issues: List[Dict[str, Any]],
        bom_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Suggest parts to fix validation issues.
        
        Args:
            validation_issues: List of validation issues from DesignValidatorAgent
            bom_items: Current BOM items
        
        Returns:
            List of suggested fixes with part recommendations
        """
        suggestions = []
        
        for issue in validation_issues:
            issue_type = issue.get("type")
            message = issue.get("message", "")
            
            if issue_type == "missing_component":
                if "power regulator" in message.lower():
                    # Suggest power regulators
                    regulators = search_parts(category="regulator_ldo")
                    regulators.extend(search_parts(category="regulator_buck"))
                    
                    if regulators:
                        suggestions.append({
                            "issue": issue,
                            "suggested_parts": regulators[:3],  # Top 3 suggestions
                            "fix_type": "add_power_regulator",
                            "description": "Add a power regulator for power management"
                        })
                
                elif "decoupling" in message.lower() or "capacitor" in message.lower():
                    # Suggest decoupling capacitors
                    capacitors = search_parts(category="capacitor")
                    # Filter for common decoupling values
                    decoupling_caps = [
                        c for c in capacitors 
                        if c.get("capacitance", {}).get("value") in [0.1, 1.0, 10.0]
                    ]
                    
                    if decoupling_caps:
                        suggestions.append({
                            "issue": issue,
                            "suggested_parts": decoupling_caps[:3],
                            "fix_type": "add_decoupling_capacitor",
                            "description": "Add decoupling capacitors for power supply stability"
                        })
                
                elif "protection" in message.lower() or "esd" in message.lower() or "tvs" in message.lower():
                    # Suggest protection components
                    protection = search_parts(category="protection_tvs")
                    protection.extend(search_parts(category="protection_esd"))
                    protection.extend(search_parts(category="protection_polyfuse"))
                    
                    if protection:
                        suggestions.append({
                            "issue": issue,
                            "suggested_parts": protection[:3],
                            "fix_type": "add_protection",
                            "description": "Add ESD/TVS protection components"
                        })
            
            elif issue_type == "power_budget":
                # Suggest higher capacity regulators
                regulators = search_parts(category="regulator_buck")
                regulators.extend(search_parts(category="regulator_ldo"))
                
                # Sort by current capacity
                regulators.sort(key=lambda x: (
                    x.get("current_max", {}).get("max", 0) 
                    if isinstance(x.get("current_max"), dict) 
                    else x.get("current_max", 0)
                ), reverse=True)
                
                if regulators:
                    suggestions.append({
                        "issue": issue,
                        "suggested_parts": regulators[:3],
                        "fix_type": "upgrade_regulator",
                        "description": "Consider a higher capacity regulator"
                    })
        
        return suggestions
    
    def suggest_missing_footprints(self, bom_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest parts with proper IPC-7351 footprints."""
        suggestions = []
        
        for item in bom_items:
            part = item.get("part_data", {})
            if not part.get("footprint"):
                # Try to find similar parts with footprints
                category = part.get("category", "")
                similar = search_parts(category=category)
                
                # Filter for parts with footprints
                with_footprints = [p for p in similar if p.get("footprint")]
                
                if with_footprints:
                    suggestions.append({
                        "part_id": part.get("id"),
                        "part_name": part.get("name"),
                        "issue": "Missing IPC-7351 footprint designation",
                        "suggested_parts": with_footprints[:3],
                        "fix_type": "add_footprint",
                        "description": "Consider parts with IPC-7351 compliant footprints"
                    })
        
        return suggestions
    
    def suggest_missing_msl(self, bom_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest ICs with MSL levels specified."""
        suggestions = []
        
        for item in bom_items:
            part = item.get("part_data", {})
            category = part.get("category", "")
            
            # Only check ICs and MCUs
            if "ic" in category or "mcu" in category or "sensor" in category:
                if not part.get("msl_level") and not part.get("moisture_sensitivity_level"):
                    # Try to find similar parts with MSL
                    similar = search_parts(category=category)
                    
                    # Filter for parts with MSL
                    with_msl = [p for p in similar if p.get("msl_level") or p.get("moisture_sensitivity_level")]
                    
                    if with_msl:
                        suggestions.append({
                            "part_id": part.get("id"),
                            "part_name": part.get("name"),
                            "issue": "Missing MSL level - required for assembly planning",
                            "suggested_parts": with_msl[:3],
                            "fix_type": "add_msl",
                            "description": "Consider parts with MSL levels specified"
                        })
        
        return suggestions

