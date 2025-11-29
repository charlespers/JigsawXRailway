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
        """Select supporting parts (power, passives, etc.) with diversity"""
        db = get_part_database()
        selected = {}
        used_categories = set()
        used_part_ids = set()
        
        # Track anchor part category and ID to avoid duplicates
        anchor_category = anchor_part.get("category", "").lower()
        anchor_id = anchor_part.get("id") or anchor_part.get("mfr_part_number", "")
        if anchor_category:
            used_categories.add(anchor_category)
        if anchor_id:
            used_part_ids.add(anchor_id)
        
        # Extract voltage requirements from anchor
        anchor_voltage = self._extract_voltage(anchor_part)
        
        # Enhanced category mapping for diverse selection
        category_map = {
            "mcu": ComponentCategory.MCU,
            "sensor": ComponentCategory.SENSOR,
            "power": ComponentCategory.POWER,
            "regulator": ComponentCategory.POWER,
            "connector": ComponentCategory.CONNECTOR,
            "passive": ComponentCategory.PASSIVE,
            "capacitor": ComponentCategory.PASSIVE,
            "resistor": ComponentCategory.PASSIVE,
            "inductor": ComponentCategory.PASSIVE,
            "interface": ComponentCategory.INTERFACE,
            "protection": ComponentCategory.PROTECTION,
            "crystal": ComponentCategory.CRYSTAL,
            "oscillator": ComponentCategory.CRYSTAL
        }
        
        for block in block_specs:
            block_type = block.get("type", "").lower()
            block_name = block.get("name", block_type)
            
            # Determine category for this block
            category = None
            for key, cat in category_map.items():
                if key in block_type:
                    category = cat
                    break
            
            # If category already used and we want diversity, try alternative
            category_str = category.value if category else block_type
            if category_str in used_categories and len(block_specs) > 1:
                # Try to find alternative category that fits the block description
                logger.info(f"Category {category_str} already used, looking for alternative for {block_name}")
            
            # Search for candidates
            candidates = []
            if category:
                candidates = db.search_parts(category=category)
            else:
                # Fallback: search all parts and filter by block type keywords
                all_parts = db.get_all_parts()
                for part in all_parts:
                    part_category = part.get("category", "").lower()
                    if block_type in part_category or any(keyword in part_category for keyword in block_type.split()):
                        candidates.append(part)
            
            # Filter out already selected parts
            candidates = [c for c in candidates if (c.get("id") or c.get("mfr_part_number", "")) not in used_part_ids]
            
            # Additional filtering based on block type
            if "power" in block_type or "regulator" in block_type:
                # Filter power parts by voltage compatibility
                if anchor_voltage:
                    filtered = []
                    for part in candidates:
                        part_voltage = self._extract_voltage(part)
                        if part_voltage and (anchor_voltage * 0.7 <= part_voltage <= anchor_voltage * 1.3):
                            filtered.append(part)
                    if filtered:
                        candidates = filtered
            
            # Select best candidate (prioritize in_stock, active lifecycle)
            if candidates:
                # Score candidates
                scored = []
                for candidate in candidates:
                    score = 0
                    # Prefer in-stock parts
                    if candidate.get("availability_status") == "in_stock":
                        score += 10
                    # Prefer active lifecycle
                    if candidate.get("lifecycle_status") == "active":
                        score += 5
                    # Prefer parts with datasheets
                    if candidate.get("datasheet_url"):
                        score += 2
                    scored.append((score, candidate))
                
                # Sort by score and select best
                scored.sort(key=lambda x: x[0], reverse=True)
                selected_part = scored[0][1]
                selected[block_name] = selected_part
                
                # Track used categories and part IDs
                part_category = selected_part.get("category", "").lower()
                part_id = selected_part.get("id") or selected_part.get("mfr_part_number", "")
                if part_category:
                    used_categories.add(part_category)
                if part_id:
                    used_part_ids.add(part_id)
                
                logger.info(f"Selected {selected_part.get('mfr_part_number', 'unknown')} for {block_name} (category: {part_category})")
            else:
                logger.warning(f"No candidates found for block {block_name} (type: {block_type})")
        
        return selected
    
    def _extract_voltage(self, part: Dict[str, Any]) -> Optional[float]:
        """Extract nominal voltage from part"""
        supply_range = part.get("supply_voltage_range", {})
        if isinstance(supply_range, dict):
            return supply_range.get("nominal") or supply_range.get("max")
        return None

