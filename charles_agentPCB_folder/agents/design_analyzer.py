"""
Design Analyzer Agent
Performs power consumption analysis, thermal analysis, and design rule checks
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict


class DesignAnalyzer:
    """Agent that analyzes design for power, thermal, and design rule compliance."""
    
    def __init__(self):
        pass
    
    def analyze_design(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        connections: List[Dict[str, Any]],
        compatibility_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive design analysis.
        
        Args:
            selected_parts: Dictionary mapping block names to part data
            connections: List of net connections
            compatibility_results: Compatibility check results
        
        Returns:
            Dictionary with analysis results:
            {
                "power_analysis": {...},
                "thermal_analysis": {...},
                "design_rule_checks": {...},
                "recommendations": [...]
            }
        """
        power_analysis = self._analyze_power(selected_parts, connections)
        thermal_analysis = self._analyze_thermal(selected_parts, power_analysis)
        drc_results = self._perform_drc(selected_parts, compatibility_results, power_analysis)
        recommendations = self._generate_recommendations(
            power_analysis, thermal_analysis, drc_results, selected_parts
        )
        
        return {
            "power_analysis": power_analysis,
            "thermal_analysis": thermal_analysis,
            "design_rule_checks": drc_results,
            "recommendations": recommendations
        }
    
    def _analyze_power(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        connections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze power consumption per rail and total."""
        power_rails = defaultdict(float)  # voltage -> current
        component_power = {}  # component_id -> power consumption
        
        # Analyze each component
        for block_name, part_data in selected_parts.items():
            part_id = part_data.get("id", block_name)
            
            # Get supply voltage
            supply_range = part_data.get("supply_voltage_range", {})
            if isinstance(supply_range, dict):
                voltage = supply_range.get("nominal") or supply_range.get("value")
                # Ensure voltage is a float, not a dict
                if isinstance(voltage, dict):
                    voltage = voltage.get("value") or voltage.get("nominal") or 0.0
                voltage = float(voltage) if voltage else 0.0
            else:
                voltage = float(supply_range) if supply_range else 0.0
            
            # Get current consumption
            current_max = part_data.get("current_max", {})
            if isinstance(current_max, dict):
                current = current_max.get("max") or current_max.get("typical", 0.0)
                # Ensure current is a float, not a dict
                if isinstance(current, dict):
                    current = current.get("value") or current.get("max") or 0.0
                current = float(current) if current else 0.0
            else:
                current = float(current_max) if current_max else 0.0
            
            if voltage and current > 0:
                power = voltage * current
                power_rails[voltage] += current
                component_power[part_id] = {
                    "voltage": voltage,
                    "current": current,
                    "power": power
                }
        
        # Calculate total power
        total_power = sum(rail_current * voltage for voltage, rail_current in power_rails.items())
        
        # Find power-hungry components
        power_hungry = []
        for part_id, power_info in component_power.items():
            if power_info["power"] > 0.5:  # > 500mW
                power_hungry.append({
                    "part_id": part_id,
                    "power_watts": round(power_info["power"], 3),
                    "voltage": power_info["voltage"],
                    "current_amps": power_info["current"]
                })
        
        # Sort by power consumption
        power_hungry.sort(key=lambda x: x["power_watts"], reverse=True)
        
        return {
            "power_rails": {
                f"{voltage}V": {
                    "voltage": voltage,
                    "current_amps": round(current, 3),
                    "power_watts": round(voltage * current, 3)
                }
                for voltage, current in power_rails.items()
            },
            "total_power_watts": round(total_power, 3),
            "component_power": component_power,
            "power_hungry_components": power_hungry
        }
    
    def _analyze_thermal(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        power_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze thermal characteristics and identify hotspots."""
        thermal_issues = []
        component_thermal = {}
        
        component_power = power_analysis.get("component_power", {})
        
        for block_name, part_data in selected_parts.items():
            part_id = part_data.get("id", block_name)
            category = part_data.get("category", "")
            
            # Get power dissipation
            power_info = component_power.get(part_id, {})
            power_dissipation = power_info.get("power", 0.0)
            
            if power_dissipation > 0:
                # Check thermal limits
                thermal_resistance = part_data.get("thermal_resistance", {})
                if isinstance(thermal_resistance, dict):
                    theta_ja = thermal_resistance.get("theta_ja") or thermal_resistance.get("junction_to_ambient")
                else:
                    theta_ja = thermal_resistance
                
                max_temp = part_data.get("max_junction_temp") or part_data.get("max_operating_temp")
                if isinstance(max_temp, dict):
                    max_temp_value = max_temp.get("max") or max_temp.get("value")
                else:
                    max_temp_value = max_temp
                
                # Calculate junction temperature (assuming 25°C ambient)
                ambient_temp = 25.0
                if theta_ja and power_dissipation > 0:
                    junction_temp = ambient_temp + (power_dissipation * theta_ja)
                    
                    thermal_ok = True
                    if max_temp_value and junction_temp > max_temp_value:
                        thermal_ok = False
                        thermal_issues.append({
                            "part_id": part_id,
                            "junction_temp_c": round(junction_temp, 1),
                            "max_temp_c": max_temp_value,
                            "power_dissipation_w": round(power_dissipation, 3),
                            "issue": "Junction temperature exceeds maximum"
                        })
                    
                    component_thermal[part_id] = {
                        "power_dissipation_w": round(power_dissipation, 3),
                        "junction_temp_c": round(junction_temp, 1),
                        "max_temp_c": max_temp_value,
                        "thermal_ok": thermal_ok
                    }
                
                # Check for LDOs with high power dissipation
                if "ldo" in category.lower() and power_dissipation > 1.0:
                    thermal_issues.append({
                        "part_id": part_id,
                        "power_dissipation_w": round(power_dissipation, 3),
                        "issue": "LDO power dissipation > 1W - consider heatsink or switching regulator"
                    })
        
        return {
            "component_thermal": component_thermal,
            "thermal_issues": thermal_issues,
            "total_thermal_issues": len(thermal_issues)
        }
    
    def _perform_drc(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        compatibility_results: Dict[str, Any],
        power_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform design rule checks."""
        drc_errors = []
        drc_warnings = []
        
        # Check compatibility
        for block_name, compat_result in compatibility_results.items():
            if isinstance(compat_result, dict):
                # Check power compatibility
                power_compat = compat_result.get("power", {})
                if not power_compat.get("compatible", True):
                    drc_errors.append({
                        "type": "voltage_compatibility",
                        "block": block_name,
                        "message": power_compat.get("reasoning", "Voltage incompatibility")
                    })
                
                # Check interface compatibility
                interface_compat = compat_result.get("interface", {})
                if not interface_compat.get("compatible", True):
                    warnings = interface_compat.get("warnings", [])
                    if warnings:
                        drc_warnings.append({
                            "type": "interface_compatibility",
                            "block": block_name,
                            "message": "; ".join(warnings)
                        })
        
        # Check power supply adequacy
        power_rails = power_analysis.get("power_rails", {})
        for rail_name, rail_info in power_rails.items():
            # Find power supply for this rail
            for block_name, part_data in selected_parts.items():
                category = part_data.get("category", "")
                if "regulator" in category:
                    output_voltage = part_data.get("output_voltage")
                    if isinstance(output_voltage, dict):
                        reg_voltage = output_voltage.get("nominal") or output_voltage.get("value")
                    else:
                        reg_voltage = output_voltage
                    
                    if reg_voltage and abs(reg_voltage - rail_info["voltage"]) < 0.1:
                        # Check current capacity
                        reg_current = part_data.get("current_max", {})
                        if isinstance(reg_current, dict):
                            reg_current_max = reg_current.get("max") or reg_current.get("typical", 0)
                        else:
                            reg_current_max = float(reg_current) if reg_current else 0
                        
                        if reg_current_max > 0 and rail_info["current_amps"] > reg_current_max * 0.9:
                            drc_warnings.append({
                                "type": "power_supply_margin",
                                "block": block_name,
                                "message": f"Power supply {block_name} operating at >90% capacity ({rail_info['current_amps']:.2f}A / {reg_current_max:.2f}A)"
                            })
        
        # Check lifecycle status
        for block_name, part_data in selected_parts.items():
            lifecycle = part_data.get("lifecycle_status", "active")
            if lifecycle != "active":
                drc_warnings.append({
                    "type": "lifecycle_status",
                    "block": block_name,
                    "message": f"Component has lifecycle status: {lifecycle}"
                })
        
        return {
            "errors": drc_errors,
            "warnings": drc_warnings,
            "error_count": len(drc_errors),
            "warning_count": len(drc_warnings),
            "passed": len(drc_errors) == 0
        }
    
    def _generate_recommendations(
        self,
        power_analysis: Dict[str, Any],
        thermal_analysis: Dict[str, Any],
        drc_results: Dict[str, Any],
        selected_parts: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate design recommendations."""
        recommendations = []
        
        # Power recommendations
        total_power = power_analysis.get("total_power_watts", 0)
        if total_power > 5.0:
            recommendations.append(f"Total power consumption is {total_power:.2f}W - ensure adequate power supply and thermal management")
        
        power_hungry = power_analysis.get("power_hungry_components", [])
        if power_hungry:
            top_consumer = power_hungry[0]
            recommendations.append(f"Highest power consumer: {top_consumer['part_id']} ({top_consumer['power_watts']}W) - consider power optimization")
        
        # Thermal recommendations
        thermal_issues = thermal_analysis.get("thermal_issues", [])
        if thermal_issues:
            recommendations.append(f"Found {len(thermal_issues)} thermal issue(s) - review component placement and consider heatsinks/thermal vias")
        
        # DRC recommendations
        if not drc_results.get("passed", False):
            error_count = drc_results.get("error_count", 0)
            if error_count > 0:
                recommendations.append(f"Design has {error_count} error(s) that must be resolved before manufacturing")
        
        warning_count = drc_results.get("warning_count", 0)
        if warning_count > 0:
            recommendations.append(f"Design has {warning_count} warning(s) - review before finalizing")
        
        # Test point recommendations
        power_rails = power_analysis.get("power_rails", {})
        if len(power_rails) > 0:
            recommendations.append("Add test points for all power rails (3V3, 5V, GND) for debugging")
        
        # General recommendations
        recommendations.append("Add decoupling capacitors close to all IC power pins")
        recommendations.append("Include fiducial marks for automated assembly")
        recommendations.append("Ensure silkscreen labels are clear and include pin 1 markers")
        
        return recommendations

