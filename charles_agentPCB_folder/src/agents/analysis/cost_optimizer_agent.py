"""
Cost Optimizer Agent
Analyzes BOM costs and suggests optimizations
"""

from typing import List, Dict, Any, Optional
from agents.alternative_finder_agent import AlternativeFinderAgent


class CostOptimizerAgent:
    """Analyzes BOM costs and suggests cost reduction opportunities."""
    
    def __init__(self):
        self.alternative_finder = AlternativeFinderAgent()
    
    def analyze_bom_cost(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze BOM cost and identify optimization opportunities.
        
        Args:
            bom_items: List of BOM items with part data
        
        Returns:
            Dictionary with cost analysis:
            {
                "total_cost": float,
                "cost_by_category": Dict,
                "high_cost_items": List,
                "optimization_opportunities": List
            }
        """
        total_cost = 0.0
        cost_by_category = {}
        high_cost_items = []
        
        for item in bom_items:
            quantity = item.get("quantity", 1)
            part = item.get("part_data", {})
            
            # Use safe cost extraction utility
            from utils.cost_utils import safe_extract_cost, safe_extract_quantity
            
            cost_est = part.get("cost_estimate", {})
            unit_cost = safe_extract_cost(cost_est, default=0.0)
            quantity = safe_extract_quantity(quantity, default=1)
            item_cost = unit_cost * quantity
            total_cost += item_cost
            
            category = part.get("category", "unknown")
            if category not in cost_by_category:
                cost_by_category[category] = 0.0
            cost_by_category[category] += item_cost
            
            # Flag high-cost items (>$1 per unit)
            if unit_cost > 1.0:
                high_cost_items.append({
                    "part_id": part.get("id"),
                    "name": part.get("name"),
                    "unit_cost": unit_cost,
                    "quantity": quantity,
                    "total_cost": item_cost
                })
        
        # Find optimization opportunities
        optimization_opportunities = []
        
        for item in bom_items:
            part = item.get("part_data", {})
            part_id = part.get("id")
            
            if not part_id:
                continue
            
            # Find lower-cost alternatives
            alternatives = self.alternative_finder.find_alternatives(
                part_id,
                criteria={"lower_cost": True, "same_footprint": True}
            )
            
            if alternatives:
                best_alt = alternatives[0]
                alt_cost = best_alt.get("cost_estimate", {})
                alt_cost_value = safe_extract_cost(alt_cost, default=0.0)
                
                current_cost = part.get("cost_estimate", {})
                current_cost_value = safe_extract_cost(current_cost, default=0.0)
                
                item_quantity = safe_extract_quantity(item.get("quantity", 1), default=1)
                if alt_cost_value > 0 and current_cost_value > alt_cost_value:
                    savings = (current_cost_value - alt_cost_value) * item_quantity
                    optimization_opportunities.append({
                        "part_id": part_id,
                        "part_name": part.get("name"),
                        "current_cost": current_cost_value,
                        "alternative": {
                            "id": best_alt.get("id"),
                            "name": best_alt.get("name"),
                            "cost": alt_cost_value
                        },
                        "savings_per_unit": current_cost_value - alt_cost_value,
                        "total_savings": savings
                    })
        
        # Sort opportunities by total savings
        optimization_opportunities.sort(key=lambda x: x.get("total_savings", 0), reverse=True)
        
        return {
            "total_cost": total_cost,
            "cost_by_category": cost_by_category,
            "high_cost_items": high_cost_items,
            "optimization_opportunities": optimization_opportunities[:10]  # Top 10
        }

