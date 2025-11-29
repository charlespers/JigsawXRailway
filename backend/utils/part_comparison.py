"""
Part Comparison Utilities
Compare multiple parts side-by-side
"""

from typing import List, Dict, Any, Optional
from utils.part_database import get_part_by_id, get_all_parts


def compare_parts(part_ids: List[str]) -> Dict[str, Any]:
    """
    Compare multiple parts side-by-side.
    
    Args:
        part_ids: List of part IDs to compare
    
    Returns:
        Dictionary with comparison data:
        {
            "parts": List[Dict],  # Part data
            "comparison": {
                "specs": Dict,  # Spec-by-spec comparison
                "differences": List[str],  # Key differences
                "recommendations": List[str]  # Recommendations
            }
        }
    """
    parts = []
    for part_id in part_ids:
        part = get_part_by_id(part_id)
        if part:
            parts.append(part)
    
    if len(parts) < 2:
        return {
            "parts": parts,
            "comparison": {
                "specs": {},
                "differences": [],
                "recommendations": ["Need at least 2 parts to compare"]
            }
        }
    
    # Extract key specs for comparison
    comparison_specs = {}
    differences = []
    
    # Compare common fields
    fields_to_compare = [
        "supply_voltage_range",
        "current_max",
        "power_rating",
        "operating_temp_range",
        "cost_estimate",
        "package",
        "footprint",
        "availability_status",
        "lifecycle_status"
    ]
    
    for field in fields_to_compare:
        values = []
        for part in parts:
            value = part.get(field)
            values.append(value)
        
        comparison_specs[field] = values
        
        # Check for differences
        if len(set(str(v) for v in values)) > 1:
            differences.append(f"{field}: Different values across parts")
    
    # Category-specific comparisons
    categories = set(p.get("category", "") for p in parts)
    if len(categories) == 1:
        category = categories.pop()
        
        # Resistor-specific
        if "resistor" in category:
            resistances = []
            for part in parts:
                res = part.get("resistance", {})
                if isinstance(res, dict):
                    resistances.append(res.get("value"))
                else:
                    resistances.append(res)
            comparison_specs["resistance"] = resistances
        
        # Capacitor-specific
        elif "capacitor" in category:
            capacitances = []
            for part in parts:
                cap = part.get("capacitance", {})
                if isinstance(cap, dict):
                    capacitances.append(cap.get("value"))
                else:
                    capacitances.append(cap)
            comparison_specs["capacitance"] = capacitances
        
        # Regulator-specific
        elif "regulator" in category:
            output_voltages = []
            efficiencies = []
            for part in parts:
                out_v = part.get("output_voltage", {})
                if isinstance(out_v, dict):
                    output_voltages.append(out_v.get("value"))
                else:
                    output_voltages.append(out_v)
                
                eff = part.get("efficiency", {})
                if isinstance(eff, dict):
                    efficiencies.append(eff.get("typical"))
                else:
                    efficiencies.append(eff)
            comparison_specs["output_voltage"] = output_voltages
            comparison_specs["efficiency"] = efficiencies
    
    # Generate recommendations
    recommendations = []
    
    # Cost comparison
    costs = []
    for part in parts:
        cost = part.get("cost_estimate", {})
        if isinstance(cost, dict):
            costs.append(cost.get("value", 0))
        else:
            costs.append(0)
    
    if costs:
        min_cost_idx = costs.index(min(c for c in costs if c > 0))
        max_cost_idx = costs.index(max(costs))
        if min_cost_idx != max_cost_idx:
            recommendations.append(
                f"Lowest cost: {parts[min_cost_idx].get('name')} "
                f"(${costs[min_cost_idx]:.2f})"
            )
    
    # Availability comparison
    availabilities = [p.get("availability_status") for p in parts]
    if "out_of_stock" in availabilities:
        recommendations.append("Some parts are out of stock - consider alternatives")
    
    # Lifecycle comparison
    lifecycles = [p.get("lifecycle_status") for p in parts]
    if "obsolete" in lifecycles or "not_recommended" in lifecycles:
        recommendations.append("Some parts are obsolete or not recommended for new designs")
    
    return {
        "parts": parts,
        "comparison": {
            "specs": comparison_specs,
            "differences": differences,
            "recommendations": recommendations
        }
    }

