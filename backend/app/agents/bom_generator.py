"""
BOM generator agent
Generates IPC-2581 compliant Bill of Materials
"""
import logging
from typing import Dict, Any, List
from collections import defaultdict
from app.domain.models import BOM, BOMItem, NetConnection, MountingType
from app.core.exceptions import BOMGenerationError

logger = logging.getLogger(__name__)


class BOMGenerator:
    """Generates IPC-2581 compliant BOM"""
    
    def generate(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        connections: List[NetConnection]
    ) -> BOM:
        """Generate BOM from selected parts"""
        try:
            items = []
            designator_counters = defaultdict(int)
            
            # Add main components
            for block_name, part in selected_parts.items():
                designator = self._get_designator(part, designator_counters)
                item = self._create_bom_item(part, designator, qty=1)
                items.append(item)
            
            # Add passives from recommended external components
            for block_name, part in selected_parts.items():
                externals = part.get("recommended_external_components", [])
                for ext in externals:
                    designator = self._get_designator(ext, designator_counters, is_passive=True)
                    item = self._create_bom_item(ext, designator, qty=1, is_passive=True)
                    items.append(item)
            
            # Calculate summary
            total_cost = sum(item.extended_cost for item in items)
            total_parts = len(items)
            total_qty = sum(item.qty for item in items)
            
            return BOM(
                items=items,
                summary={
                    "total_cost": round(total_cost, 2),
                    "total_parts": total_parts,
                    "total_qty": total_qty
                },
                metadata={
                    "standard": "IPC-2581",
                    "revision": "1.0"
                }
            )
        except Exception as e:
            logger.error(f"BOM generation error: {e}")
            raise BOMGenerationError(f"Failed to generate BOM: {e}")
    
    def _get_designator(
        self,
        part: Dict[str, Any],
        counters: defaultdict,
        is_passive: bool = False
    ) -> str:
        """Get designator (U1, R1, C1, etc.)"""
        category = part.get("category", "").lower()
        
        if is_passive or "passive" in category:
            if "capacitor" in category or "cap" in category:
                prefix = "C"
            elif "resistor" in category or "res" in category:
                prefix = "R"
            elif "inductor" in category:
                prefix = "L"
            else:
                prefix = "R"
        elif "mcu" in category or "ic" in category:
            prefix = "U"
        elif "connector" in category:
            prefix = "J"
        elif "crystal" in category:
            prefix = "Y"
        else:
            prefix = "U"
        
        counters[prefix] += 1
        return f"{prefix}{counters[prefix]}"
    
    def _create_bom_item(
        self,
        part: Dict[str, Any],
        designator: str,
        qty: int = 1,
        is_passive: bool = False
    ) -> BOMItem:
        """Create BOM item from part"""
        cost = part.get("cost_estimate", {})
        unit_cost = cost.get("unit") or cost.get("value") or 0.0
        if isinstance(unit_cost, dict):
            unit_cost = unit_cost.get("value", 0.0)
        unit_cost = float(unit_cost) if unit_cost else 0.0
        
        return BOMItem(
            designator=designator,
            qty=qty,
            manufacturer=part.get("manufacturer", ""),
            mfr_part_number=part.get("mfr_part_number", ""),
            description=part.get("description", ""),
            category=part.get("category", ""),
            package=part.get("package", ""),
            footprint=part.get("footprint", ""),
            value=part.get("value"),
            tolerance=part.get("tolerance"),
            mounting_type=MountingType.SMT,
            assembly_side="top",
            msl_level=part.get("msl_level"),
            unit_cost=unit_cost,
            extended_cost=unit_cost * qty,
            datasheet_url=part.get("datasheet_url"),
            notes=""
        )
    
    def generate_connections(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        architecture: Dict[str, Any]
    ) -> List[NetConnection]:
        """Generate netlist connections"""
        connections = []
        power_nets = defaultdict(list)
        
        # Build power connections
        for block_name, part in selected_parts.items():
            pinout = part.get("pinout", {})
            part_id = part.get("id", block_name)
            
            for pin_name, pin_desc in pinout.items():
                pin_upper = pin_name.upper()
                if "VDD" in pin_upper or "VCC" in pin_upper or "3V3" in pin_upper:
                    power_nets["3V3"].append([part_id, pin_name])
                elif "5V" in pin_upper or "VBUS" in pin_upper:
                    power_nets["5V"].append([part_id, pin_name])
                elif "GND" in pin_upper or "GROUND" in pin_upper:
                    power_nets["GND"].append([part_id, pin_name])
        
        # Convert to NetConnection objects
        for net_name, conns in power_nets.items():
            net_class = "power" if net_name != "GND" else "ground"
            connections.append(NetConnection(
                net_name=net_name,
                net_class=net_class,
                connections=conns
            ))
        
        return connections

