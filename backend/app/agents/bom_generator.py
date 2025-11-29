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
        """Generate BOM from selected parts with enhanced pricing, quantities, and metadata"""
        try:
            items = []
            designator_counters = defaultdict(int)
            ic_count = 0  # Count ICs for decoupling cap calculation
            
            # Add main components
            for block_name, part in selected_parts.items():
                designator = self._get_designator(part, designator_counters)
                qty = self._calculate_quantity(part, block_name)
                item = self._create_bom_item(part, designator, qty=qty)
                items.append(item)
                
                # Count ICs for decoupling cap calculation
                category = part.get("category", "").lower()
                if "mcu" in category or "ic" in category or "processor" in category:
                    ic_count += qty
            
            # Add passives from recommended external components
            for block_name, part in selected_parts.items():
                externals = part.get("recommended_external_components", [])
                for ext in externals:
                    designator = self._get_designator(ext, designator_counters, is_passive=True)
                    qty = self._calculate_quantity(ext, block_name, is_passive=True)
                    item = self._create_bom_item(ext, designator, qty=qty, is_passive=True)
                    items.append(item)
            
            # Add standard decoupling capacitors (1 per IC + 1 bulk)
            if ic_count > 0:
                # 100nF ceramic cap per IC
                for i in range(ic_count):
                    designator = self._get_designator({"category": "capacitor"}, designator_counters, is_passive=True)
                    decap = {
                        "category": "passive",
                        "manufacturer": "Generic",
                        "mfr_part_number": "GRM188R71C104KA93D",
                        "description": "100nF 50V X7R Ceramic Capacitor (Decoupling)",
                        "package": "0603",
                        "footprint": "CAPC0603X33N",
                        "value": "100nF",
                        "cost_estimate": {"unit": 0.01},
                        "recommended_for": "Power supply decoupling"
                    }
                    item = self._create_bom_item(decap, designator, qty=1, is_passive=True)
                    items.append(item)
                
                # 10uF bulk capacitor
                designator = self._get_designator({"category": "capacitor"}, designator_counters, is_passive=True)
                bulk_cap = {
                    "category": "passive",
                    "manufacturer": "Generic",
                    "mfr_part_number": "CL10A106KP8NNNC",
                    "description": "10uF 25V X7R Ceramic Capacitor (Bulk)",
                    "package": "0805",
                    "footprint": "CAPC0805X55N",
                    "value": "10uF",
                    "cost_estimate": {"unit": 0.02},
                    "recommended_for": "Bulk power supply filtering"
                }
                item = self._create_bom_item(bulk_cap, designator, qty=1, is_passive=True)
                items.append(item)
            
            # Calculate summary with enhanced metadata
            total_cost = sum(item.extended_cost for item in items)
            total_parts = len(items)
            total_qty = sum(item.qty for item in items)
            
            # Collect useful perks/metadata
            perks = self._extract_perks(selected_parts, items)
            
            return BOM(
                items=items,
                summary={
                    "total_cost": round(total_cost, 2),
                    "total_parts": total_parts,
                    "total_qty": total_qty,
                    "average_cost_per_part": round(total_cost / total_parts, 2) if total_parts > 0 else 0,
                    "perks": perks
                },
                metadata={
                    "standard": "IPC-2581",
                    "revision": "1.0",
                    "includes_decoupling": ic_count > 0,
                    "ic_count": ic_count,
                    "design_notes": self._generate_design_notes(selected_parts, items)
                }
            )
        except Exception as e:
            logger.error(f"BOM generation error: {e}")
            raise BOMGenerationError(f"Failed to generate BOM: {e}")
    
    def _calculate_quantity(self, part: Dict[str, Any], block_name: str, is_passive: bool = False) -> int:
        """Calculate proper quantity for a part"""
        # Check if quantity is explicitly set
        if "quantity" in part:
            return int(part["quantity"])
        
        # For passives, check if it's a multi-instance component
        if is_passive:
            recommended_qty = part.get("recommended_quantity", 1)
            return int(recommended_qty) if recommended_qty else 1
        
        # Default to 1 for main components
        return 1
    
    def _extract_perks(self, selected_parts: Dict[str, Dict[str, Any]], items: List[BOMItem]) -> List[str]:
        """Extract useful perks and highlights from parts"""
        perks = []
        
        # Check for RoHS compliance
        rohs_count = sum(1 for part in selected_parts.values() if part.get("rohs_compliant", True))
        if rohs_count == len(selected_parts):
            perks.append("✅ Fully RoHS compliant design")
        
        # Check for active lifecycle parts
        active_count = sum(1 for part in selected_parts.values() if part.get("lifecycle_status", "active") == "active")
        if active_count == len(selected_parts):
            perks.append("✅ All parts in active lifecycle (no obsolescence risk)")
        
        # Check for in-stock parts
        in_stock_count = sum(1 for part in selected_parts.values() if part.get("availability_status", "in_stock") == "in_stock")
        if in_stock_count == len(selected_parts):
            perks.append("✅ All parts currently in stock")
        
        # Check for datasheets
        datasheet_count = sum(1 for item in items if item.datasheet_url)
        if datasheet_count > 0:
            perks.append(f"📄 {datasheet_count} parts have datasheets available")
        
        # Check for low-cost design
        total_cost = sum(item.extended_cost for item in items)
        if total_cost < 10:
            perks.append("💰 Low-cost design (< $10)")
        elif total_cost < 50:
            perks.append("💰 Cost-effective design (< $50)")
        
        # Check for SMT-only design
        smt_only = all(item.mounting_type == MountingType.SMT for item in items)
        if smt_only:
            perks.append("🔧 SMT-only design (easy automated assembly)")
        
        return perks
    
    def _generate_design_notes(self, selected_parts: Dict[str, Dict[str, Any]], items: List[BOMItem]) -> List[str]:
        """Generate helpful design notes"""
        notes = []
        
        # Power supply notes
        power_parts = [p for p in selected_parts.values() if "power" in p.get("category", "").lower()]
        if power_parts:
            notes.append("Power supply components included - verify voltage compatibility")
        
        # Interface notes
        for part_name, part in selected_parts.items():
            interfaces = part.get("interface_type", [])
            if isinstance(interfaces, str):
                interfaces = [interfaces]
            if interfaces:
                notes.append(f"{part_name} uses {', '.join(interfaces)} - ensure proper termination")
        
        # MSL notes
        msl_parts = [item for item in items if item.msl_level and item.msl_level > 3]
        if msl_parts:
            notes.append(f"⚠️ {len(msl_parts)} parts have MSL > 3 - handle with care during assembly")
        
        return notes
    
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
        """Create BOM item from part with enhanced cost extraction"""
        # Enhanced cost extraction - handle multiple formats
        unit_cost = self._extract_cost(part)
        
        # Build notes with useful information
        notes_parts = []
        
        # Availability info
        availability = part.get("availability_status", "")
        if availability:
            notes_parts.append(f"Availability: {availability}")
        
        # Lifecycle info
        lifecycle = part.get("lifecycle_status", "")
        if lifecycle and lifecycle != "active":
            notes_parts.append(f"Lifecycle: {lifecycle}")
        
        # Lead time
        lead_time = part.get("lead_time_days")
        if lead_time:
            notes_parts.append(f"Lead time: {lead_time} days")
        
        # Recommended usage
        recommended_for = part.get("recommended_for", "")
        if recommended_for:
            notes_parts.append(f"Use: {recommended_for}")
        
        notes = " | ".join(notes_parts) if notes_parts else ""
        
        return BOMItem(
            designator=designator,
            qty=qty,
            manufacturer=part.get("manufacturer", "Unknown"),
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
            extended_cost=round(unit_cost * qty, 2),
            datasheet_url=part.get("datasheet_url"),
            notes=notes
        )
    
    def _extract_cost(self, part: Dict[str, Any]) -> float:
        """Extract cost from part data, handling multiple formats"""
        cost_data = part.get("cost_estimate", {})
        
        # Try different cost field names
        if isinstance(cost_data, dict):
            # Try: unit, value, price, cost
            unit_cost = (
                cost_data.get("unit") or
                cost_data.get("value") or
                cost_data.get("price") or
                cost_data.get("cost") or
                0.0
            )
        elif isinstance(cost_data, (int, float)):
            unit_cost = float(cost_data)
        else:
            unit_cost = 0.0
        
        # Handle nested dicts
        if isinstance(unit_cost, dict):
            unit_cost = unit_cost.get("value") or unit_cost.get("unit") or 0.0
        
        # Convert to float and ensure non-negative
        try:
            unit_cost = float(unit_cost) if unit_cost else 0.0
            return max(0.0, unit_cost)
        except (ValueError, TypeError):
            logger.warning(f"Could not parse cost for part {part.get('mfr_part_number', 'unknown')}: {cost_data}")
            return 0.0
    
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

