"""
Manufacturing Readiness Agent
Provides DFM checks, assembly complexity analysis, test point coverage, and panelization recommendations
"""

from typing import List, Dict, Any, Optional


class ManufacturingReadinessAgent:
    """Provides manufacturing readiness analysis."""
    
    def analyze_manufacturing_readiness(
        self,
        bom_items: List[Dict[str, Any]],
        connections: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Perform manufacturing readiness analysis.
        
        Args:
            bom_items: List of BOM items with part data
            connections: Optional list of connections
        
        Returns:
            Dictionary with manufacturing analysis:
            {
                "dfm_checks": Dict,
                "assembly_complexity": Dict,
                "test_point_coverage": Dict,
                "panelization_recommendations": List[str],
                "overall_readiness": str,
                "recommendations": List[str]
            }
        """
        dfm_checks = self._perform_dfm_checks(bom_items)
        assembly_complexity = self._analyze_assembly_complexity(bom_items)
        test_point_coverage = self._analyze_test_points(bom_items, connections)
        panelization_recommendations = self._get_panelization_recommendations(bom_items)
        
        # Determine overall readiness
        critical_issues = sum(1 for check in dfm_checks.values() if isinstance(check, dict) and check.get("status") == "fail")
        warnings = sum(1 for check in dfm_checks.values() if isinstance(check, dict) and check.get("status") == "warning")
        
        if critical_issues > 0:
            overall_readiness = "not_ready"
        elif warnings > 3:
            overall_readiness = "needs_review"
        else:
            overall_readiness = "ready"
        
        # Generate recommendations
        recommendations = []
        
        if critical_issues > 0:
            recommendations.append(f"{critical_issues} critical DFM issue(s) must be resolved before manufacturing")
        
        if warnings > 0:
            recommendations.append(f"{warnings} warning(s) should be reviewed")
        
        if assembly_complexity.get("complexity_score", 0) > 7:
            recommendations.append("High assembly complexity - consider simplifying design or using assembly house with advanced capabilities")
        
        if test_point_coverage.get("coverage_percentage", 0) < 80:
            recommendations.append(f"Test point coverage ({test_point_coverage['coverage_percentage']:.1f}%) is below recommended 80%")
        
        if not recommendations:
            recommendations.append("Design appears ready for manufacturing")
        
        return {
            "dfm_checks": dfm_checks,
            "assembly_complexity": assembly_complexity,
            "test_point_coverage": test_point_coverage,
            "panelization_recommendations": panelization_recommendations,
            "overall_readiness": overall_readiness,
            "recommendations": recommendations
        }
    
    def _perform_dfm_checks(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform Design for Manufacturing (DFM) checks."""
        checks = {}
        
        # Check for minimum component spacing
        has_bga = any("BGA" in str(part.get("part_data", {}).get("package", "")).upper() 
                     for part in bom_items)
        has_qfn = any("QFN" in str(part.get("part_data", {}).get("package", "")).upper() 
                     for part in bom_items)
        
        checks["component_spacing"] = {
            "status": "pass" if not (has_bga and has_qfn) else "warning",
            "message": "BGA and QFN packages detected - ensure adequate spacing for rework" if (has_bga and has_qfn) else "Component spacing appears adequate"
        }
        
        # Check for fine-pitch components
        fine_pitch_count = 0
        for item in bom_items:
            part = item.get("part_data", {})
            package = part.get("package", "")
            if any(fp in package.upper() for fp in ["QFN", "BGA", "CSP", "WLCSP"]):
                fine_pitch_count += 1
        
        checks["fine_pitch_components"] = {
            "status": "pass" if fine_pitch_count < 5 else "warning",
            "count": fine_pitch_count,
            "message": f"{fine_pitch_count} fine-pitch component(s) - ensure assembly house can handle" if fine_pitch_count >= 5 else "Fine-pitch component count is manageable"
        }
        
        # Check for through-hole components
        through_hole_count = sum(1 for item in bom_items 
                                 if "through" in str(item.get("part_data", {}).get("package", "")).lower() or
                                    "DIP" in str(item.get("part_data", {}).get("package", "")).upper())
        
        checks["through_hole_components"] = {
            "status": "pass" if through_hole_count == 0 else "warning",
            "count": through_hole_count,
            "message": f"{through_hole_count} through-hole component(s) - may require manual assembly" if through_hole_count > 0 else "All components are SMT"
        }
        
        # Check for missing footprints
        missing_footprints = sum(1 for item in bom_items 
                               if not item.get("part_data", {}).get("footprint"))
        
        checks["footprint_coverage"] = {
            "status": "fail" if missing_footprints > 0 else "pass",
            "missing_count": missing_footprints,
            "message": f"{missing_footprints} component(s) missing footprint designation" if missing_footprints > 0 else "All components have footprint designations"
        }
        
        # Check for missing MSL levels
        missing_msl = sum(1 for item in bom_items 
                         if not item.get("part_data", {}).get("msl_level"))
        
        checks["msl_coverage"] = {
            "status": "warning" if missing_msl > 0 else "pass",
            "missing_count": missing_msl,
            "message": f"{missing_msl} component(s) missing MSL level - required for assembly planning" if missing_msl > 0 else "All components have MSL levels"
        }
        
        return checks
    
    def _analyze_assembly_complexity(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze assembly complexity."""
        total_components = sum(item.get("quantity", 1) for item in bom_items)
        unique_components = len(bom_items)
        
        # Count components by package type
        package_types = {}
        for item in bom_items:
            package = item.get("part_data", {}).get("package", "unknown")
            package_types[package] = package_types.get(package, 0) + item.get("quantity", 1)
        
        # Calculate complexity score (0-10)
        complexity_score = 0
        
        # Fine-pitch components add complexity
        fine_pitch_packages = ["QFN", "BGA", "CSP", "WLCSP", "LGA"]
        fine_pitch_count = sum(qty for pkg, qty in package_types.items() 
                              if any(fp in pkg.upper() for fp in fine_pitch_packages))
        complexity_score += min(fine_pitch_count / 10.0, 3.0)
        
        # High component count adds complexity
        if total_components > 50:
            complexity_score += min((total_components - 50) / 20.0, 2.0)
        
        # Many unique components adds complexity
        if unique_components > 30:
            complexity_score += min((unique_components - 30) / 15.0, 2.0)
        
        # Through-hole components add complexity
        through_hole_count = sum(qty for pkg, qty in package_types.items() 
                                if "through" in pkg.lower() or "DIP" in pkg.upper())
        if through_hole_count > 0:
            complexity_score += 1.0
        
        complexity_score = min(complexity_score, 10.0)
        
        if complexity_score < 3:
            complexity_level = "low"
        elif complexity_score < 6:
            complexity_level = "medium"
        else:
            complexity_level = "high"
        
        return {
            "total_components": total_components,
            "unique_components": unique_components,
            "package_types": len(package_types),
            "fine_pitch_count": fine_pitch_count,
            "through_hole_count": through_hole_count,
            "complexity_score": round(complexity_score, 1),
            "complexity_level": complexity_level
        }
    
    def _analyze_test_points(self, bom_items: List[Dict[str, Any]], 
                            connections: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze test point coverage."""
        # Count power rails
        power_rails = set()
        for item in bom_items:
            part = item.get("part_data", {})
            supply_range = part.get("supply_voltage_range", {})
            if isinstance(supply_range, dict):
                voltage = supply_range.get("nominal") or supply_range.get("max")
                if voltage:
                    power_rails.add(f"{voltage}V")
        
        # Count test points in BOM
        test_point_count = sum(1 for item in bom_items 
                              if "test" in str(item.get("part_data", {}).get("category", "")).lower() or
                                 "test_point" in str(item.get("part_data", {}).get("id", "")).lower())
        
        # Recommended test points: at least one per power rail + GND + a few for signals
        recommended_test_points = len(power_rails) + 1 + 3  # Power rails + GND + 3 signal test points
        
        coverage_percentage = (test_point_count / recommended_test_points * 100) if recommended_test_points > 0 else 0
        coverage_percentage = min(coverage_percentage, 100)
        
        return {
            "test_point_count": test_point_count,
            "recommended_test_points": recommended_test_points,
            "power_rails": list(power_rails),
            "coverage_percentage": round(coverage_percentage, 1),
            "status": "adequate" if coverage_percentage >= 80 else "needs_improvement"
        }
    
    def _get_panelization_recommendations(self, bom_items: List[Dict[str, Any]]) -> List[str]:
        """Get panelization recommendations."""
        recommendations = []
        
        total_components = sum(item.get("quantity", 1) for item in bom_items)
        
        if total_components < 20:
            recommendations.append("Small board - consider panelization for efficient assembly")
        elif total_components > 100:
            recommendations.append("Large board - may benefit from panelization with breakaway tabs")
        
        # Check for edge components
        has_edge_components = any("connector" in str(item.get("part_data", {}).get("category", "")).lower() 
                                 for item in bom_items)
        
        if has_edge_components:
            recommendations.append("Edge connectors detected - ensure adequate clearance for panelization")
        
        if not recommendations:
            recommendations.append("Standard panelization practices apply")
        
        return recommendations

