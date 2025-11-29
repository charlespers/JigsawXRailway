"""
Cost Optimization Agent
Finds cost-saving opportunities without compromising design
"""
import logging
from typing import Dict, List, Any, Optional
from app.agents.alternative_finder import AlternativeFinderAgent
from app.agents.compatibility import CompatibilityAgent

logger = logging.getLogger(__name__)


class CostOptimizerAgent:
    """
    Optimizes design cost by finding cheaper alternatives.
    
    Solves: "Can I reduce cost without compromising functionality?"
    """
    
    def __init__(self):
        self.alternative_finder = AlternativeFinderAgent()
        self.compat_agent = CompatibilityAgent()
    
    def optimize_cost(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        target_savings_percent: float = 20.0,
        preserve_critical: bool = True
    ) -> Dict[str, Any]:
        """
        Find cost optimization opportunities.
        
        Args:
            selected_parts: Current parts selection
            target_savings_percent: Target cost reduction percentage
            preserve_critical: Don't suggest changes to critical parts
        
        Returns:
            Optimization analysis with suggestions and savings
        """
        current_cost = sum(self._extract_cost(p) for p in selected_parts.values())
        target_cost = current_cost * (1 - target_savings_percent / 100)
        
        optimizations = []
        total_savings = 0.0
        
        for part_name, part in selected_parts.items():
            # Skip critical parts if requested
            if preserve_critical and self._is_critical(part):
                continue
            
            # Find cheaper alternatives
            part_id = part.get("id", part_name)
            alternatives = self.alternative_finder.find_alternatives(
                part_id,
                criteria={
                    "lower_cost": True,
                    "same_footprint": True,
                    "better_availability": True
                }
            )
            
            # Find alternatives that are cheaper and compatible
            for alt in alternatives[:3]:  # Top 3 alternatives
                alt_part = alt["part"]
                alt_cost = self._extract_cost(alt_part)
                current_part_cost = self._extract_cost(part)
                
                if alt_cost and current_part_cost and alt_cost < current_part_cost:
                    savings = current_part_cost - alt_cost
                    
                    # Check compatibility
                    compat = self.compat_agent.check_compatibility(part, alt_part)
                    
                    if compat["compatible"]:
                        optimizations.append({
                            "part_name": part_name,
                            "current_part": {
                                "name": part.get("name"),
                                "cost": current_part_cost,
                                "mfr_part_number": part.get("mfr_part_number")
                            },
                            "suggested_part": {
                                "name": alt_part.get("name"),
                                "cost": alt_cost,
                                "mfr_part_number": alt_part.get("mfr_part_number"),
                                "score": alt["score"]
                            },
                            "savings": savings,
                            "savings_percent": (savings / current_part_cost) * 100,
                            "compatibility": compat,
                            "reasons": alt.get("reasons", []),
                            "risk_level": self._assess_risk(part, alt_part, compat)
                        })
                        total_savings += savings
        
        # Sort by savings
        optimizations.sort(key=lambda x: x["savings"], reverse=True)
        
        # Calculate potential total cost
        optimized_cost = current_cost - total_savings
        
        return {
            "current_cost": round(current_cost, 2),
            "optimized_cost": round(optimized_cost, 2),
            "potential_savings": round(total_savings, 2),
            "savings_percent": round((total_savings / current_cost) * 100, 1) if current_cost > 0 else 0,
            "optimizations": optimizations,
            "target_met": optimized_cost <= target_cost,
            "recommendations": self._generate_optimization_recommendations(optimizations)
        }
    
    def _is_critical(self, part: Dict[str, Any]) -> bool:
        """Determine if part is critical (shouldn't be swapped)"""
        category = part.get("category", "").lower()
        # MCUs and main sensors are typically critical
        return "mcu" in category or "anchor" in str(part.get("id", "")).lower()
    
    def _assess_risk(
        self,
        original: Dict[str, Any],
        alternative: Dict[str, Any],
        compat: Dict[str, Any]
    ) -> str:
        """Assess risk level of substitution"""
        if not compat["compatible"]:
            return "high"
        
        if compat["warnings"]:
            return "medium"
        
        # Check if footprint matches
        if original.get("footprint") == alternative.get("footprint"):
            return "low"
        
        return "medium"
    
    def _extract_cost(self, part: Dict[str, Any]) -> float:
        """Extract cost from part"""
        cost = part.get("cost_estimate", {})
        if isinstance(cost, dict):
            value = cost.get("unit") or cost.get("value")
            return float(value) if value else 0.0
        return float(cost) if cost else 0.0
    
    def _generate_optimization_recommendations(
        self,
        optimizations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if not optimizations:
            recommendations.append("No cost optimization opportunities found")
            return recommendations
        
        high_savings = [o for o in optimizations if o["savings_percent"] > 30]
        if high_savings:
            recommendations.append(
                f"💰 {len(high_savings)} part(s) with >30% cost savings available"
            )
        
        low_risk = [o for o in optimizations if o["risk_level"] == "low"]
        if low_risk:
            recommendations.append(
                f"✅ {len(low_risk)} low-risk substitution(s) available - "
                f"${sum(o['savings'] for o in low_risk):.2f} total savings"
            )
        
        return recommendations

