"""
Part selection agent
Selects compatible parts from database based on requirements
"""
import logging
from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent
from app.domain.part_database import get_part_database
from app.domain.models import ComponentCategory, Part
from app.core.exceptions import PartSelectionError

logger = logging.getLogger(__name__)


class PartSelectionAgent(BaseAgent):
    """Selects compatible parts from database"""
    
    def select_anchor_part(
        self,
        block_spec: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Select anchor part (main component)"""
        db = get_part_database()
        
        # Determine category
        block_type = block_spec.get("type", "").lower()
        category_map = {
            "mcu": ComponentCategory.MCU,
            "sensor": ComponentCategory.SENSOR,
            "power": ComponentCategory.POWER,
            "connector": ComponentCategory.CONNECTOR
        }
        category = None
        for key, cat in category_map.items():
            if key in block_type:
                category = cat
                break
        
        # Search by category
        candidates = db.search_parts(category=category) if category else db.get_all_parts()
        
        # Filter by interface requirements
        if requirements.get("interface_requirements"):
            filtered = []
            for part in candidates:
                part_interfaces = part.get("interface_type", [])
                if isinstance(part_interfaces, str):
                    part_interfaces = [part_interfaces]
                if any(iface.lower() in [i.lower() for i in part_interfaces] 
                       for iface in requirements["interface_requirements"]):
                    filtered.append(part)
            if filtered:
                candidates = filtered
        
        # Return first match (in production, use scoring/ranking)
        return candidates[0] if candidates else None
    
    def select_supporting_parts(
        self,
        anchor_part: Dict[str, Any],
        block_specs: List[Dict[str, Any]],
        requirements: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Select supporting parts (power, passives, etc.)"""
        db = get_part_database()
        selected = {}
        
        # Extract voltage requirements from anchor
        anchor_voltage = self._extract_voltage(anchor_part)
        
        for block in block_specs:
            block_type = block.get("type", "").lower()
            block_name = block.get("name", block_type)
            
            if "power" in block_type or "regulator" in block_type:
                # Select power regulator
                candidates = db.search_parts(
                    category=ComponentCategory.POWER,
                    voltage_range=(anchor_voltage * 0.8, anchor_voltage * 1.2) if anchor_voltage else None
                )
                if candidates:
                    selected[block_name] = candidates[0]
            
            elif "connector" in block_type:
                # Select connector
                candidates = db.search_parts(category=ComponentCategory.CONNECTOR)
                if candidates:
                    selected[block_name] = candidates[0]
            
            elif "passive" in block_type or "capacitor" in block_type:
                # Select passives (simplified - in production use proper selection)
                candidates = db.search_parts(category=ComponentCategory.PASSIVE)
                if candidates:
                    selected[block_name] = candidates[0]
        
        return selected
    
    def _extract_voltage(self, part: Dict[str, Any]) -> Optional[float]:
        """Extract nominal voltage from part"""
        supply_range = part.get("supply_voltage_range", {})
        if isinstance(supply_range, dict):
            return supply_range.get("nominal") or supply_range.get("max")
        return None

