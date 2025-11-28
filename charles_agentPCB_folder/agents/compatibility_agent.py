"""
Compatibility & Constraint Checking Agent
Verifies electrical, mechanical, interface, and lifecycle compatibility
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from requests.exceptions import Timeout as RequestsTimeout

# Add development_demo/utils to path for config access
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from utils.config import load_config
except ImportError:
    # Fallback: try to load from environment directly
    load_config = None


class CompatibilityAgent:
    """Agent that checks compatibility between parts."""
    
    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager
        # Don't initialize API keys here - do it lazily
        # This allows the provider to be set in the environment before use
        self._initialized = False
        self.api_key = None
        self.endpoint = None
        self.model = None
        self.temperature = None
        self.provider = None
        self.headers = None
    
    def _ensure_initialized(self):
        """Lazily initialize API configuration based on current environment."""
        if self._initialized:
            return
        
        if load_config:
            try:
                config = load_config()
                self.api_key = config.get("api_key")
                self.endpoint = config.get("endpoint")
                self.model = config.get("model")
                self.temperature = config.get("temperature")
                self.provider = config.get("provider", "openai")
            except Exception as e:
                provider = os.getenv("LLM_PROVIDER", "openai").lower()
                if provider == "xai":
                    self.api_key = os.getenv("XAI_API_KEY")
                    self.endpoint = "https://api.x.ai/v1/chat/completions"
                    self.model = os.getenv("XAI_MODEL", "grok-3")
                    self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.2"))
                else:
                    self.api_key = os.getenv("OPENAI_API_KEY")
                    self.endpoint = "https://api.openai.com/v1/chat/completions"
                    self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                    self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
                self.provider = provider
        else:
            provider = os.getenv("LLM_PROVIDER", "openai").lower()
            if provider == "xai":
                self.api_key = os.getenv("XAI_API_KEY")
                self.endpoint = "https://api.x.ai/v1/chat/completions"
                self.model = os.getenv("XAI_MODEL", "grok-3")
                self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.2"))
            else:
                self.api_key = os.getenv("OPENAI_API_KEY")
                self.endpoint = "https://api.openai.com/v1/chat/completions"
                self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
            self.provider = provider
        
        if not self.api_key:
            provider_name = "XAI" if self.provider == "xai" else "OpenAI"
            raise ValueError(f"{provider_name}_API_KEY not found.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        self._initialized = True
    
    def check_compatibility(
        self,
        part_a: Dict[str, Any],
        part_b: Dict[str, Any],
        connection_type: str = "power"
    ) -> Dict[str, Any]:
        """
        Check compatibility between two parts.
        
        Args:
            part_a: First part (typically driver/source)
            part_b: Second part (typically receiver/load)
            connection_type: Type of connection ("power", "signal", "interface")
        
        Returns:
            {
                "compatible": bool,
                "reasoning": str,
                "risks": List[str],
                "required_buffers": List[str],
                "warnings": List[str]
            }
        """
        # Check cache first
        if self.cache_manager:
            part_a_id = part_a.get("id", "")
            part_b_id = part_b.get("id", "")
            cache_key = f"compatibility:{part_a_id}:{part_b_id}:{connection_type}"
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        # Rule-based checks first
        rule_result = self._rule_based_check(part_a, part_b, connection_type)
        
        # If rule-based check is conclusive, cache and return it
        if rule_result["compatible"] is not None:
            # Cache result
            if self.cache_manager:
                part_a_id = part_a.get("id", "")
                part_b_id = part_b.get("id", "")
                cache_key = f"compatibility:{part_a_id}:{part_b_id}:{connection_type}"
                self.cache_manager.set(cache_key, rule_result, ttl=86400)  # 24 hours
            return rule_result
        
        # Otherwise use LLM for complex cases
        # Ensure initialized before LLM call
        self._ensure_initialized()
        llm_result = self._llm_based_check(part_a, part_b, connection_type)
        
        # Cache LLM result
        if self.cache_manager:
            part_a_id = part_a.get("id", "")
            part_b_id = part_b.get("id", "")
            cache_key = f"compatibility:{part_a_id}:{part_b_id}:{connection_type}"
            self.cache_manager.set(cache_key, llm_result, ttl=86400)  # 24 hours
        
        return llm_result
    
    def _rule_based_check(
        self,
        part_a: Dict[str, Any],
        part_b: Dict[str, Any],
        connection_type: str
    ) -> Dict[str, Any]:
        """Rule-based compatibility checking."""
        risks = []
        warnings = []
        required_buffers = []
        
        if connection_type == "power":
            # Check voltage compatibility
            a_output = part_a.get("output_voltage") or part_a.get("supply_voltage_range")
            b_input = part_b.get("supply_voltage_range")
            
            if a_output and b_input:
                if isinstance(a_output, dict):
                    a_voltage = a_output.get("nominal") or a_output.get("value")
                else:
                    a_voltage = a_output
                
                if isinstance(b_input, dict):
                    b_min = b_input.get("min")
                    b_max = b_input.get("max")
                    b_nominal = b_input.get("nominal")
                    
                    if a_voltage and b_min and b_max:
                        if not (b_min <= a_voltage <= b_max):
                            return {
                                "compatible": False,
                                "voltage_mismatch": True,
                                "voltage_gap": {
                                    "source_voltage": a_voltage,
                                    "target_min": b_min,
                                    "target_max": b_max,
                                    "target_nominal": b_nominal
                                },
                                "reasoning": f"Voltage mismatch: {part_a.get('id')} outputs {a_voltage}V but {part_b.get('id')} requires {b_min}-{b_max}V",
                                "risks": ["Voltage out of range"],
                                "required_buffers": [],
                                "warnings": []
                            }
                
                # Check current capability
                a_current = part_a.get("current_max", {})
                b_current = part_b.get("current_max", {})
                
                if isinstance(a_current, dict):
                    a_max = a_current.get("max") or a_current.get("typical", 0)
                else:
                    a_max = a_current or 0
                
                if isinstance(b_current, dict):
                    b_max = b_current.get("max") or b_current.get("typical", 0)
                else:
                    b_max = b_current or 0
                
                if a_max > 0 and b_max > 0 and a_max < b_max:
                    warnings.append(f"{part_a.get('id')} max current ({a_max}A) may be insufficient for {part_b.get('id')} ({b_max}A)")
        
        elif connection_type == "interface":
            # Check interface compatibility
            a_interfaces = part_a.get("interface_type", [])
            b_interfaces = part_b.get("interface_type", [])
            
            if not isinstance(a_interfaces, list):
                a_interfaces = [a_interfaces]
            if not isinstance(b_interfaces, list):
                b_interfaces = [b_interfaces]
            
            # Check if interfaces overlap
            common = set(a_interfaces) & set(b_interfaces)
            if not common:
                return {
                    "compatible": False,
                    "reasoning": f"No common interfaces: {part_a.get('id')} has {a_interfaces}, {part_b.get('id')} has {b_interfaces}",
                    "risks": ["Interface mismatch"],
                    "required_buffers": [],
                    "warnings": []
                }
            
            # Check IO voltage levels
            a_io = part_a.get("io_voltage_levels", {})
            b_io = part_b.get("io_voltage_levels", {})
            
            if a_io and b_io:
                a_high_min = a_io.get("logic_high_min")
                b_high_min = b_io.get("logic_high_min")
                
                if a_high_min and b_high_min:
                    if abs(a_high_min - b_high_min) > 0.5:  # More than 0.5V difference
                        warnings.append("IO voltage levels differ - may need level shifter")
                        required_buffers.append("level_shifter")
        
        # Check operating temperature ranges
        a_temp = part_a.get("operating_temp_range", {})
        b_temp = part_b.get("operating_temp_range", {})
        
        if a_temp and b_temp:
            a_min = a_temp.get("min")
            a_max = a_temp.get("max")
            b_min = b_temp.get("min")
            b_max = b_temp.get("max")
            
            if a_min and b_max and a_min > b_max:
                return {
                    "compatible": False,
                    "reasoning": f"Temperature range mismatch: {part_a.get('id')} min ({a_min}°C) > {part_b.get('id')} max ({b_max}°C)",
                    "risks": ["Operating temperature incompatibility"],
                    "required_buffers": [],
                    "warnings": []
                }
            if a_max and b_min and a_max < b_min:
                return {
                    "compatible": False,
                    "reasoning": f"Temperature range mismatch: {part_a.get('id')} max ({a_max}°C) < {part_b.get('id')} min ({b_min}°C)",
                    "risks": ["Operating temperature incompatibility"],
                    "required_buffers": [],
                    "warnings": []
                }
        
        return {
            "compatible": True,
            "voltage_mismatch": False,
            "reasoning": "Basic compatibility checks passed",
            "risks": risks,
            "required_buffers": required_buffers,
            "warnings": warnings
        }
    
    def _llm_based_check(
        self,
        part_a: Dict[str, Any],
        part_b: Dict[str, Any],
        connection_type: str
    ) -> Dict[str, Any]:
        """LLM-based compatibility checking for complex cases."""
        # Ensure API is initialized (reads provider from environment at runtime)
        self._ensure_initialized()
        
        prompt = f"""
