"""
BOM Insights Agent
Provides comprehensive BOM statistics and analysis
"""

from typing import List, Dict, Any
from collections import defaultdict


class BOMInsightsAgent:
    """Provides detailed BOM statistics and insights."""
    
    def analyze_bom(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze BOM and provide comprehensive insights.
        
        Args:
            bom_items: List of BOM items with part data
        
        Returns:
            Dictionary with BOM insights:
            {
                "component_count": int,
                "component_count_by_category": Dict,
                "cost_breakdown": Dict,
                "lifecycle_status": Dict,
                "availability_status": Dict,
                "package_types": Dict,
                "manufacturers": List,
                "recommendations": List
            }
        """
        component_count = len(bom_items)
        component_count_by_category = defaultdict(int)
        cost_by_category = defaultdict(float)
        lifecycle_status = defaultdict(int)
        availability_status = defaultdict(int)
        package_types = defaultdict(int)
        manufacturers = set()
        total_cost = 0.0
        
        for item in bom_items:
            part = item.get("part_data", {})
            quantity = item.get("quantity", 1)
            
            # Count by category
            category = part.get("category", "unknown")
            component_count_by_category[category] += quantity
            
            # Cost breakdown - safe extraction
            from utils.cost_utils import safe_extract_cost, safe_extract_quantity
            cost_est = part.get("cost_estimate", {})
            unit_cost = safe_extract_cost(cost_est, default=0.0)
            quantity = safe_extract_quantity(quantity, default=1)
            item_cost = unit_cost * quantity
            total_cost += item_cost
            cost_by_category[category] += item_cost
            
            # Lifecycle status
            lifecycle = part.get("lifecycle_status", "unknown")
            lifecycle_status[lifecycle] += quantity
            
            # Availability status
            availability = part.get("availability_status", "unknown")
            availability_status[availability] += quantity
            
            # Package types
            package = part.get("package", "unknown")
            package_types[package] += quantity
            
            # Manufacturers
            manufacturer = part.get("manufacturer", "")
            if manufacturer:
                manufacturers.add(manufacturer)
        
        # Generate recommendations
        recommendations = []
        
        # Check for lifecycle issues
        if lifecycle_status.get("obsolete", 0) > 0:
            recommendations.append(f"Warning: {lifecycle_status['obsolete']} component(s) marked as obsolete - consider alternatives")
        
        if lifecycle_status.get("not_recommended", 0) > 0:
            recommendations.append(f"Warning: {lifecycle_status['not_recommended']} component(s) not recommended for new designs")
        
        # Check availability
        if availability_status.get("out_of_stock", 0) > 0:
            recommendations.append(f"Warning: {availability_status['out_of_stock']} component(s) currently out of stock")
        
        if availability_status.get("limited", 0) > 0:
            recommendations.append(f"Note: {availability_status['limited']} component(s) have limited availability")
        
        # Check for high component count
        if component_count > 50:
            recommendations.append(f"BOM has {component_count} unique components - consider consolidation opportunities")
        
        # Check for high cost items
        high_cost_threshold = total_cost * 0.2  # 20% of total cost
        high_cost_items = []
        for item in bom_items:
            part = item.get("part_data", {})
            quantity = item.get("quantity", 1)
            cost_est = part.get("cost_estimate", {})
            unit_cost = safe_extract_cost(cost_est, default=0.0)
            quantity = safe_extract_quantity(quantity, default=1)
            item_cost = unit_cost * quantity
            if item_cost > high_cost_threshold:
                high_cost_items.append({
                    "part_id": part.get("id"),
                    "name": part.get("name"),
                    "cost": item_cost,
                    "percentage": (item_cost / total_cost * 100) if total_cost > 0 else 0
                })
        
        if high_cost_items:
            top_item = high_cost_items[0]
            recommendations.append(f"Highest cost item: {top_item['name']} ({top_item['percentage']:.1f}% of total) - review for cost optimization")
        
        return {
            "component_count": component_count,
            "total_quantity": sum(item.get("quantity", 1) for item in bom_items),
            "component_count_by_category": dict(component_count_by_category),
            "cost_breakdown": {
                "total_cost": round(total_cost, 2),
                "cost_by_category": {k: round(v, 2) for k, v in cost_by_category.items()},
                "average_cost_per_component": round(total_cost / component_count, 2) if component_count > 0 else 0
            },
            "lifecycle_status": dict(lifecycle_status),
            "availability_status": dict(availability_status),
            "package_types": dict(package_types),
            "manufacturers": sorted(list(manufacturers)),
            "high_cost_items": high_cost_items[:5],  # Top 5
            "recommendations": recommendations
        }

