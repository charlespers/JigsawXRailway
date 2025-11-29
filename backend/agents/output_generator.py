"""
Output Generator
Produces connection list (netlist) and BOM
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.testpoint_fiducial_agent import TestPointFiducialAgent
from agents.eda_asset_agent import EDAAssetAgent
from utils.cost_utils import safe_extract_cost, safe_extract_quantity


class OutputGenerator:
    """Generates connection lists and BOMs from selected parts."""
    
    def __init__(self):
        self.testpoint_agent = TestPointFiducialAgent()
        self.eda_asset_agent = EDAAssetAgent()
    
    def generate_connections(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        architecture: Dict[str, Any],
        intermediaries: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate connection list (netlist-like) from selected parts.
        Handles intermediaries by creating connections through them.
        
        Args:
            selected_parts: Dictionary mapping block names to part data
            architecture: Architecture graph with dependencies
            intermediaries: Optional dict mapping target block names to intermediary block names
        
        Returns:
            List of nets, each with net_name and connections
        """
        nets = []
        
        # Build nets from power rails
        power_nets = defaultdict(list)
        
        # Track which parts are intermediaries
        intermediary_blocks = set()
        if intermediaries:
            intermediary_blocks = set(intermediaries.values())
        
        # Process each selected part
        for block_name, part_data in selected_parts.items():
            part_id = part_data.get("id", block_name)
            pinout = part_data.get("pinout", {})
            category = part_data.get("category", "")
            
            # Skip if this is an intermediary - we'll handle it separately
            if block_name in intermediary_blocks:
                continue
            
            # Power connections
            for pin_name, pin_desc in pinout.items():
                pin_upper = pin_name.upper()
                
                # Identify power pins
                if "VDD" in pin_upper or "VCC" in pin_upper or "VIN" in pin_upper:
                    # Check if this part has an intermediary for power
                    intermediary_block = None
                    if intermediaries:
                        intermediary_block = intermediaries.get(block_name)
                    
                    if intermediary_block and intermediary_block in selected_parts:
                        # Connect through intermediary
                        intermediary_part = selected_parts[intermediary_block]
                        intermediary_id = intermediary_part.get("id", intermediary_block)
                        intermediary_pinout = intermediary_part.get("pinout", {})
                        
                        # Find intermediary input pin (VIN)
                        for int_pin, int_desc in intermediary_pinout.items():
                            int_pin_upper = int_pin.upper()
                            if "VIN" in int_pin_upper or "INPUT" in int_pin_upper:
                                # Connect source to intermediary input
                                voltage = self._extract_voltage_from_part(part_data, pin_name)
                                if voltage:
                                    net_name = f"{voltage}V_INPUT".replace(".", "")
                                    power_nets[net_name].append([part_id, pin_name])
                                    power_nets[net_name].append([intermediary_id, int_pin])
                                
                                # Find intermediary output pin (VOUT)
                                for out_pin, out_desc in intermediary_pinout.items():
                                    out_pin_upper = out_pin.upper()
                                    if "VOUT" in out_pin_upper or "OUTPUT" in out_pin_upper or "VDD" in out_pin_upper:
                                        output_voltage = self._extract_voltage_from_part(intermediary_part, out_pin)
                                        if output_voltage:
                                            net_name = f"{output_voltage}V".replace(".", "")
                                            power_nets[net_name].append([intermediary_id, out_pin])
                                        break
                                break
                    else:
                        # Direct connection
                        if "3.3" in str(pin_desc) or "3V3" in pin_upper:
                            power_nets["3V3"].append([part_id, pin_name])
                        elif "5" in str(pin_desc) or "5V" in pin_upper or "VBUS" in pin_upper:
                            power_nets["5V"].append([part_id, pin_name])
                        else:
                            # Extract voltage from description
                            voltage = self._extract_voltage(pin_desc)
                            if voltage:
                                net_name = f"{voltage}V".replace(".", "")
                                power_nets[net_name].append([part_id, pin_name])
                
                # Ground connections
                if "GND" in pin_upper or "GROUND" in pin_upper:
                    power_nets["GND"].append([part_id, pin_name])
            
            # Signal connections (I2C, SPI, etc.)
            interfaces = part_data.get("interface_type", [])
            if isinstance(interfaces, str):
                interfaces = [interfaces]
            
            if "I2C" in interfaces:
                # Check if there's a level shifter for signals
                signal_intermediary = None
                if intermediaries:
                    signal_key = f"{block_name}_signal"
                    signal_intermediary = intermediaries.get(signal_key)
                
                for pin_name, pin_desc in pinout.items():
                    pin_upper = pin_name.upper()
                    if "SDA" in pin_upper or "I2C_SDA" in pin_upper or "DATA" in pin_upper:
                        if signal_intermediary and signal_intermediary in selected_parts:
                            # Connect through level shifter
                            level_shifter = selected_parts[signal_intermediary]
                            level_shifter_id = level_shifter.get("id", signal_intermediary)
                            # Add connections for level shifter (simplified)
                            power_nets["I2C_SDA"].append([part_id, pin_name])
                            power_nets["I2C_SDA"].append([level_shifter_id, "A1"])  # Simplified pin names
                        else:
                            if "I2C_SDA" not in power_nets:
                                power_nets["I2C_SDA"] = []
                            power_nets["I2C_SDA"].append([part_id, pin_name])
                    if "SCL" in pin_upper or "I2C_SCL" in pin_upper or "CLOCK" in pin_upper:
                        if signal_intermediary and signal_intermediary in selected_parts:
                            level_shifter = selected_parts[signal_intermediary]
                            level_shifter_id = level_shifter.get("id", signal_intermediary)
                            power_nets["I2C_SCL"].append([part_id, pin_name])
                            power_nets["I2C_SCL"].append([level_shifter_id, "A2"])  # Simplified pin names
                        else:
                            if "I2C_SCL" not in power_nets:
                                power_nets["I2C_SCL"] = []
                            power_nets["I2C_SCL"].append([part_id, pin_name])
        
        # Add intermediary power connections (VIN, VOUT, GND)
        for intermediary_block in intermediary_blocks:
            if intermediary_block in selected_parts:
                intermediary_part = selected_parts[intermediary_block]
                intermediary_id = intermediary_part.get("id", intermediary_block)
                pinout = intermediary_part.get("pinout", {})
                
                for pin_name, pin_desc in pinout.items():
                    pin_upper = pin_name.upper()
                    if "GND" in pin_upper or "GROUND" in pin_upper:
                        power_nets["GND"].append([intermediary_id, pin_name])
        
        # Convert to net list format with classification and current analysis
        for net_name, connections in power_nets.items():
            if len(connections) > 0:
                # Classify net type
                net_class = self._classify_net(net_name, connections, selected_parts)
                
                # Calculate current for power nets
                current_estimate = 0.0
                if net_class in ["power", "ground"]:
                    current_estimate = self._estimate_net_current(net_name, connections, selected_parts)
                
                # Recommend trace width based on current
                trace_width_mils = None
                if net_class == "power" and current_estimate > 0:
                    trace_width_mils = self._recommend_trace_width(current_estimate)
                
                nets.append({
                    "net_name": net_name,
                    "net_class": net_class,
                    "connections": connections,
                    "current_estimate_amps": round(current_estimate, 3) if current_estimate > 0 else None,
                    "recommended_trace_width_mils": trace_width_mils,
                    "impedance_ohms": self._get_impedance_requirement(net_name, net_class)
                })
        
        return nets
    
    def _classify_net(self, net_name: str, connections: List, selected_parts: Dict[str, Dict[str, Any]]) -> str:
        """Classify net as power, ground, signal, clock, or differential."""
        net_upper = net_name.upper()
        
        if net_upper == "GND" or "GROUND" in net_upper:
            return "ground"
        elif "VDD" in net_upper or "VCC" in net_upper or "VIN" in net_upper or "VOUT" in net_upper or "VBUS" in net_upper or any(c.isdigit() and "V" in net_upper for c in net_upper):
            return "power"
        elif "CLK" in net_upper or "CLOCK" in net_upper or "OSC" in net_upper:
            return "clock"
        elif "I2C" in net_upper or "SPI" in net_upper or "UART" in net_upper or "SDA" in net_upper or "SCL" in net_upper:
            # Check if differential pair
            if "D+" in net_upper or "D-" in net_upper or "TX+" in net_upper or "TX-" in net_upper or "RX+" in net_upper or "RX-" in net_upper:
                return "differential"
            return "signal"
        else:
            return "signal"
    
    def _estimate_net_current(self, net_name: str, connections: List, selected_parts: Dict[str, Dict[str, Any]]) -> float:
        """Estimate current flowing through a net."""
        total_current = 0.0
        
        # Extract voltage from net name
        voltage = None
        net_upper = net_name.upper()
        if "GND" not in net_upper:
            # Try to extract voltage
            import re
            match = re.search(r'(\d+\.?\d*)V', net_upper)
            if match:
                voltage = float(match.group(1))
        
        # Sum current from all connected parts
        for part_id, pin_name in connections:
            # Find part in selected_parts
            part_data = None
            for block_name, part in selected_parts.items():
                if part.get("id") == part_id:
                    part_data = part
                    break
            
            if part_data:
                # Get current requirement
                current_max = part_data.get("current_max", {})
                if isinstance(current_max, dict):
                    current = current_max.get("max") or current_max.get("typical", 0.0)
                else:
                    current = float(current_max) if current_max else 0.0
                
                # Only add if this is a power pin (not ground)
                if voltage and current > 0:
                    total_current += current
        
        return total_current
    
    def _recommend_trace_width(self, current_amps: float) -> Optional[int]:
        """
        Recommend trace width in mils based on current (IPC-2221 standards).
        
        For 1oz copper, 10°C temperature rise:
        - 0.5A: ~10 mils
        - 1A: ~20 mils
        - 2A: ~40 mils
        - 3A: ~60 mils
        """
        if current_amps <= 0:
            return None
        
        # Simple approximation: 20 mils per amp for 1oz copper
        width_mils = max(10, int(current_amps * 20))
        
        # Round to common values
        if width_mils < 20:
            return 10
        elif width_mils < 40:
            return 20
        elif width_mils < 60:
            return 40
        elif width_mils < 100:
            return 60
        else:
            return 100
    
    def _get_impedance_requirement(self, net_name: str, net_class: str) -> Optional[int]:
        """Get impedance requirement for net."""
        net_upper = net_name.upper()
        
        # High-speed signals need impedance control
        if net_class == "differential":
            return 100  # 100Ω differential
        elif net_class == "signal" and ("USB" in net_upper or "ETHERNET" in net_upper or "HDMI" in net_upper):
            return 90  # 90Ω differential for USB
        elif net_class == "signal" and ("CLK" in net_upper or "CLOCK" in net_upper):
            return 50  # 50Ω single-ended for clocks
        elif net_class == "power":
            return None  # Power nets don't have impedance requirements
        else:
            return None
    
    def _extract_voltage_from_part(self, part: Dict[str, Any], pin_name: str) -> Optional[float]:
        """Extract voltage from part's pin or part specification."""
        pinout = part.get("pinout", {})
        pin_desc = pinout.get(pin_name, "")
        
        # Try to extract from pin description
        voltage_str = self._extract_voltage(pin_desc)
        if voltage_str:
            try:
                return float(voltage_str)
            except ValueError:
                pass
        
        # Try part's output voltage
        output_voltage = part.get("output_voltage")
        if output_voltage:
            if isinstance(output_voltage, dict):
                return output_voltage.get("nominal") or output_voltage.get("value")
            return float(output_voltage)
        
        # Try supply voltage range
        supply_range = part.get("supply_voltage_range")
        if supply_range:
            return supply_range.get("nominal") or supply_range.get("value")
        
        return None
    
    def generate_bom(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        external_components: List[Dict[str, Any]],
        connections: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate BOM from selected parts and external components.
        
        Args:
            selected_parts: Dictionary mapping block names to part data
            external_components: List of external/passive components
        
        Returns:
            Dictionary with BOM entries and summary:
            {
                "items": List[Dict],  # BOM entries
                "summary": {
                    "total_cost": float,
                    "total_parts": int,
                    "total_qty": int
                }
            }
        """
        bom_items = []
        total_cost = 0.0
        
        # Designator counters
        designator_counters = {
            "U": 1,  # ICs
            "J": 1,  # Connectors
            "R": 1,  # Resistors
            "C": 1,  # Capacitors
            "D": 1,  # Diodes
            "Q": 1,  # Transistors
            "F": 1,  # Fuses
            "L": 1,  # Inductors
            "Y": 1,  # Crystals
        }
        
        # Add main parts
        for block_name, part_data in selected_parts.items():
            part_id = part_data.get("id", block_name)
            category = part_data.get("category", "")
            
            # Determine designator prefix
            if "mcu" in category or "module" in category:
                prefix = "U"
            elif "connector" in category:
                prefix = "J"
            elif "sensor" in category:
                prefix = "U"
            elif "regulator" in category:
                prefix = "U"
            elif "protection" in category:
                if "fuse" in category:
                    prefix = "F"
                else:
                    prefix = "D"
            elif "crystal" in category:
                prefix = "Y"
            elif "led" in category:
                prefix = "D"
            else:
                prefix = "U"
            
            designator = f"{prefix}{designator_counters[prefix]}"
            designator_counters[prefix] += 1
            
            # Extract cost - safe extraction to handle nested dicts
            cost_estimate = part_data.get("cost_estimate", {})
            unit_cost = safe_extract_cost(cost_estimate, default=0.0)
            extended_cost = unit_cost * 1  # qty = 1 for main parts
            total_cost += extended_cost
            
            # Extract additional fields
            tolerance = part_data.get("tolerance")
            if tolerance and isinstance(tolerance, dict):
                tolerance = tolerance.get("value") or tolerance.get("typical")
            
            # Determine mounting type from package
            mounting_type = "SMT"
            package = part_data.get("package", "").upper()
            if "TH" in package or "THROUGH" in package or "DIP" in package:
                mounting_type = "through_hole"
            
            # Extract IPC-7351 compliant footprint (use footprint field if available, otherwise derive from package)
            footprint = part_data.get("footprint", "")
            if not footprint and part_data.get("package"):
                # Derive IPC-7351 footprint name from package
                footprint = self._derive_footprint_name(part_data.get("package", ""))
            
            # Determine assembly side (default to top for SMT, bottom for through-hole)
            assembly_side = "top"
            if mounting_type == "through_hole":
                assembly_side = "both"  # Through-hole spans both sides
            elif "bottom" in category.lower() or "back" in category.lower():
                assembly_side = "bottom"
            
            # Extract MSL level (Moisture Sensitivity Level) for ICs
            msl_level = part_data.get("msl_level") or part_data.get("moisture_sensitivity_level")
            
            # Extract alternate part numbers
            alternate_part_numbers = part_data.get("alternate_part_numbers", [])
            if isinstance(alternate_part_numbers, str):
                alternate_part_numbers = [alternate_part_numbers]
            
            # Generate assembly notes based on MSL and special handling
            assembly_notes = self._generate_assembly_notes(part_data, msl_level)
            
            # Get EDA assets (footprint, symbol, 3D model) for KiCad
            eda_assets = {}
            try:
                eda_assets = self.eda_asset_agent.get_eda_assets(part_data, tool="kicad", asset_types=["footprint", "symbol"])
            except Exception:
                pass  # If EDA asset generation fails, continue without it
            
            bom_items.append({
                "designator": designator,
                "qty": 1,
                "manufacturer": part_data.get("manufacturer", ""),
                "mfr_part_number": part_data.get("mfr_part_number", ""),
                "description": part_data.get("description", ""),
                "category": category,
                "package": part_data.get("package", ""),
                "footprint": footprint,  # IPC-7351 compliant footprint name
                "value": self._extract_value(part_data),
                "tolerance": f"±{tolerance*100}%" if tolerance else "",
                "temperature_rating": self._extract_temperature_rating(part_data),
                "rohs_compliant": part_data.get("rohs_compliant", True),  # Default True
                "lifecycle_status": part_data.get("lifecycle_status", "active"),
                "availability_status": part_data.get("availability_status", "in_stock"),
                "lead_time_days": part_data.get("lead_time_days"),
                "distributor_part_numbers": part_data.get("distributor_part_numbers", {}),
                "mounting_type": mounting_type,
                "assembly_side": assembly_side,  # "top", "bottom", or "both"
                "msl_level": msl_level,  # Moisture Sensitivity Level (1-6)
                "datasheet_url": part_data.get("datasheet_url", ""),
                "alternate_part_numbers": alternate_part_numbers,  # Approved substitutes
                "assembly_notes": assembly_notes,  # Special handling instructions
                "test_point": False,  # Flag for test points
                "fiducial": False,  # Flag for fiducial marks
                "unit_cost": round(unit_cost, 4),
                "extended_cost": round(extended_cost, 4),
                "eda_assets": eda_assets,  # EDA assets (footprint, symbol, 3D model)
                "notes": ""
            })
        
        # Add external components (group identical ones)
        external_groups = defaultdict(list)
        for ext_comp in external_components:
            # Create a key for grouping
            comp_type = ext_comp.get("type", "")
            value = ext_comp.get("value", "")
            package = ext_comp.get("package", "")
            key = f"{comp_type}_{value}_{package}"
            external_groups[key].append(ext_comp)
        
        # Add grouped external components to BOM
        for key, group in external_groups.items():
            first = group[0]
            comp_type = first.get("type", "")
            qty = len(group)
            
            # Determine designator prefix
            if comp_type == "capacitor":
                prefix = "C"
            elif comp_type == "resistor":
                prefix = "R"
            elif comp_type == "tvs_diode":
                prefix = "D"
            elif comp_type == "inductor":
                prefix = "L"
            else:
                prefix = "R"  # Default
            
            # Create designator range if multiple
            if qty > 1:
                start_num = designator_counters[prefix]
                end_num = start_num + qty - 1
                designator = f"{prefix}{start_num}-{prefix}{end_num}"
            else:
                designator = f"{prefix}{designator_counters[prefix]}"
            
            designator_counters[prefix] += qty
            
            # Try to find matching part in database
            mfr_part_number = first.get("mfr_part_number", "")
            manufacturer = first.get("manufacturer", "")
            description = f"{value} {comp_type}"
            
            if comp_type == "capacitor":
                voltage_rating = first.get("voltage_rating", "")
                description = f"{value} {voltage_rating}V {package} capacitor" if voltage_rating else f"{value} {package} capacitor"
            elif comp_type == "resistor":
                description = f"{value}Ω {package} resistor"
            
            # Extract cost for external components - safe extraction to handle nested dicts
            cost_estimate = first.get("cost_estimate", {})
            unit_cost = safe_extract_cost(cost_estimate, default=0.0)
            qty = safe_extract_quantity(qty, default=1)
            extended_cost = unit_cost * qty
            total_cost += extended_cost
            
            # Extract tolerance
            tolerance = first.get("tolerance")
            if tolerance and isinstance(tolerance, dict):
                tolerance = tolerance.get("value") or tolerance.get("typical")
            
            # Extract footprint for external components
            footprint = first.get("footprint", "")
            if not footprint and package:
                footprint = self._derive_footprint_name(package)
            
            bom_items.append({
                "designator": designator,
                "qty": qty,
                "manufacturer": manufacturer,
                "mfr_part_number": mfr_part_number,
                "description": description,
                "category": comp_type,
                "package": package,
                "footprint": footprint,  # IPC-7351 compliant footprint name
                "value": value,
                "tolerance": f"±{tolerance*100}%" if tolerance else "",
                "temperature_rating": first.get("temperature_coefficient", ""),
                "rohs_compliant": first.get("rohs_compliant", True),
                "lifecycle_status": first.get("lifecycle_status", "active"),
                "availability_status": first.get("availability_status", "in_stock"),
                "lead_time_days": first.get("lead_time_days"),
                "distributor_part_numbers": first.get("distributor_part_numbers", {}),
                "mounting_type": "SMT" if package else "unknown",
                "assembly_side": "top",  # Passives typically on top
                "msl_level": None,  # Passives don't have MSL
                "datasheet_url": first.get("datasheet_url", ""),
                "alternate_part_numbers": first.get("alternate_part_numbers", []),
                "assembly_notes": "",
                "test_point": False,
                "fiducial": False,
                "unit_cost": round(unit_cost, 4),
                "extended_cost": round(extended_cost, 4),
                "notes": first.get("purpose", "")
            })
        
        # Add test points and fiducials
        if connections:
            test_points = self.testpoint_agent.generate_test_points(connections, selected_parts)
            bom_items = self.testpoint_agent.add_test_points_to_bom(bom_items, test_points)
            total_cost += sum(tp.get("unit_cost", 0.01) for tp in test_points)
        
        # Always add fiducials (required for automated assembly)
        fiducials = self.testpoint_agent.generate_fiducials()
        bom_items = self.testpoint_agent.add_fiducials_to_bom(bom_items, fiducials)
        total_cost += sum(fid.get("unit_cost", 0.01) for fid in fiducials)
        
        # Calculate totals
        total_qty = sum(item["qty"] for item in bom_items)
        
        # Add BOM metadata
        from datetime import datetime
        bom_metadata = {
            "revision": "1.0",
            "revision_date": datetime.now().strftime("%Y-%m-%d"),
            "generated_by": "PCB Design Agent System",
            "standard": "IPC-2581 compatible"
        }
        
        return {
            "items": bom_items,
            "summary": {
                "total_cost": round(total_cost, 2),
                "total_parts": len(bom_items),
                "total_qty": total_qty
            },
            "metadata": bom_metadata
        }
    
    def _extract_voltage(self, text: Any) -> Optional[str]:
        """Extract voltage value from text."""
        if isinstance(text, (int, float)):
            return str(text)
        if isinstance(text, str):
            # Look for voltage patterns
            import re
            match = re.search(r'(\d+\.?\d*)\s*V', text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_value(self, part_data: Dict[str, Any]) -> str:
        """Extract value string from part data."""
        # Check various value fields
        if "value" in part_data:
            return str(part_data["value"])
        if "output_voltage" in part_data:
            ov = part_data["output_voltage"]
            if isinstance(ov, dict):
                return f"{ov.get('value', '')}V"
            return f"{ov}V"
        if "resistance" in part_data:
            r = part_data["resistance"]
            if isinstance(r, dict):
                return f"{r.get('value', '')}Ω"
            return f"{r}Ω"
        if "capacitance" in part_data:
            c = part_data["capacitance"]
            if isinstance(c, dict):
                return f"{c.get('value', '')}uF"
            return f"{c}uF"
        return ""
    
    def _extract_temperature_rating(self, part_data: Dict[str, Any]) -> str:
        """Extract temperature rating information."""
        temp_range = part_data.get("operating_temp_range", {})
        if isinstance(temp_range, dict):
            min_temp = temp_range.get("min")
            max_temp = temp_range.get("max")
            if min_temp is not None and max_temp is not None:
                return f"{min_temp}°C to {max_temp}°C"
        
        # Check for temperature coefficient (for passives)
        temp_coeff = part_data.get("temperature_coefficient")
        if temp_coeff:
            return str(temp_coeff)
        
        return ""
    
    def _derive_footprint_name(self, package: str) -> str:
        """
        Derive IPC-7351 compliant footprint name from package string.
        This is a simplified mapping - in production, use a comprehensive footprint library.
        """
        package_upper = package.upper()
        
        # Common IPC-7351 footprint patterns
        if "0402" in package_upper:
            return "RESC1005X40N" if "RES" in package_upper else "CAPC1005X40N"
        elif "0603" in package_upper:
            return "RESC1608X55N" if "RES" in package_upper else "CAPC1608X55N"
        elif "0805" in package_upper:
            return "RESC2012X55N" if "RES" in package_upper else "CAPC2012X55N"
        elif "1206" in package_upper:
            return "RESC3216X90N" if "RES" in package_upper else "CAPC3216X90N"
        elif "SOIC" in package_upper or "SO" in package_upper:
            # Extract pin count
            import re
            pin_match = re.search(r'(\d+)', package_upper)
            pins = int(pin_match.group(1)) if pin_match else 8
            return f"SOIC{pins}P127_600X175X120-8N"
        elif "QFN" in package_upper:
            pin_match = re.search(r'(\d+)', package_upper)
            pins = int(pin_match.group(1)) if pin_match else 48
            return f"QFN{pins}P{int(pins/4)}X{int(pins/4)}X{int(pins/4)}-{pins}N"
        elif "QFP" in package_upper:
            pin_match = re.search(r'(\d+)', package_upper)
            pins = int(pin_match.group(1)) if pin_match else 64
            return f"QFP{pins}P{int(pins/4)}X{int(pins/4)}X{int(pins/4)}-{pins}N"
        elif "DIP" in package_upper:
            pin_match = re.search(r'(\d+)', package_upper)
            pins = int(pin_match.group(1)) if pin_match else 8
            return f"DIP{pins}P254_600X{int(pins/2)*254}N"
        else:
            # Return generic footprint name based on package
            return f"FOOTPRINT_{package_upper.replace(' ', '_')}"
    
    def _generate_assembly_notes(self, part_data: Dict[str, Any], msl_level: Optional[str]) -> str:
        """
        Generate assembly notes based on MSL level and special handling requirements.
        """
        notes = []
        
        # MSL-based baking requirements
        if msl_level:
            msl_num = int(msl_level) if str(msl_level).isdigit() else None
            if msl_num:
                if msl_num >= 3:
                    notes.append(f"MSL {msl_num}: Requires baking before assembly (see IPC/JEDEC J-STD-033)")
                if msl_num >= 5:
                    notes.append("Critical: Must be assembled within 168 hours after baking")
        
        # ESD sensitivity
        if part_data.get("esd_sensitivity"):
            esd_level = part_data.get("esd_sensitivity")
            notes.append(f"ESD sensitive: Handle with ESD precautions ({esd_level})")
        
        # Special reflow profile
        if part_data.get("reflow_profile"):
            notes.append(f"Special reflow profile required: {part_data.get('reflow_profile')}")
        
        # Orientation requirements
        if part_data.get("orientation_required"):
            notes.append("Orientation critical: Verify pin 1 marker before placement")
        
        # Polarity requirements
        if part_data.get("polarity_required"):
            notes.append("Polarity critical: Verify polarity marking before placement")
        
        return "; ".join(notes) if notes else ""

