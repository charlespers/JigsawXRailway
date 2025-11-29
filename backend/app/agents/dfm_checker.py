"""
DFM (Design for Manufacturability) checker agent
Validates design for manufacturing readiness - solves manufacturing defect pain points
"""
import logging
from typing import Dict, List, Any
from app.domain.models import BOM, BOMItem, MountingType

logger = logging.getLogger(__name__)


class DFMCheckerAgent:
    """
    Checks design for manufacturability issues.
    Solves: "Will this design be manufacturable? Are there assembly issues?"
    """
    
    def check_design(
        self,
        bom: BOM,
        selected_parts: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check design for manufacturability issues
        
        Args:
            bom: Bill of Materials
            selected_parts: Selected parts dictionary
        
        Returns:
            DFM analysis with issues, warnings, and recommendations
        """
        issues = []
        warnings = []
        recommendations = []
        
        # Check for missing footprints
        missing_footprints = []
        for item in bom.items:
            if not item.footprint or item.footprint == "":
                missing_footprints.append(item.designator)
                issues.append(f"Missing footprint for {item.designator} ({item.mfr_part_number})")
        
        if missing_footprints:
            recommendations.append("Add IPC-7351 compliant footprints for all components")
        
        # Check for MSL (Moisture Sensitivity Level) issues
        msl_issues = []
        for item in bom.items:
            if item.msl_level and item.msl_level >= 3:
                msl_issues.append({
                    "designator": item.designator,
                    "msl_level": item.msl_level,
                    "requires_baking": item.msl_level >= 3
                })
                if item.msl_level >= 5:
                    warnings.append(
                        f"CRITICAL: {item.designator} has MSL {item.msl_level} - "
                        "must be assembled within 168 hours after baking"
                    )
        
        if msl_issues:
            recommendations.append(
                "Ensure proper MSL handling: components with MSL ≥3 require baking before assembly"
            )
        
        # Check for mixed mounting types
        mounting_types = set(item.mounting_type for item in bom.items)
        if len(mounting_types) > 1:
            warnings.append(
                f"Mixed mounting types detected: {', '.join(mounting_types)}. "
                "This may require multiple assembly passes"
            )
            recommendations.append("Consider standardizing on SMT for cost efficiency")
        
        # Check for through-hole components (more expensive)
        th_count = sum(1 for item in bom.items if item.mounting_type == MountingType.THROUGH_HOLE)
        if th_count > 0:
            warnings.append(
                f"{th_count} through-hole component(s) detected. "
                "Consider SMT alternatives for cost reduction"
            )
        
        # Check for components requiring special handling
        special_handling = []
        for item in bom.items:
            part = selected_parts.get(item.designator) or {}
            if part.get("esd_sensitivity"):
                special_handling.append(f"{item.designator}: ESD sensitive")
            if part.get("orientation_required"):
                special_handling.append(f"{item.designator}: Orientation critical")
            if part.get("polarity_required"):
                special_handling.append(f"{item.designator}: Polarity critical")
        
        if special_handling:
            warnings.append("Components requiring special handling:")
            warnings.extend(special_handling)
            recommendations.append("Ensure assembly instructions include special handling requirements")
        
        # Check for fiducials and test points
        has_fiducials = any("fiducial" in item.description.lower() for item in bom.items)
        has_test_points = any("test" in item.description.lower() for item in bom.items)
        
        if not has_fiducials:
            recommendations.append("Add fiducial marks for automated assembly")
        
        if not has_test_points and len(bom.items) > 10:
            recommendations.append("Consider adding test points for debugging and validation")
        
        # Check package sizes (very small packages are harder to assemble)
        small_packages = []
        for item in bom.items:
            package = item.package.upper()
            if "0201" in package or "01005" in package:
                small_packages.append(f"{item.designator}: {item.package}")
        
        if small_packages:
            warnings.append(
                f"Very small packages detected ({len(small_packages)} components). "
                "May require specialized assembly equipment"
            )
        
        # Check for RoHS compliance
        non_rohs = [item.designator for item in bom.items 
                    if hasattr(item, 'rohs_compliant') and not getattr(item, 'rohs_compliant', True)]
        if non_rohs:
            warnings.append(f"Non-RoHS components detected: {', '.join(non_rohs)}")
        
        return {
            "dfm_score": self._calculate_dfm_score(issues, warnings),
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "msl_components": msl_issues,
            "special_handling_required": len(special_handling) > 0,
            "manufacturing_readiness": "ready" if len(issues) == 0 else "needs_attention"
        }
    
    def _calculate_dfm_score(self, issues: List[str], warnings: List[str]) -> int:
        """Calculate DFM score (0-100)"""
        score = 100
        score -= len(issues) * 10  # Each issue costs 10 points
        score -= len(warnings) * 3  # Each warning costs 3 points
        return max(0, score)

