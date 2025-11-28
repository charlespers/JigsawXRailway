"""
Design Analyzer Agent
Performs power consumption analysis, thermal analysis, and design rule checks
"""

from typing import Dict, Any, List, Optional, Union
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def safe_float_extract(value: Any, default: float = 0.0, context: str = "") -> float:
    """
    Safely extract a float value from nested dicts or direct values.
    Recursively extracts until a number is found.
    Enhanced with logging for debugging dict/float multiplication errors.
    
    Args:
        value: The value to extract (can be dict, list, number, or string)
        default: Default value if extraction fails
        context: Optional context string for logging (e.g., "voltage for U1")
    """
    if value is None:
        return default
    
    # If already a number, return it
    if isinstance(value, (int, float)):
        return float(value)
    
    # If it's a dict, recursively extract
    if isinstance(value, dict):
        # Log warning for deeply nested dicts (potential issue)
        if len(value) > 3 and context:
            logger.warning(f"[FLOAT_EXTRACT] Deeply nested dict in {context}: keys={list(value.keys())[:5]}")
        
        # Try common keys in order of preference
        for key in ["value", "nominal", "max", "typical", "min"]:
            if key in value:
                result = safe_float_extract(value[key], default, f"{context}.{key}" if context else key)
                if result != default:
                    return result
        
        # If no common keys, try first value
        if value:
            first_key = next(iter(value.keys()))
            result = safe_float_extract(value[first_key], default, f"{context}.{first_key}" if context else first_key)
            if result != default:
                return result
        
        if context:
            logger.warning(f"[FLOAT_EXTRACT] Could not extract float from dict in {context}, using default {default}")
        return default
    
    # If it's a list, try first element
    if isinstance(value, list):
        if value and len(value) > 0:
            logger.warning(f"[FLOAT_EXTRACT] Value is a list in {context}, using first element")
            return safe_float_extract(value[0], default, context)
        return default
    
    # Try to convert to float
    try:
        return float(value)
    except (ValueError, TypeError) as e:
        if context:
            logger.warning(f"[FLOAT_EXTRACT] Failed to convert {type(value).__name__} to float in {context}: {e}, using default {default}")
        return default


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
        
        # Ensure selected_parts is a dict, not a list
        if not isinstance(selected_parts, dict):
            # If it's a list, convert to dict
            if isinstance(selected_parts, list):
                selected_parts = {f"part_{i}": part for i, part in enumerate(selected_parts) if isinstance(part, dict)}
            else:
                return {
                    "power_rails": {},
                    "total_power_watts": 0.0,
                    "component_power": {},
                    "power_hungry_components": []
                }
        
        # Analyze each component
        for block_name, part_data in selected_parts.items():
            # Ensure part_data is a dict
            if not isinstance(part_data, dict):
                continue  # Skip invalid entries
            
            part_id = part_data.get("id", block_name)
            
            # Get supply voltage - use safe extraction
            supply_range = part_data.get("supply_voltage_range", {})
            if isinstance(supply_range, dict):
                voltage = safe_float_extract(supply_range.get("nominal") or supply_range.get("value") or supply_range.get("max"))
            else:
                voltage = safe_float_extract(supply_range)
            
            # Get current consumption - use safe extraction
            current_max = part_data.get("current_max", {})
            if isinstance(current_max, dict):
                current = safe_float_extract(current_max.get("max") or current_max.get("typical") or current_max.get("value"))
            else:
                current = safe_float_extract(current_max)
            
            # Use safe extraction with context for debugging
            voltage_float = safe_float_extract(voltage, context=f"voltage for {part_id}")
            current_float = safe_float_extract(current, context=f"current for {part_id}")
            
            # Skip if voltage is invalid
            if voltage_float <= 0:
                continue
            
            if voltage_float > 0 and current_float > 0:
                power = voltage_float * current_float
                # Use float voltage as key to ensure it's hashable
                power_rails[voltage_float] += current_float
                component_power[part_id] = {
                    "voltage": voltage,
                    "current": current,
                    "power": power
                }
        
        # Calculate total power - ensure all values are floats
        total_power = 0.0
        for voltage_key, rail_current in power_rails.items():
            # Use safe extraction for both key and value
            voltage_float = safe_float_extract(voltage_key)
            current_float = safe_float_extract(rail_current)
            
            # Final check before multiplication
            if voltage_float > 0 and current_float > 0:
                total_power += voltage_float * current_float
        
        # Find power-hungry components
        power_hungry = []
        for part_id, power_info in component_power.items():
            # Use safe extraction for power values
            power_watts = safe_float_extract(power_info.get("power", 0.0))
            if power_watts > 0.5:  # > 500mW
                power_hungry.append({
                    "part_id": part_id,
                    "power_watts": round(power_watts, 3),
                    "voltage": safe_float_extract(power_info.get("voltage", 0.0)),
                    "current_amps": safe_float_extract(power_info.get("current", 0.0))
                })
        
        # Sort by power consumption
        power_hungry.sort(key=lambda x: x["power_watts"], reverse=True)
        
        # Build power rails dict - ensure all values are floats
        power_rails_dict = {}
        for voltage_key, current_value in power_rails.items():
            # Use safe extraction
            voltage_float = safe_float_extract(voltage_key)
            current_float = safe_float_extract(current_value)
            
            if voltage_float > 0:  # Only add valid rails
                power_rails_dict[f"{voltage_float}V"] = {
                    "voltage": voltage_float,
                    "current_amps": round(current_float, 3),
                    "power_watts": round(voltage_float * current_float, 3)
                }
        
        return {
            "power_rails": power_rails_dict,
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
                max_temp_value = None
                if isinstance(max_temp, dict):
                    max_temp_value = max_temp.get("max") or max_temp.get("value")
                    # Recursively extract if still a dict
                    while isinstance(max_temp_value, dict):
                        max_temp_value = max_temp_value.get("value") or max_temp_value.get("max") or None
                else:
                    max_temp_value = max_temp
                
                # Ensure max_temp_value is a float
                if max_temp_value is not None:
                    try:
                        max_temp_value = float(max_temp_value)
                    except (ValueError, TypeError):
                        max_temp_value = None
                
                # Calculate junction temperature (assuming 25°C ambient)
                ambient_temp = 25.0
                theta_ja_float = safe_float_extract(theta_ja) if theta_ja is not None else None
                if theta_ja_float and theta_ja_float > 0 and power_dissipation > 0:
                    junction_temp = ambient_temp + (power_dissipation * theta_ja_float)
                    
                    thermal_ok = True
                    if max_temp_value is not None and max_temp_value > 0 and junction_temp > max_temp_value:
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
                        "max_temp_c": max_temp_value if max_temp_value is not None else 0.0,
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
        # Ensure selected_parts is a dict
        if not isinstance(selected_parts, dict):
            if isinstance(selected_parts, list):
                selected_parts = {f"part_{i}": part for i, part in enumerate(selected_parts) if isinstance(part, dict)}
            else:
                return {
                    "errors": [],
                    "warnings": [],
                    "error_count": 0,
                    "warning_count": 0,
                    "passed": True
                }
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
        # Ensure selected_parts is a dict
        if not isinstance(selected_parts, dict):
            if isinstance(selected_parts, list):
                selected_parts = {f"part_{i}": part for i, part in enumerate(selected_parts) if isinstance(part, dict)}
            else:
                return {
                    "errors": drc_errors,
                    "warnings": drc_warnings,
                    "error_count": len(drc_errors),
                    "warning_count": len(drc_warnings),
                    "passed": len(drc_errors) == 0
                }
        
        for rail_name, rail_info in power_rails.items():
            # Find power supply for this rail
            for block_name, part_data in selected_parts.items():
                # Ensure part_data is a dict
                if not isinstance(part_data, dict):
                    continue
                category = part_data.get("category", "")
                if "regulator" in category:
                    output_voltage = part_data.get("output_voltage")
                    if isinstance(output_voltage, dict):
                        reg_voltage = output_voltage.get("nominal") or output_voltage.get("value")
                    else:
                        reg_voltage = output_voltage
                    
                    # Ensure reg_voltage is a float
                    if isinstance(reg_voltage, dict):
                        reg_voltage = reg_voltage.get("value") or reg_voltage.get("nominal") or reg_voltage.get("max") or 0.0
                    try:
                        reg_voltage = float(reg_voltage) if reg_voltage else 0.0
                    except (ValueError, TypeError):
                        reg_voltage = 0.0
                    
                    # Ensure rail_info["voltage"] is a float
                    rail_voltage = rail_info.get("voltage", 0.0)
                    if isinstance(rail_voltage, dict):
                        rail_voltage = rail_voltage.get("value") or rail_voltage.get("nominal") or rail_voltage.get("max") or 0.0
                    try:
                        rail_voltage = float(rail_voltage) if rail_voltage else 0.0
                    except (ValueError, TypeError):
                        rail_voltage = 0.0
                    
                    if reg_voltage > 0 and rail_voltage > 0 and abs(reg_voltage - rail_voltage) < 0.1:
                        # Check current capacity
                        reg_current = part_data.get("current_max", {})
                        reg_current_max = 0.0
                        if isinstance(reg_current, dict):
                            reg_current_max = reg_current.get("max") or reg_current.get("typical") or 0.0
                            # Recursively extract if still a dict
                            while isinstance(reg_current_max, dict):
                                reg_current_max = reg_current_max.get("value") or reg_current_max.get("max") or reg_current_max.get("typical") or 0.0
                        else:
                            reg_current_max = reg_current or 0.0
                        
                        try:
                            reg_current_max = float(reg_current_max) if reg_current_max else 0.0
                        except (ValueError, TypeError):
                            reg_current_max = 0.0
                        
                        # Ensure rail_info["current_amps"] is a float
                        rail_current_amps = rail_info.get("current_amps", 0.0)
                        if isinstance(rail_current_amps, dict):
                            rail_current_amps = rail_current_amps.get("value") or rail_current_amps.get("max") or 0.0
                        try:
                            rail_current_amps = float(rail_current_amps) if rail_current_amps else 0.0
                        except (ValueError, TypeError):
                            rail_current_amps = 0.0
                        
                        if reg_current_max > 0 and rail_current_amps > 0 and rail_current_amps > reg_current_max * 0.9:
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
            recommendations.append("Consider adding test points for power rails for debugging")
        
        return recommendations
    
    def generate_actionable_recommendations(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate specific, actionable recommendations with part suggestions.
        
        Args:
            selected_parts: Dictionary of selected parts
            analysis_results: Results from analyze_design
        
        Returns:
            List of actionable recommendations, each with:
            - issue_description: str
            - suggested_parts: List[Dict] (optional)
            - expected_improvement: str
            - cost_impact: Dict (optional)
            - priority: str ("high", "medium", "low")
            - category: str ("power", "thermal", "compliance", etc.)
        """
        recommendations = []
        
        power_analysis = analysis_results.get("power_analysis", {})
        thermal_analysis = analysis_results.get("thermal_analysis", {})
        drc_results = analysis_results.get("design_rule_checks", {})
        
        # Power-related recommendations
        total_power = power_analysis.get("total_power_watts", 0)
        if total_power > 5.0:
            recommendations.append({
                "issue_description": f"High power consumption ({total_power:.2f}W) - ensure adequate power supply and thermal management",
                "suggested_parts": [],  # Could suggest higher capacity regulators
                "expected_improvement": "Prevent thermal issues and ensure stable operation",
                "cost_impact": None,
                "priority": "high",
                "category": "power"
            })
        
        power_hungry = power_analysis.get("power_hungry_components", [])
        if power_hungry:
            top_consumer = power_hungry[0]
            recommendations.append({
                "issue_description": f"High power consumer: {top_consumer['part_id']} ({top_consumer['power_watts']}W)",
                "suggested_parts": [],  # Could suggest lower power alternatives
                "expected_improvement": "Reduce overall power consumption and thermal load",
                "cost_impact": None,
                "priority": "medium",
                "category": "power"
            })
        
        # Thermal recommendations
        thermal_issues = thermal_analysis.get("thermal_issues", [])
        if thermal_issues:
            critical_thermal = [t for t in thermal_issues if t.get("severity") == "critical"]
            if critical_thermal:
                recommendations.append({
                    "issue_description": f"{len(critical_thermal)} critical thermal issue(s) identified",
                    "suggested_parts": [],  # Could suggest heatsinks, thermal pads
                    "expected_improvement": "Prevent component failure and improve reliability",
                    "cost_impact": None,
                    "priority": "high",
                    "category": "thermal"
                })
        
        # DRC recommendations
        drc_errors = drc_results.get("errors", [])
        if drc_errors:
            recommendations.append({
                "issue_description": f"{len(drc_errors)} design rule check error(s) must be resolved",
                "suggested_parts": [],
                "expected_improvement": "Ensure design meets manufacturing requirements",
                "cost_impact": None,
                "priority": "high",
                "category": "compliance"
            })
        
        drc_warnings = drc_results.get("warnings", [])
        if drc_warnings:
            recommendations.append({
                "issue_description": f"{len(drc_warnings)} design rule check warning(s) - review recommended",
                "suggested_parts": [],
                "expected_improvement": "Improve design quality and manufacturability",
                "cost_impact": None,
                "priority": "medium",
                "category": "compliance"
            })
        
        # Missing components recommendations
        missing_components = []
        has_regulator = any("regulator" in p.get("category", "").lower() for p in selected_parts.values())
        has_decoupling = any("capacitor" in p.get("category", "").lower() for p in selected_parts.values())
        has_protection = any("protection" in p.get("category", "").lower() or "tvs" in p.get("category", "").lower() for p in selected_parts.values())
        
        if not has_regulator:
            missing_components.append("power regulator")
        if not has_decoupling:
            missing_components.append("decoupling capacitors")
        if not has_protection:
            missing_components.append("ESD/TVS protection")
        
        if missing_components:
            recommendations.append({
                "issue_description": f"Missing recommended components: {', '.join(missing_components)}",
                "suggested_parts": [],  # AutoFixAgent will populate these
                "expected_improvement": "Improve design reliability and compliance",
                "cost_impact": None,
                "priority": "medium",
                "category": "compliance"
            })
        
        # General recommendations
        recommendations.append({
            "issue_description": "Add test points for all power rails (3V3, 5V, GND) for debugging",
            "suggested_parts": [],
            "expected_improvement": "Enable easier debugging and testing",
            "cost_impact": None,
            "priority": "low",
            "category": "testability"
        })
        recommendations.append({
            "issue_description": "Add decoupling capacitors close to all IC power pins",
            "suggested_parts": [],
            "expected_improvement": "Improve power supply stability and reduce noise",
            "cost_impact": None,
            "priority": "medium",
            "category": "power"
        })
        recommendations.append({
            "issue_description": "Include fiducial marks for automated assembly",
            "suggested_parts": [],
            "expected_improvement": "Enable automated pick-and-place assembly",
            "cost_impact": None,
            "priority": "medium",
            "category": "manufacturing"
        })
        recommendations.append({
            "issue_description": "Ensure silkscreen labels are clear and include pin 1 markers",
            "suggested_parts": [],
            "expected_improvement": "Improve assembly accuracy and debugging",
            "cost_impact": None,
            "priority": "low",
            "category": "manufacturing"
        })
        
        return recommendations

