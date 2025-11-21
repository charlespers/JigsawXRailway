"""
Signal Integrity Agent
Provides signal integrity analysis, trace impedance calculations, and EMI/EMC recommendations
"""

from typing import List, Dict, Any, Optional


class SignalIntegrityAgent:
    """Provides signal integrity and EMI/EMC analysis."""
    
    def analyze_signal_integrity(
        self,
        bom_items: List[Dict[str, Any]],
        connections: Optional[List[Dict[str, Any]]] = None,
        pcb_thickness_mm: float = 1.6,
        trace_width_mils: float = 5.0
    ) -> Dict[str, Any]:
        """
        Perform signal integrity analysis.
        
        Args:
            bom_items: List of BOM items with part data
            connections: Optional list of connections
            pcb_thickness_mm: PCB thickness in mm (default 1.6mm)
            trace_width_mils: Default trace width in mils (default 5 mils)
        
        Returns:
            Dictionary with signal integrity analysis:
            {
                "high_speed_signals": List[Dict],
                "impedance_recommendations": List[Dict],
                "emi_emc_recommendations": List[str],
                "routing_recommendations": List[str],
                "decoupling_analysis": Dict
            }
        """
        high_speed_signals = []
        impedance_recommendations = []
        emi_emc_recommendations = []
        routing_recommendations = []
        
        # Identify high-speed interfaces
        high_speed_interfaces = ["USB", "Ethernet", "SPI", "I2C", "UART", "CAN", "HDMI", "MIPI"]
        
        for item in bom_items:
            part = item.get("part_data", {})
            interfaces = part.get("interface_type", [])
            
            for interface in interfaces:
                if any(hs in interface.upper() for hs in high_speed_interfaces):
                    # Calculate characteristic impedance
                    impedance = self._calculate_impedance(trace_width_mils, pcb_thickness_mm)
                    
                    # Determine required impedance
                    required_impedance = self._get_required_impedance(interface)
                    
                    if required_impedance:
                        impedance_ok = abs(impedance - required_impedance) < 5  # 5 ohm tolerance
                        
                        high_speed_signals.append({
                            "part_id": part.get("id"),
                            "name": part.get("name"),
                            "interface": interface,
                            "calculated_impedance_ohms": round(impedance, 1),
                            "required_impedance_ohms": required_impedance,
                            "impedance_ok": impedance_ok,
                            "recommendation": self._get_impedance_recommendation(interface, impedance, required_impedance)
                        })
                        
                        if not impedance_ok:
                            impedance_recommendations.append({
                                "interface": interface,
                                "part": part.get("name"),
                                "current_impedance": round(impedance, 1),
                                "required_impedance": required_impedance,
                                "recommendation": f"Adjust trace width or PCB stackup to achieve {required_impedance}Ω impedance"
                            })
        
        # EMI/EMC recommendations
        has_wifi = any("wifi" in str(part.get("part_data", {}).get("interface_type", [])).lower() 
                      for part in bom_items)
        has_bluetooth = any("bluetooth" in str(part.get("part_data", {}).get("interface_type", [])).lower() 
                           for part in bom_items)
        
        if has_wifi or has_bluetooth:
            emi_emc_recommendations.append("RF components detected - ensure proper antenna placement and RF ground plane")
            emi_emc_recommendations.append("Add ferrite beads on power supply lines to RF components")
            emi_emc_recommendations.append("Keep digital and analog grounds separate, connect at single point")
        
        # Check for high-speed digital signals
        if high_speed_signals:
            routing_recommendations.append("Use controlled impedance routing for high-speed signals")
            routing_recommendations.append("Keep high-speed traces away from noisy components (switching regulators, crystals)")
            routing_recommendations.append("Maintain consistent trace width and spacing for differential pairs")
            routing_recommendations.append("Add ground vias near high-speed signal vias to provide return path")
        
        # Decoupling analysis
        decoupling_analysis = self._analyze_decoupling(bom_items)
        
        # General recommendations
        if not high_speed_signals:
            routing_recommendations.append("No high-speed signals detected - standard routing practices apply")
        
        return {
            "high_speed_signals": high_speed_signals,
            "impedance_recommendations": impedance_recommendations,
            "emi_emc_recommendations": emi_emc_recommendations,
            "routing_recommendations": routing_recommendations,
            "decoupling_analysis": decoupling_analysis,
            "pcb_parameters": {
                "thickness_mm": pcb_thickness_mm,
                "trace_width_mils": trace_width_mils
            }
        }
    
    def _calculate_impedance(self, trace_width_mils: float, pcb_thickness_mm: float) -> float:
        """Calculate characteristic impedance for a microstrip trace."""
        # Simplified microstrip impedance calculation
        # Z0 ≈ (87 / sqrt(er + 1.41)) * ln(5.98 * h / (0.8 * w + t))
        # Where: er = dielectric constant (4.5 for FR4), h = substrate thickness, w = trace width, t = trace thickness
        
        er = 4.5  # FR4 dielectric constant
        h = pcb_thickness_mm * 39.37  # Convert mm to mils
        w = trace_width_mils
        t = 1.4  # Typical trace thickness in mils (1 oz copper)
        
        # Simplified formula
        z0 = (87.0 / ((er + 1.41) ** 0.5)) * (5.98 * h / (0.8 * w + t))
        
        return z0
    
    def _get_required_impedance(self, interface: str) -> Optional[float]:
        """Get required characteristic impedance for an interface."""
        interface_upper = interface.upper()
        
        impedance_map = {
            "USB": 90.0,  # USB 2.0 differential impedance
            "USB2.0": 90.0,
            "USB3.0": 90.0,
            "ETHERNET": 100.0,  # Ethernet differential impedance
            "SPI": 50.0,  # Single-ended
            "I2C": None,  # I2C doesn't require controlled impedance for low speeds
            "UART": 50.0,  # Single-ended
            "CAN": 120.0,  # CAN bus differential impedance
            "HDMI": 100.0,  # HDMI differential impedance
            "MIPI": 100.0  # MIPI differential impedance
        }
        
        for key, value in impedance_map.items():
            if key in interface_upper:
                return value
        
        return None
    
    def _get_impedance_recommendation(self, interface: str, calculated: float, required: float) -> str:
        """Get recommendation for impedance matching."""
        diff = abs(calculated - required)
        
        if diff < 5:
            return "Impedance is within acceptable range"
        elif calculated < required:
            return f"Impedance too low ({calculated:.1f}Ω) - increase trace width or use thinner PCB"
        else:
            return f"Impedance too high ({calculated:.1f}Ω) - decrease trace width or use thicker PCB"
    
    def _analyze_decoupling(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze decoupling capacitor placement."""
        ic_count = 0
        decoupling_cap_count = 0
        
        for item in bom_items:
            part = item.get("part_data", {})
            category = part.get("category", "")
            
            if "mcu" in category.lower() or "ic" in category.lower():
                ic_count += 1
            
            if "capacitor" in category.lower():
                # Check if it's a decoupling capacitor (typically 0.1uF or 10uF)
                capacitance = part.get("capacitance", {})
                if isinstance(capacitance, dict):
                    value = capacitance.get("value", 0)
                else:
                    value = capacitance or 0
                
                if value and (0.05 <= float(value) <= 0.2 or 4.7 <= float(value) <= 22):
                    decoupling_cap_count += item.get("quantity", 1)
        
        recommendation = "Adequate decoupling" if decoupling_cap_count >= ic_count * 2 else "Add more decoupling capacitors"
        
        return {
            "ic_count": ic_count,
            "decoupling_cap_count": decoupling_cap_count,
            "ratio": round(decoupling_cap_count / ic_count, 2) if ic_count > 0 else 0,
            "recommendation": recommendation
        }

