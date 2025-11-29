"""
Alternative part finder agent
Finds drop-in replacements and alternatives - solves availability and cost optimization pain points
"""
import logging
from typing import Dict, List, Any, Optional
from app.domain.part_database import get_part_database
from app.domain.models import ComponentCategory
from app.agents.compatibility import CompatibilityAgent

logger = logging.getLogger(__name__)


class AlternativeFinderAgent:
    """
    Finds alternative parts and drop-in replacements.
    Solves: "This part is obsolete/expensive/unavailable, what are my options?"
    """
    
    def __init__(self):
        self.db = get_part_database()
        self.compatibility_agent = CompatibilityAgent()
    
    def find_alternatives(
        self,
        part_id: str,
        criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find alternative parts for a given part
        
        Args:
            part_id: ID of the part to find alternatives for
            criteria: Optional criteria:
                - same_footprint: Require same footprint
                - lower_cost: Prefer lower cost
                - better_availability: Prefer better availability
                - same_voltage: Require same voltage range
                - same_interface: Require same interfaces
        
        Returns:
            List of alternative parts with compatibility scores
        """
        original_part = self.db.get_part(part_id)
        if not original_part:
            return []
        
        criteria = criteria or {}
        category_str = original_part.get("category", "")
        category = None
        if category_str:
            try:
                category = ComponentCategory(category_str)
            except ValueError:
                # Try to match by value
                for cat in ComponentCategory:
                    if cat.value.lower() == category_str.lower():
                        category = cat
                        break
        
        # Search for parts in same category
        candidates = self.db.search_parts(category=category) if category else self.db.get_all_parts()
        
        alternatives = []
        for candidate in candidates:
            if candidate.get("id") == part_id:
                continue  # Skip original part
            
            # Check compatibility
            compat = self.compatibility_agent.check_compatibility(original_part, candidate)
            
            if not compat["compatible"] and criteria.get("strict_compatibility"):
                continue
            
            # Calculate alternative score
            score = self._calculate_alternative_score(
                original_part,
                candidate,
                criteria,
                compat
            )
            
            alternatives.append({
                "part": candidate,
                "compatibility": compat,
                "score": score,
                "reasons": self._get_alternative_reasons(original_part, candidate, criteria)
            })
        
        # Sort by score
        alternatives.sort(key=lambda x: x["score"], reverse=True)
        
        return alternatives[:10]  # Top 10 alternatives
    
    def _calculate_alternative_score(
        self,
        original: Dict[str, Any],
        candidate: Dict[str, Any],
        criteria: Dict[str, Any],
        compat: Dict[str, Any]
    ) -> float:
        """Calculate how good an alternative is (0-100)"""
        score = 50.0  # Base score
        
        # Footprint match
        if criteria.get("same_footprint"):
            if original.get("footprint") == candidate.get("footprint"):
                score += 30
            else:
                score -= 20
        
        # Cost comparison
        if criteria.get("lower_cost"):
            orig_cost = self._extract_cost(original)
            cand_cost = self._extract_cost(candidate)
            if orig_cost and cand_cost:
                if cand_cost < orig_cost:
                    score += 20
                    if cand_cost < orig_cost * 0.8:
                        score += 10  # Significant savings
                else:
                    score -= 10
        
        # Availability
        if criteria.get("better_availability"):
            orig_avail = original.get("availability_status", "unknown")
            cand_avail = candidate.get("availability_status", "unknown")
            
            if cand_avail == "in_stock" and orig_avail != "in_stock":
                score += 25
            elif cand_avail == "in_stock":
                score += 10
        
        # Lifecycle status
        orig_lifecycle = original.get("lifecycle_status", "unknown")
        cand_lifecycle = candidate.get("lifecycle_status", "unknown")
        
        if cand_lifecycle == "active" and orig_lifecycle != "active":
            score += 15
        elif cand_lifecycle == "active":
            score += 5
        
        # Voltage match
        if criteria.get("same_voltage"):
            orig_v = self._extract_voltage_range(original)
            cand_v = self._extract_voltage_range(candidate)
            if orig_v and cand_v and orig_v == cand_v:
                score += 15
        
        # Interface match
        if criteria.get("same_interface"):
            orig_ifaces = original.get("interface_type", [])
            cand_ifaces = candidate.get("interface_type", [])
            if isinstance(orig_ifaces, str):
                orig_ifaces = [orig_ifaces]
            if isinstance(cand_ifaces, str):
                cand_ifaces = [cand_ifaces]
            
            if set(orig_ifaces) == set(cand_ifaces):
                score += 15
        
        # Compatibility bonus
        if compat["compatible"]:
            score += 10
        
        return max(0, min(100, score))
    
    def _extract_cost(self, part: Dict[str, Any]) -> Optional[float]:
        """Extract cost from part"""
        cost = part.get("cost_estimate", {})
        if isinstance(cost, dict):
            return cost.get("unit") or cost.get("value")
        elif isinstance(cost, (int, float)):
            return float(cost)
        return None
    
    def _extract_voltage_range(self, part: Dict[str, Any]) -> Optional[tuple]:
        """Extract voltage range"""
        supply = part.get("supply_voltage_range", {})
        if isinstance(supply, dict):
            min_v = supply.get("min")
            max_v = supply.get("max")
            if min_v is not None and max_v is not None:
                return (min_v, max_v)
        return None
    
    def _get_alternative_reasons(
        self,
        original: Dict[str, Any],
        candidate: Dict[str, Any],
        criteria: Dict[str, Any]
    ) -> List[str]:
        """Get reasons why this is a good alternative"""
        reasons = []
        
        # Cost savings
        orig_cost = self._extract_cost(original)
        cand_cost = self._extract_cost(candidate)
        if orig_cost and cand_cost and cand_cost < orig_cost:
            savings_pct = ((orig_cost - cand_cost) / orig_cost) * 100
            reasons.append(f"{savings_pct:.1f}% cost savings")
        
        # Better availability
        if candidate.get("availability_status") == "in_stock" and original.get("availability_status") != "in_stock":
            reasons.append("Better availability")
        
        # Active lifecycle
        if candidate.get("lifecycle_status") == "active" and original.get("lifecycle_status") != "active":
            reasons.append("Active lifecycle status")
        
        # Same footprint
        if original.get("footprint") == candidate.get("footprint"):
            reasons.append("Drop-in replacement (same footprint)")
        
        return reasons

