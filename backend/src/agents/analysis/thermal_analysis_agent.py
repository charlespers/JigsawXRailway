"""
Thermal Analysis Agent
Provides detailed thermal analysis including junction temperature calculations and heat sink recommendations
"""

from typing import List, Dict, Any, Optional


class ThermalAnalysisAgent:
    """Provides detailed thermal analysis for PCB designs."""
    
    def analyze_thermal(
        self,
        bom_items: List[Dict[str, Any]],
        ambient_temp: float = 25.0,
        pcb_area_cm2: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive thermal analysis.
        
        Args:
            bom_items: List of BOM items with part data
            ambient_temp: Ambient temperature in Celsius (default 25°C)
            pcb_area_cm2: PCB area in cm² (optional, for board-level analysis)
        
        Returns:
            Dictionary with thermal analysis:
            {
                "component_thermal": List[Dict],
                "thermal_hotspots": List[Dict],
                "heat_sink_recommendations": List[Dict],
                "board_level_analysis": Dict,
                "recommendations": List[str]
            }
        """
        component_thermal = []
        thermal_hotspots = []
        heat_sink_recommendations = []
        total_power_dissipation = 0.0
        
        from utils.cost_utils import safe_extract_quantity
        from agents.design.design_analyzer import safe_float_extract
        
        for item in bom_items:
            part = item.get("part_data", {})
            quantity = safe_extract_quantity(item.get("quantity", 1), default=1)
            part_id = part.get("id")
            category = part.get("category", "")
            
            # Calculate power dissipation - use safe extraction
            power_dissipation = self._calculate_power_dissipation(part, item)
            power_dissipation_float = safe_float_extract(
                power_dissipation,
                context=f"power_dissipation for {part.get('id', 'unknown')}"
            )
            total_power_dissipation += power_dissipation_float * quantity
            
            if power_dissipation_float > 0:
                # Get thermal resistance - use safe extraction
                thermal_resistance = self._get_thermal_resistance(part)
                thermal_resistance_float = safe_float_extract(
                    thermal_resistance,
                    context=f"thermal_resistance for {part.get('id', 'unknown')}"
                )
                
                # Calculate junction temperature
                junction_temp = None
                if thermal_resistance_float and thermal_resistance_float > 0:
                    junction_temp = ambient_temp + (power_dissipation_float * thermal_resistance_float)
                
                # Get maximum operating temperature
                max_temp = self._get_max_temperature(part)
                
                # Check if thermal limits are exceeded
                thermal_ok = True
                thermal_warning = None
                if junction_temp and max_temp:
                    if junction_temp > max_temp:
                        thermal_ok = False
                        thermal_warning = f"Junction temperature ({junction_temp:.1f}°C) exceeds maximum ({max_temp}°C)"
                        thermal_hotspots.append({
                            "part_id": part_id,
                            "name": part.get("name"),
                            "junction_temp_c": round(junction_temp, 1),
                            "max_temp_c": max_temp,
                            "power_dissipation_w": round(power_dissipation, 3),
                            "thermal_resistance_c_per_w": thermal_resistance,
                            "severity": "critical"
                        })
                    elif junction_temp > max_temp * 0.9:
                        thermal_warning = f"Junction temperature ({junction_temp:.1f}°C) approaching maximum ({max_temp}°C)"
                        thermal_hotspots.append({
                            "part_id": part_id,
                            "name": part.get("name"),
                            "junction_temp_c": round(junction_temp, 1),
                            "max_temp_c": max_temp,
                            "power_dissipation_w": round(power_dissipation, 3),
                            "thermal_resistance_c_per_w": thermal_resistance,
                            "severity": "warning"
                        })
                
                # Check for LDOs with high power dissipation
                if "ldo" in category.lower() and power_dissipation > 1.0:
                    heat_sink_recommendations.append({
                        "part_id": part_id,
                        "name": part.get("name"),
                        "power_dissipation_w": round(power_dissipation, 3),
                        "recommendation": "Consider heatsink or switching regulator",
                        "reason": f"LDO power dissipation ({power_dissipation:.2f}W) exceeds 1W threshold"
                    })
                
                # Check for switching regulators with high power
                if "switching" in category.lower() and power_dissipation > 2.0:
                    heat_sink_recommendations.append({
                        "part_id": part_id,
                        "name": part.get("name"),
                        "power_dissipation_w": round(power_dissipation, 3),
                        "recommendation": "Consider thermal vias and copper pour",
                        "reason": f"Switching regulator power dissipation ({power_dissipation:.2f}W) is high"
                    })
                
                component_thermal.append({
                    "part_id": part_id,
                    "name": part.get("name"),
                    "category": category,
                    "power_dissipation_w": round(power_dissipation, 3),
                    "thermal_resistance_c_per_w": thermal_resistance,
                    "junction_temp_c": round(junction_temp, 1) if junction_temp else None,
                    "max_temp_c": max_temp,
                    "thermal_margin_c": round(max_temp - junction_temp, 1) if (junction_temp and max_temp) else None,
                    "thermal_ok": thermal_ok,
                    "warning": thermal_warning,
                    "quantity": quantity
                })
        
        # Board-level analysis
        board_level_analysis = {}
        if pcb_area_cm2:
            power_density = total_power_dissipation / pcb_area_cm2
            board_level_analysis = {
                "total_power_dissipation_w": round(total_power_dissipation, 3),
                "pcb_area_cm2": pcb_area_cm2,
                "power_density_w_per_cm2": round(power_density, 3),
                "recommendation": "Consider thermal vias and copper pours" if power_density > 0.1 else "Power density is acceptable"
            }
        
        # Generate recommendations
        recommendations = []
        if thermal_hotspots:
            critical_count = sum(1 for h in thermal_hotspots if h.get("severity") == "critical")
            if critical_count > 0:
                recommendations.append(f"{critical_count} component(s) exceed thermal limits - immediate action required")
            
            warning_count = sum(1 for h in thermal_hotspots if h.get("severity") == "warning")
            if warning_count > 0:
                recommendations.append(f"{warning_count} component(s) approaching thermal limits - review thermal design")
        
        if heat_sink_recommendations:
            recommendations.append(f"Consider heat sinks or thermal management for {len(heat_sink_recommendations)} component(s)")
        
        if total_power_dissipation > 5.0:
            recommendations.append(f"Total power dissipation ({total_power_dissipation:.2f}W) is high - ensure adequate cooling")
        
        if not recommendations:
            recommendations.append("Thermal analysis passed - no critical issues detected")
        
        return {
            "ambient_temp_c": ambient_temp,
            "component_thermal": component_thermal,
            "thermal_hotspots": thermal_hotspots,
            "heat_sink_recommendations": heat_sink_recommendations,
            "board_level_analysis": board_level_analysis,
            "total_power_dissipation_w": round(total_power_dissipation, 3),
            "recommendations": recommendations
        }
    
    def _calculate_power_dissipation(self, part: Dict[str, Any], item: Dict[str, Any]) -> float:
        """Calculate power dissipation for a component."""
        category = part.get("category", "")
        
        # For regulators, calculate (Vin - Vout) * Iout
        if "regulator" in category.lower() or "ldo" in category.lower():
            supply_range = part.get("supply_voltage_range", {})
            if isinstance(supply_range, dict):
                vin = supply_range.get("nominal") or supply_range.get("max", 0)
                if isinstance(vin, dict):
                    vin = vin.get("value") or vin.get("nominal") or 0
                vin = float(vin) if vin else 0.0
            else:
                vin = float(supply_range) if supply_range else 0.0
            
            output_voltage = part.get("output_voltage", {})
            if isinstance(output_voltage, dict):
                vout = output_voltage.get("nominal") or output_voltage.get("value", 0)
                if isinstance(vout, dict):
                    vout = vout.get("value") or vout.get("nominal") or 0
                vout = float(vout) if vout else 0.0
            else:
                vout = float(output_voltage) if output_voltage else 0.0
            
            current_max = part.get("current_max", {})
            if isinstance(current_max, dict):
                iout = current_max.get("typical") or current_max.get("max", 0)
                if isinstance(iout, dict):
                    iout = iout.get("value") or iout.get("max") or 0
                iout = float(iout) if iout else 0.0
            else:
                iout = float(current_max) if current_max else 0.0
            
            if vin > 0 and vout > 0 and iout > 0:
                return (vin - vout) * iout
        
        # Import safe_float_extract
        from agents.design.design_analyzer import safe_float_extract
        
        # For other components, use supply voltage * current - use safe extraction
        supply_range = part.get("supply_voltage_range", {})
        voltage = safe_float_extract(
            supply_range.get("nominal") if isinstance(supply_range, dict) else supply_range,
            context=f"voltage for {part.get('id', 'unknown')}"
        )
        
        current_max = part.get("current_max", {})
        current = safe_float_extract(
            current_max.get("typical") if isinstance(current_max, dict) else current_max,
            context=f"current for {part.get('id', 'unknown')}"
        )
        
        if voltage > 0 and current > 0:
            return voltage * current
        
        return 0.0
    
    def _get_thermal_resistance(self, part: Dict[str, Any]) -> Optional[float]:
        """Get thermal resistance (theta_ja) for a component."""
        thermal_resistance = part.get("thermal_resistance", {})
        if isinstance(thermal_resistance, dict):
            theta_ja = thermal_resistance.get("theta_ja") or thermal_resistance.get("junction_to_ambient")
            if isinstance(theta_ja, dict):
                theta_ja = theta_ja.get("value") or theta_ja.get("typical")
            return float(theta_ja) if theta_ja else None
        elif isinstance(thermal_resistance, (int, float)):
            return float(thermal_resistance)
        
        # Default thermal resistance based on package
        package = part.get("package", "").upper()
        default_theta_ja = {
            "SOT-23": 250.0,
            "SOT-223": 65.0,
            "TO-220": 50.0,
            "QFN": 35.0,
            "LQFP": 45.0,
            "SOIC": 70.0
        }
        
        for pkg, theta in default_theta_ja.items():
            if pkg in package:
                return theta
        
        return 50.0  # Default
    
    def _get_max_temperature(self, part: Dict[str, Any]) -> Optional[float]:
        """Get maximum operating temperature for a component."""
        max_temp = part.get("max_junction_temp") or part.get("max_operating_temp")
        if isinstance(max_temp, dict):
            max_temp = max_temp.get("max") or max_temp.get("value")
        
        if max_temp:
            return float(max_temp)
        
        # Default based on operating temp range
        operating_temp = part.get("operating_temp_range", {})
        if isinstance(operating_temp, dict):
            max_op_temp = operating_temp.get("max")
            if max_op_temp:
                return float(max_op_temp)
        
        return 85.0  # Default

