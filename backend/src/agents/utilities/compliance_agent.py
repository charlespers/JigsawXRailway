"""
Compliance Agent
Checks RoHS, REACH, conflict minerals, and environmental compliance
"""

from typing import List, Dict, Any


class ComplianceAgent:
    """Checks design compliance with environmental and regulatory standards."""
    
    def check_compliance(
        self,
        bom_items: List[Dict[str, Any]],
        regions: List[str] = ["EU", "US", "China"]
    ) -> Dict[str, Any]:
        """
        Check compliance with various regulations.
        
        Args:
            bom_items: List of BOM items
            regions: List of regions to check compliance for
        
        Returns:
            Dictionary with compliance status:
            {
                "rohs": Dict,
                "reach": Dict,
                "conflict_minerals": Dict,
                "waste_directive": Dict,
                "overall_compliance": str,
                "non_compliant_parts": List[Dict]
            }
        """
        rohs_status = self._check_rohs(bom_items)
        reach_status = self._check_reach(bom_items)
        conflict_minerals_status = self._check_conflict_minerals(bom_items)
        waste_directive_status = self._check_waste_directive(bom_items)
        
        # Find non-compliant parts
        non_compliant_parts = []
        for item in bom_items:
            part = item.get("part_data", {})
            compliance_issues = []
            
            if not part.get("rohs_compliant", True):
                compliance_issues.append("RoHS")
            if not part.get("reach_compliant", True):
                compliance_issues.append("REACH")
            if not part.get("conflict_mineral_free", True):
                compliance_issues.append("Conflict Minerals")
            
            if compliance_issues:
                non_compliant_parts.append({
                    "part_id": part.get("id"),
                    "name": part.get("name"),
                    "manufacturer": part.get("manufacturer"),
                    "issues": compliance_issues
                })
        
        # Determine overall compliance
        all_compliant = (
            rohs_status.get("compliant", False) and
            reach_status.get("compliant", False) and
            conflict_minerals_status.get("compliant", False)
        )
        
        overall_compliance = "compliant" if all_compliant else "non_compliant"
        
        return {
            "rohs": rohs_status,
            "reach": reach_status,
            "conflict_minerals": conflict_minerals_status,
            "waste_directive": waste_directive_status,
            "overall_compliance": overall_compliance,
            "non_compliant_parts": non_compliant_parts,
            "regions_checked": regions,
            "recommendations": self._generate_compliance_recommendations(
                rohs_status, reach_status, conflict_minerals_status, non_compliant_parts
            )
        }
    
    def _check_rohs(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check RoHS (Restriction of Hazardous Substances) compliance."""
        total_parts = len(bom_items)
        rohs_compliant = 0
        non_rohs_parts = []
        
        for item in bom_items:
            part = item.get("part_data", {})
            rohs_status = part.get("rohs_compliant", True)  # Default to True if not specified
            
            if rohs_status:
                rohs_compliant += 1
            else:
                non_rohs_parts.append({
                    "part_id": part.get("id"),
                    "name": part.get("name")
                })
        
        compliance_percentage = (rohs_compliant / total_parts * 100) if total_parts > 0 else 100
        
        return {
            "compliant": compliance_percentage == 100,
            "compliance_percentage": round(compliance_percentage, 1),
            "compliant_count": rohs_compliant,
            "non_compliant_count": total_parts - rohs_compliant,
            "non_compliant_parts": non_rohs_parts,
            "standard": "RoHS 3 (EU Directive 2015/863)",
            "restricted_substances": ["Lead", "Cadmium", "Mercury", "Hexavalent Chromium", "PBB", "PBDE", "DEHP", "BBP", "DBP", "DIBP"]
        }
    
    def _check_reach(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check REACH (Registration, Evaluation, Authorisation and Restriction of Chemicals) compliance."""
        total_parts = len(bom_items)
        reach_compliant = 0
        non_reach_parts = []
        
        for item in bom_items:
            part = item.get("part_data", {})
            reach_status = part.get("reach_compliant", True)  # Default to True if not specified
            
            if reach_status:
                reach_compliant += 1
            else:
                non_reach_parts.append({
                    "part_id": part.get("id"),
                    "name": part.get("name")
                })
        
        compliance_percentage = (reach_compliant / total_parts * 100) if total_parts > 0 else 100
        
        return {
            "compliant": compliance_percentage == 100,
            "compliance_percentage": round(compliance_percentage, 1),
            "compliant_count": reach_compliant,
            "non_compliant_count": total_parts - reach_compliant,
            "non_compliant_parts": non_reach_parts,
            "standard": "REACH (EC 1907/2006)",
            "note": "REACH requires registration of substances used in quantities >1 ton/year"
        }
    
    def _check_conflict_minerals(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check conflict minerals compliance (Dodd-Frank Act, EU Conflict Minerals Regulation)."""
        total_parts = len(bom_items)
        conflict_free = 0
        potentially_non_compliant = []
        
        # Check for components that might contain conflict minerals
        # Typically: tantalum capacitors, some ICs, connectors
        conflict_mineral_categories = ["capacitor", "ic", "connector"]
        
        for item in bom_items:
            part = item.get("part_data", {})
            category = part.get("category", "").lower()
            
            conflict_mineral_free = part.get("conflict_mineral_free", True)
            
            # If category might contain conflict minerals, check status
            if any(cat in category for cat in conflict_mineral_categories):
                if not conflict_mineral_free:
                    potentially_non_compliant.append({
                        "part_id": part.get("id"),
                        "name": part.get("name"),
                        "category": category
                    })
                else:
                    conflict_free += 1
            else:
                conflict_free += 1
        
        compliance_percentage = (conflict_free / total_parts * 100) if total_parts > 0 else 100
        
        return {
            "compliant": len(potentially_non_compliant) == 0,
            "compliance_percentage": round(compliance_percentage, 1),
            "conflict_free_count": conflict_free,
            "potentially_non_compliant_count": len(potentially_non_compliant),
            "potentially_non_compliant_parts": potentially_non_compliant,
            "standard": "Dodd-Frank Act Section 1502 / EU Conflict Minerals Regulation",
            "minerals_checked": ["Tin", "Tantalum", "Tungsten", "Gold"],
            "note": "Due diligence required for components containing 3TG minerals"
        }
    
    def _check_waste_directive(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check WEEE (Waste Electrical and Electronic Equipment) Directive compliance."""
        # WEEE compliance is typically at the product level, not component level
        # But we can check if components are marked appropriately
        
        return {
            "compliant": True,
            "standard": "WEEE Directive (2012/19/EU)",
            "note": "WEEE compliance is assessed at product level, not component level",
            "recommendation": "Ensure product is marked with crossed-out wheeled bin symbol"
        }
    
    def _generate_compliance_recommendations(
        self,
        rohs_status: Dict[str, Any],
        reach_status: Dict[str, Any],
        conflict_minerals_status: Dict[str, Any],
        non_compliant_parts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []
        
        if not rohs_status.get("compliant", True):
            recommendations.append(f"Replace {rohs_status.get('non_compliant_count', 0)} non-RoHS compliant component(s)")
        
        if not reach_status.get("compliant", True):
            recommendations.append(f"Review {reach_status.get('non_compliant_count', 0)} component(s) for REACH compliance")
        
        if not conflict_minerals_status.get("compliant", True):
            recommendations.append("Perform due diligence on conflict minerals - obtain certificates from suppliers")
        
        if len(non_compliant_parts) > 0:
            recommendations.append("Obtain compliance certificates from component manufacturers")
            recommendations.append("Maintain compliance documentation for regulatory audits")
        
        if not recommendations:
            recommendations.append("Design appears compliant with all checked regulations")
        
        return recommendations

