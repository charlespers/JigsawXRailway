"""
Design Validator Agent
Validates design against industry standards and best practices
"""

from typing import List, Dict, Any, Optional


class DesignValidatorAgent:
    """Validates PCB design against IPC standards and best practices."""
    
    def validate_design(
        self,
        bom_items: List[Dict[str, Any]],
        connections: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Validate design against industry standards.
        
        Args:
            bom_items: List of BOM items
            connections: Optional list of connections
        
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "issues": List[Dict],
                "warnings": List[str],
                "compliance": Dict
            }
        """
        issues = []
        warnings = []
        compliance = {
            "ipc_2221": True,
            "ipc_7351": True,
            "rohs": True,
            "power_budget": True
        }
        
        # Check for required components
        has_power_regulator = False
        has_decoupling_caps = False
        has_protection = False
        
        power_components = []
        total_power = 0.0
        
        for item in bom_items:
            part = item.get("part_data", {})
            category = part.get("category", "")
            
            # Power regulator check
            if "regulator" in category:
                has_power_regulator = True
                power_components.append(part)
            
            # Decoupling capacitors
            if "capacitor" in category:
                has_decoupling_caps = True
            
            # Protection components
            if "protection" in category or "tvs" in category or "polyfuse" in category:
                has_protection = True
            
            # Import safe_float_extract
            from agents.design.design_analyzer import safe_float_extract
            
            # Power consumption estimate - use safe extraction
            current_max = part.get("current_max", {})
            current = safe_float_extract(
                current_max.get("max") if isinstance(current_max, dict) else current_max,
                context=f"current for {part.get('id', 'unknown')}"
            )
            
            voltage_range = part.get("supply_voltage_range", {})
            voltage = safe_float_extract(
                voltage_range.get("nominal") if isinstance(voltage_range, dict) else voltage_range,
                context=f"voltage for {part.get('id', 'unknown')}"
            )
            
            if current > 0 and voltage > 0:
                power = current * voltage
                total_power += power
        
        # Validation checks with actionable recommendations
        if not has_power_regulator:
            issues.append({
                "type": "missing_component",
                "severity": "error",
                "component": None,
                "message": "No power regulator found - design requires power management",
                "current": None,
                "required": "Power regulator (LDO or switching regulator)",
                "recommendation": "Add a power regulator to provide stable voltage rails. For 3.3V systems, consider: TPS62133 (switching) or LP5907 (LDO)",
                "fixable": True,
                "category": "power_management"
            })
            compliance["power_budget"] = False
        
        if not has_decoupling_caps:
            warnings.append({
                "type": "missing_component",
                "severity": "warning",
                "component": None,
                "message": "No decoupling capacitors found - recommended for power supply stability",
                "current": None,
                "required": "Decoupling capacitors (100nF ceramic + 10uF tantalum per IC)",
                "recommendation": "Add 100nF ceramic capacitor within 2mm of each IC power pin, plus 10uF bulk capacitor per power rail",
                "fixable": True,
                "category": "power_management"
            })
        
        if not has_protection:
            warnings.append({
                "type": "missing_component",
                "severity": "warning",
                "component": None,
                "message": "No protection components found - consider ESD/TVS protection for I/O",
                "current": None,
                "required": "ESD/TVS protection diodes on I/O lines",
                "recommendation": "Add TVS diodes (e.g., SMAJ5.0A) on all external I/O lines to protect against ESD events",
                "fixable": True,
                "category": "protection"
            })
        
        # Check power budget
        if power_components:
            for regulator in power_components:
                from agents.design.design_analyzer import safe_float_extract
                reg_current = regulator.get("current_max", {})
                reg_max_current = safe_float_extract(
                    reg_current.get("max") if isinstance(reg_current, dict) else reg_current,
                    context=f"regulator current for {regulator.get('id', 'unknown')}"
                )
                
                if reg_max_current > 0 and total_power / reg_max_current > 0.8:
                    utilization = (total_power / reg_max_current) * 100
                    issues.append({
                        "type": "power_budget",
                        "severity": "warning",
                        "component": regulator.get("id", "regulator"),
                        "message": f"Power consumption ({total_power:.2f}W) exceeds {utilization:.1f}% of regulator capacity ({reg_max_current:.2f}A)",
                        "current": f"{total_power:.2f}W ({utilization:.1f}% utilization)",
                        "required": f"< 80% of {reg_max_current:.2f}A capacity",
                        "recommendation": f"Upgrade to regulator with >{reg_max_current * 1.25:.2f}A capacity or reduce power consumption",
                        "fixable": True,
                        "category": "power_management"
                    })
        
        # Check RoHS compliance
        non_rohs_parts = []
        for item in bom_items:
            part = item.get("part_data", {})
            rohs = part.get("rohs_compliant")
            if rohs is False:
                non_rohs_parts.append(part.get("name"))
                compliance["rohs"] = False
        
        if non_rohs_parts:
            warnings.append({
                "type": "rohs_compliance",
                "severity": "warning",
                "component": ", ".join(non_rohs_parts),
                "message": f"Non-RoHS compliant parts found: {', '.join(non_rohs_parts)}",
                "current": "Non-RoHS",
                "required": "RoHS compliant parts",
                "recommendation": "Replace with RoHS-compliant alternatives to meet environmental regulations",
                "fixable": True,
                "category": "compliance"
            })
        
        # Check footprint compliance (IPC-7351) - structured warnings
        for item in bom_items:
            part = item.get("part_data", {})
            footprint = part.get("footprint")
            if not footprint:
                part_name = part.get("name") or part.get("id") or "Unknown"
                package = part.get("package", "")
                warnings.append({
                    "type": "missing_footprint",
                    "severity": "warning",
                    "component": part_name,
                    "message": f"{part_name} missing IPC-7351 footprint designation",
                    "current": None,
                    "required": f"IPC-7351 compliant footprint for {package}",
                    "recommendation": f"Add footprint designation (e.g., {package}_IPC7351) or use standard library footprint",
                    "fixable": True,
                    "category": "ipc_compliance"
                })
        
        # Check MSL levels for ICs - structured warnings
        for item in bom_items:
            part = item.get("part_data", {})
            category = part.get("category", "")
            if "ic" in category.lower() or "mcu" in category.lower():
                msl = part.get("msl_level")
                if not msl:
                    part_name = part.get("name") or part.get("id") or "Unknown"
                    warnings.append({
                        "type": "missing_msl",
                        "severity": "warning",
                        "component": part_name,
                        "message": f"{part_name} missing MSL level - required for assembly planning",
                        "current": None,
                        "required": "MSL level (1-6) per J-STD-020",
                        "recommendation": "Add MSL level to part data. Most ICs are MSL 3. Check datasheet for exact value.",
                        "fixable": True,
                        "category": "assembly_planning"
                    })
        
        valid = len([i for i in issues if i.get("severity") == "error"]) == 0
        
        # Calculate compliance score (0-100)
        # Start with 100 and deduct for each compliance failure
        compliance_score = 100.0
        
        # Deduct points for each compliance failure
        if not compliance.get("ipc_2221", True):
            compliance_score -= 25.0
        if not compliance.get("ipc_7351", True):
            compliance_score -= 25.0
        if not compliance.get("rohs", True):
            compliance_score -= 20.0
        if not compliance.get("power_budget", True):
            compliance_score -= 30.0
        
        # Deduct points for errors (5 points per error)
        error_count = len([i for i in issues if i.get("severity") == "error"])
        compliance_score -= error_count * 5.0
        
        # Deduct points for warnings (1 point per warning, max 10 points)
        warning_count = len(warnings)
        compliance_score -= min(warning_count * 1.0, 10.0)
        
        # Ensure score is between 0 and 100
        compliance_score = max(0.0, min(100.0, compliance_score))
        
        # Calculate summary statistics
        summary = {
            "error_count": error_count,
            "warning_count": warning_count,
            "compliance_score": round(compliance_score, 1)
        }
        
        return {
            "valid": valid,
            "issues": issues,
            "warnings": warnings,
            "compliance": compliance,
            "summary": summary
        }

