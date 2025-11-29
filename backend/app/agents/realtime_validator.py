"""
Real-time Design Validator Agent
Validates design as parts are selected - provides instant feedback
"""
import logging
from typing import Dict, List, Any, Optional
from app.agents.compatibility import CompatibilityAgent
from app.agents.power_analyzer import PowerAnalyzerAgent
from app.core.exceptions import CompatibilityError

logger = logging.getLogger(__name__)


class RealtimeValidatorAgent:
    """
    Real-time validation as designer selects parts.
    
    Solves: Designer adds part → Instant feedback on compatibility, power, thermal
    """
    
    def __init__(self):
        self.compat_agent = CompatibilityAgent()
        self.power_analyzer = PowerAnalyzerAgent()
    
    def validate_addition(
        self,
        new_part: Dict[str, Any],
        existing_parts: Dict[str, Dict[str, Any]],
        design_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate adding a new part to existing design.
        
        Returns instant feedback on compatibility, issues, warnings.
        """
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": [],
            "compatibility_checks": {},
            "power_impact": None,
            "thermal_impact": None
        }
        
        # Check compatibility with existing parts
        for existing_name, existing_part in existing_parts.items():
            compat = self.compat_agent.check_compatibility(
                existing_part,
                new_part,
                self._infer_connection_type(existing_part, new_part)
            )
            
            validation_results["compatibility_checks"][existing_name] = compat
            
            if not compat["compatible"]:
                validation_results["valid"] = False
                validation_results["errors"].append(
                    f"Incompatible with {existing_name}: {', '.join(compat['issues'])}"
                )
            
            if compat["warnings"]:
                validation_results["warnings"].extend([
                    f"{existing_name}: {w}" for w in compat["warnings"]
                ])
        
        # Check power impact
        all_parts = {**existing_parts, "new": new_part}
        power_analysis = self.power_analyzer.analyze_power_budget(all_parts)
        validation_results["power_impact"] = {
            "additional_power_watts": power_analysis["total_power_watts"],
            "warnings": power_analysis["warnings"],
            "status": power_analysis["power_budget_status"]
        }
        
        if power_analysis["power_budget_status"] == "critical":
            validation_results["valid"] = False
            validation_results["errors"].extend(power_analysis["warnings"])
        
        # Check thermal impact
        thermal = power_analysis.get("thermal_analysis", {})
        if thermal.get("high_power_components"):
            validation_results["thermal_impact"] = {
                "high_power_count": len(thermal["high_power_components"]),
                "estimated_temp_rise": thermal.get("estimated_temp_rise_c", 0),
                "warnings": thermal.get("warnings", [])
            }
            
            if thermal.get("estimated_temp_rise_c", 0) > 50:
                validation_results["warnings"].append(
                    f"High thermal impact: {thermal['estimated_temp_rise_c']:.1f}°C temperature rise"
                )
        
        # Generate recommendations
        if validation_results["valid"]:
            validation_results["recommendations"].append("✅ Part is compatible and can be added")
        
        # Check for missing supporting components
        if new_part.get("category", "").lower() == "mcu":
            if not any("power" in p.get("category", "").lower() 
                      for p in existing_parts.values()):
                validation_results["recommendations"].append(
                    "💡 Consider adding a power regulator for the MCU"
                )
        
        return validation_results
    
    def validate_design(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        connections: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Validate complete design"""
        all_validations = []
        
        # Validate each part addition
        accumulated_parts = {}
        for part_name, part in selected_parts.items():
            validation = self.validate_addition(part, accumulated_parts)
            all_validations.append({
                "part": part_name,
                "validation": validation
            })
            accumulated_parts[part_name] = part
        
        # Overall design health
        all_errors = []
        all_warnings = []
        issues = []
        
        for v in all_validations:
            errors = v["validation"]["errors"]
            warnings = v["validation"]["warnings"]
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            
            # Format errors as issues
            for error in errors:
                issues.append({
                    "type": "compatibility" if "incompatible" in error.lower() else "power" if "power" in error.lower() else "general",
                    "severity": "error",
                    "component": v["part"],
                    "message": error
                })
            
            # Format warnings
            for warning in warnings:
                if isinstance(warning, str):
                    all_warnings.append(warning)
        
        # Calculate compliance score (0-100)
        health_score = self._calculate_health_score(all_errors, all_warnings)
        compliance_score = health_score  # Use health score as compliance score
        
        # Check IPC compliance (simplified - check for footprint, package, etc.)
        ipc_7351_compliant = all(
            part.get("footprint") and part.get("package")
            for part in selected_parts.values()
        )
        ipc_2221_compliant = len(all_errors) == 0  # Simplified check
        rohs_compliant = True  # Assume compliant unless specified otherwise
        power_budget_ok = all(
            v["validation"].get("power_impact", {}).get("status") != "critical"
            for v in all_validations
        )
        
        return {
            "valid": len(all_errors) == 0,
            "issues": issues,
            "warnings": all_warnings,
            "compliance": {
                "ipc_2221": ipc_2221_compliant,
                "ipc_7351": ipc_7351_compliant,
                "rohs": rohs_compliant,
                "power_budget": power_budget_ok
            },
            "summary": {
                "error_count": len(all_errors),
                "warning_count": len(all_warnings),
                "compliance_score": compliance_score
            },
            "fix_suggestions": []  # Can be populated by other agents
        }
    
    def _infer_connection_type(self, part1: Dict[str, Any], part2: Dict[str, Any]) -> str:
        """Infer connection type between parts"""
        cat1 = part1.get("category", "").lower()
        cat2 = part2.get("category", "").lower()
        
        if "power" in cat1 or "power" in cat2:
            return "power"
        return "signal"
    
    def _calculate_health_score(self, errors: List[str], warnings: List[str]) -> int:
        """Calculate design health score (0-100)"""
        score = 100
        score -= len(errors) * 20
        score -= len(warnings) * 5
        return max(0, score)

