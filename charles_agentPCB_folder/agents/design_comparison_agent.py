"""
Design Comparison Agent
Compare multiple design versions, A/B testing, change analysis
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict


class DesignComparisonAgent:
    """Compares multiple design versions and analyzes changes."""
    
    def compare_designs(
        self,
        designs: List[Dict[str, Any]],
        baseline_index: int = 0
    ) -> Dict[str, Any]:
        """
        Compare multiple design versions.
        
        Args:
            designs: List of design dictionaries, each containing bom_items and optionally metadata
            baseline_index: Index of baseline design (default 0)
        
        Returns:
            Dictionary with comparison results:
            {
                "baseline": Dict,
                "comparisons": List[Dict],
                "summary": Dict,
                "recommendations": List[str]
            }
        """
        if len(designs) < 2:
            return {"error": "Need at least 2 designs to compare"}
        
        baseline = designs[baseline_index]
        baseline_bom = baseline.get("bom_items", [])
        baseline_metadata = baseline.get("metadata", {})
        
        comparisons = []
        
        for i, design in enumerate(designs):
            if i == baseline_index:
                continue
            
            comparison = self._compare_two_designs(
                baseline_bom,
                design.get("bom_items", []),
                baseline_metadata,
                design.get("metadata", {}),
                f"Design {i+1}"
            )
            comparisons.append(comparison)
        
        # Generate summary
        summary = self._generate_summary(comparisons)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(comparisons, summary)
        
        return {
            "baseline": {
                "index": baseline_index,
                "metadata": baseline_metadata,
                "component_count": len(baseline_bom),
                "total_cost": self._calculate_total_cost(baseline_bom)
            },
            "comparisons": comparisons,
            "summary": summary,
            "recommendations": recommendations
        }
    
    def _compare_two_designs(
        self,
        baseline_bom: List[Dict[str, Any]],
        comparison_bom: List[Dict[str, Any]],
        baseline_metadata: Dict[str, Any],
        comparison_metadata: Dict[str, Any],
        comparison_name: str
    ) -> Dict[str, Any]:
        """Compare two designs."""
        baseline_parts = {item.get("part_data", {}).get("id"): item for item in baseline_bom}
        comparison_parts = {item.get("part_data", {}).get("id"): item for item in comparison_bom}
        
        # Find added, removed, and changed parts
        added_parts = []
        removed_parts = []
        changed_parts = []
        unchanged_parts = []
        
        for part_id, item in comparison_parts.items():
            if part_id not in baseline_parts:
                added_parts.append({
                    "part_id": part_id,
                    "name": item.get("part_data", {}).get("name"),
                    "quantity": item.get("quantity", 1)
                })
            else:
                baseline_item = baseline_parts[part_id]
                baseline_qty = baseline_item.get("quantity", 1)
                comparison_qty = item.get("quantity", 1)
                
                if baseline_qty != comparison_qty:
                    changed_parts.append({
                        "part_id": part_id,
                        "name": item.get("part_data", {}).get("name"),
                        "baseline_quantity": baseline_qty,
                        "comparison_quantity": comparison_qty,
                        "change": comparison_qty - baseline_qty
                    })
                else:
                    unchanged_parts.append(part_id)
        
        for part_id, item in baseline_parts.items():
            if part_id not in comparison_parts:
                removed_parts.append({
                    "part_id": part_id,
                    "name": item.get("part_data", {}).get("name"),
                    "quantity": item.get("quantity", 1)
                })
        
        # Calculate cost differences
        baseline_cost = self._calculate_total_cost(baseline_bom)
        comparison_cost = self._calculate_total_cost(comparison_bom)
        cost_difference = comparison_cost - baseline_cost
        cost_change_percentage = (cost_difference / baseline_cost * 100) if baseline_cost > 0 else 0
        
        # Calculate component count differences
        baseline_count = len(baseline_bom)
        comparison_count = len(comparison_bom)
        count_difference = comparison_count - baseline_count
        
        return {
            "comparison_name": comparison_name,
            "metadata": comparison_metadata,
            "component_changes": {
                "added": added_parts,
                "removed": removed_parts,
                "changed": changed_parts,
                "unchanged_count": len(unchanged_parts)
            },
            "cost_analysis": {
                "baseline_cost": round(baseline_cost, 2),
                "comparison_cost": round(comparison_cost, 2),
                "cost_difference": round(cost_difference, 2),
                "cost_change_percentage": round(cost_change_percentage, 1),
                "cost_improvement": cost_difference < 0
            },
            "component_count": {
                "baseline": baseline_count,
                "comparison": comparison_count,
                "difference": count_difference
            },
            "change_summary": {
                "total_changes": len(added_parts) + len(removed_parts) + len(changed_parts),
                "added_count": len(added_parts),
                "removed_count": len(removed_parts),
                "changed_count": len(changed_parts)
            }
        }
    
    def _calculate_total_cost(self, bom_items: List[Dict[str, Any]]) -> float:
        """Calculate total cost of BOM."""
        total = 0.0
        for item in bom_items:
            part = item.get("part_data", {})
            quantity = item.get("quantity", 1)
            cost_est = part.get("cost_estimate", {})
            
            if isinstance(cost_est, dict):
                unit_cost = cost_est.get("value", 0)
                if isinstance(unit_cost, dict):
                    unit_cost = unit_cost.get("value", 0)
                unit_cost = float(unit_cost) if unit_cost else 0.0
            else:
                unit_cost = float(cost_est) if cost_est else 0.0
            
            total += unit_cost * quantity
        return total
    
    def _generate_summary(self, comparisons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comparison summary."""
        total_comparisons = len(comparisons)
        cost_improvements = sum(1 for c in comparisons if c.get("cost_analysis", {}).get("cost_improvement", False))
        avg_cost_change = sum(c.get("cost_analysis", {}).get("cost_change_percentage", 0) for c in comparisons) / total_comparisons if total_comparisons > 0 else 0
        
        return {
            "total_comparisons": total_comparisons,
            "cost_improvements": cost_improvements,
            "average_cost_change_percentage": round(avg_cost_change, 1),
            "best_cost_reduction": min((c.get("cost_analysis", {}).get("cost_change_percentage", 0) for c in comparisons), default=0)
        }
    
    def _generate_recommendations(
        self,
        comparisons: List[Dict[str, Any]],
        summary: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on comparisons."""
        recommendations = []
        
        # Find best cost reduction
        best_comparison = min(comparisons, 
                             key=lambda c: c.get("cost_analysis", {}).get("cost_change_percentage", 0),
                             default=None)
        
        if best_comparison and best_comparison.get("cost_analysis", {}).get("cost_improvement", False):
            cost_reduction = abs(best_comparison.get("cost_analysis", {}).get("cost_change_percentage", 0))
            recommendations.append(f"Best cost reduction: {best_comparison['comparison_name']} reduces cost by {cost_reduction:.1f}%")
        
        # Check for significant changes
        for comparison in comparisons:
            change_count = comparison.get("change_summary", {}).get("total_changes", 0)
            if change_count > 10:
                recommendations.append(f"{comparison['comparison_name']} has {change_count} changes - review carefully")
        
        if not recommendations:
            recommendations.append("All design variants are similar - consider consolidating")
        
        return recommendations