You are a PCB compatibility checking agent. Determine if two parts can be safely connected.

Part A ({connection_type} source):
{json.dumps(part_a, indent=2)}

Part B ({connection_type} receiver):
{json.dumps(part_b, indent=2)}

Connection Type: {connection_type}

Analyze electrical, mechanical, interface, and environmental compatibility. Return ONLY JSON:
{{
  "compatible": true/false,
  "reasoning": "detailed explanation",
  "risks": ["risk1", "risk2"],
  "required_buffers": ["buffer1"] (e.g., "level_shifter", "current_limiter"),
  "warnings": ["warning1", "warning2"]
}}

Return ONLY valid JSON, no additional text.
"""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert PCB compatibility checker. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": 1500,
        }
        
        try:
            # Reduced timeout to prevent blocking (15 seconds instead of 45)
            resp = requests.post(self.endpoint, headers=self.headers, json=payload, timeout=15)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            json_str = self._extract_json(content)
            return json.loads(json_str)
        except RequestsTimeout:
            # Timeout - fallback to rule-based result
            return {
                "compatible": True,
                "reasoning": "LLM check timeout, using rule-based result",
                "risks": [],
                "required_buffers": [],
                "warnings": ["Compatibility check timed out, using rule-based analysis"]
            }
        except Exception as e:
            # Fallback to rule-based result
            return {
                "compatible": True,
                "reasoning": f"LLM check failed, using rule-based result: {str(e)}",
                "risks": [],
                "required_buffers": [],
                "warnings": ["Could not perform detailed compatibility check"]
            }
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from LLM response."""
        if "```" in text:
            start = text.find("```")
            end = text.find("```", start + 3)
            if end > start:
                text = text[start + 3:end]
                if text.startswith("json"):
                    text = text[4:]
        
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx >= 0 and end_idx > start_idx:
            return text[start_idx:end_idx + 1]
        return text
    
    def can_be_resolved_with_intermediary(self, compat_result: Dict[str, Any]) -> bool:
        """
        Check if a compatibility issue can be resolved with an intermediary component.
        
        Args:
            compat_result: Result from check_compatibility()
        
        Returns:
            True if voltage mismatch can be resolved with intermediary
        """
        return compat_result.get("voltage_mismatch", False) is True

