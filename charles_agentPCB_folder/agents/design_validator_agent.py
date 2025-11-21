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
            
            # Power consumption estimate
            current_max = part.get("current_max", {})
            if isinstance(current_max, dict):
                current = current_max.get("max") or current_max.get("typical", 0)
                # Ensure current is a float, not a dict
                if isinstance(current, dict):
                    current = current.get("value") or current.get("max") or 0.0
                current = float(current) if current else 0.0
            else:
                current = float(current_max) if current_max else 0.0
            
            voltage_range = part.get("supply_voltage_range", {})
            if isinstance(voltage_range, dict):
                voltage = voltage_range.get("nominal") or voltage_range.get("max", 0)
                # Ensure voltage is a float, not a dict
                if isinstance(voltage, dict):
                    voltage = voltage.get("value") or voltage.get("nominal") or 0.0
                voltage = float(voltage) if voltage else 0.0
            else:
                voltage = float(voltage_range) if voltage_range else 0.0
            
            if current > 0 and voltage > 0:
                power = current * voltage
                total_power += power
        
        # Validation checks
        if not has_power_regulator:
            issues.append({
                "type": "missing_component",
                "severity": "error",
                "message": "No power regulator found - design requires power management"
            })
            compliance["power_budget"] = False
        
        if not has_decoupling_caps:
            warnings.append("No decoupling capacitors found - recommended for power supply stability")
        
        if not has_protection:
            warnings.append("No protection components found - consider ESD/TVS protection for I/O")
        
        # Check power budget
        if power_components:
            for regulator in power_components:
                reg_current = regulator.get("current_max", {})
                if isinstance(reg_current, dict):
                    reg_max_current = reg_current.get("max") or reg_current.get("typical", 0)
                else:
                    reg_max_current = reg_current or 0
                
                if reg_max_current > 0 and total_power / reg_max_current > 0.8:
                    issues.append({
                        "type": "power_budget",
                        "severity": "warning",
                        "message": f"Power consumption ({total_power:.2f}W) may exceed regulator capacity"
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
            warnings.append(f"Non-RoHS compliant parts found: {', '.join(non_rohs_parts)}")
        
        # Check footprint compliance (IPC-7351)
        for item in bom_items:
            part = item.get("part_data", {})
            footprint = part.get("footprint")
            if not footprint:
                warnings.append(f"{part.get('name')} missing IPC-7351 footprint designation")
        
        # Check MSL levels for ICs
        for item in bom_items:
            part = item.get("part_data", {})
            category = part.get("category", "")
            if "ic" in category or "mcu" in category:
                msl = part.get("msl_level")
                if not msl:
                    warnings.append(f"{part.get('name')} missing MSL level - required for assembly planning")
        
        valid = len([i for i in issues if i.get("severity") == "error"]) == 0
        
        return {
            "valid": valid,
            "issues": issues,
            "warnings": warnings,
            "compliance": compliance
        }

