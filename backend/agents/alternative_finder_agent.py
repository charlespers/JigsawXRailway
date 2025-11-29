"""
Alternative Part Finder Agent
Finds drop-in replacements and alternatives for parts
"""

from typing import List, Dict, Any, Optional
from utils.part_database import get_part_by_id, get_all_parts, search_parts


class AlternativeFinderAgent:
    """Finds alternative parts based on compatibility criteria."""
    
    def find_alternatives(
        self,
        part_id: str,
        criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find alternative parts for a given part.
        
        Args:
            part_id: ID of the part to find alternatives for
            criteria: Optional criteria:
                - same_footprint: bool - Require same footprint
                - lower_cost: bool - Prefer lower cost
                - better_availability: bool - Prefer better availability
                - same_voltage: bool - Require same voltage range
        
        Returns:
            List of alternative parts with compatibility scores
        """
        part = get_part_by_id(part_id)
        if not part:
            return []
        
        criteria = criteria or {}
        all_parts = get_all_parts()
        alternatives = []
        
        part_category = part.get("category", "")
        part_footprint = part.get("footprint")
        part_package = part.get("package")
        part_voltage_range = part.get("supply_voltage_range")
        part_cost = part.get("cost_estimate", {})
        if isinstance(part_cost, dict):
            part_cost_value = part_cost.get("value", 0)
        else:
            part_cost_value = part_cost or 0
        
        for candidate in all_parts:
            # Skip the same part
            if candidate.get("id") == part_id:
                continue
            
            # Must be same category or compatible category
            candidate_category = candidate.get("category", "")
            if not self._categories_compatible(part_category, candidate_category):
                continue
            
            score = 0.0
            compatibility_notes = []
            
            # Footprint compatibility
            candidate_footprint = candidate.get("footprint")
            if part_footprint and candidate_footprint:
                if part_footprint == candidate_footprint:
                    score += 30.0
                    compatibility_notes.append("Same footprint")
                elif criteria.get("same_footprint", False):
                    continue  # Skip if footprint required but different
            
            # Package compatibility
            candidate_package = candidate.get("package")
            if part_package and candidate_package:
                if part_package == candidate_package:
                    score += 20.0
                    compatibility_notes.append("Same package")
            
            # Voltage compatibility
            candidate_voltage_range = candidate.get("supply_voltage_range")
            if part_voltage_range and candidate_voltage_range:
                if self._voltage_ranges_compatible(part_voltage_range, candidate_voltage_range):
                    score += 25.0
                    compatibility_notes.append("Compatible voltage range")
                elif criteria.get("same_voltage", False):
                    continue
            
            # Cost comparison
            candidate_cost = candidate.get("cost_estimate", {})
            if isinstance(candidate_cost, dict):
                candidate_cost_value = candidate_cost.get("value", 0)
            else:
                candidate_cost_value = candidate_cost or 0
            
            if candidate_cost_value > 0 and part_cost_value > 0:
                if candidate_cost_value < part_cost_value:
                    score += 15.0
                    compatibility_notes.append(f"Lower cost (${candidate_cost_value:.2f} vs ${part_cost_value:.2f})")
                elif criteria.get("lower_cost", False) and candidate_cost_value >= part_cost_value:
                    continue
            
            # Availability
            candidate_availability = candidate.get("availability_status")
            part_availability = part.get("availability_status")
            
            if candidate_availability == "in_stock" and part_availability != "in_stock":
                score += 10.0
                compatibility_notes.append("Better availability")
            elif criteria.get("better_availability", False) and candidate_availability != "in_stock":
                continue
            
            # Lifecycle status
            candidate_lifecycle = candidate.get("lifecycle_status")
            part_lifecycle = part.get("lifecycle_status")
            
            if candidate_lifecycle == "active" and part_lifecycle != "active":
                score += 10.0
                compatibility_notes.append("Better lifecycle status")
            
            # Only include if score is above threshold
            if score >= 20.0:
                candidate["compatibility_score"] = score
                candidate["compatibility_notes"] = compatibility_notes
                alternatives.append(candidate)
        
        # Sort by compatibility score (descending)
        alternatives.sort(key=lambda x: x.get("compatibility_score", 0), reverse=True)
        
        return alternatives[:10]  # Return top 10
    
    def _categories_compatible(self, cat1: str, cat2: str) -> bool:
        """Check if two categories are compatible."""
        # Same category
        if cat1 == cat2:
            return True
        
        # Both resistors
        if "resistor" in cat1 and "resistor" in cat2:
            return True
        
        # Both capacitors
        if "capacitor" in cat1 and "capacitor" in cat2:
            return True
        
        # Both regulators (LDO, buck, boost)
        if "regulator" in cat1 and "regulator" in cat2:
            return True
        
        # Both connectors
        if "connector" in cat1 and "connector" in cat2:
            return True
        
        return False
    
    def _voltage_ranges_compatible(self, range1: Dict[str, Any], range2: Dict[str, Any]) -> bool:
        """Check if two voltage ranges are compatible."""
        min1 = range1.get("min")
        max1 = range1.get("max")
        min2 = range2.get("min")
        max2 = range2.get("max")
        
        if not all([min1, max1, min2, max2]):
            return False
        
        # Check if ranges overlap
        return not (max1 < min2 or max2 < min1)

