"""
Cost Forecast Agent
Cost forecasting, budget planning, and price trend analysis
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class CostForecastAgent:
    """Forecasts costs and analyzes price trends."""
    
    def forecast_costs(
        self,
        bom_items: List[Dict[str, Any]],
        forecast_months: int = 12,
        production_volume: int = 1000
    ) -> Dict[str, Any]:
        """
        Forecast BOM costs over time.
        
        Args:
            bom_items: List of BOM items
            forecast_months: Number of months to forecast (default 12)
            production_volume: Expected production volume (default 1000)
        
        Returns:
            Dictionary with cost forecast:
            {
                "current_cost": float,
                "forecasted_costs": List[Dict],
                "price_trends": Dict,
                "budget_recommendations": List[str]
            }
        """
        current_cost = self._calculate_total_cost(bom_items)
        
        # Forecast costs by month
        forecasted_costs = []
        for month in range(1, forecast_months + 1):
            month_cost = self._forecast_month_cost(bom_items, month)
            forecasted_costs.append({
                "month": month,
                "date": (datetime.now() + timedelta(days=month * 30)).isoformat(),
                "unit_cost": round(month_cost, 2),
                "total_cost_1000_units": round(month_cost * production_volume, 2),
                "cost_change_percentage": round((month_cost - current_cost) / current_cost * 100, 1) if current_cost > 0 else 0
            })
        
        # Analyze price trends
        price_trends = self._analyze_price_trends(bom_items)
        
        # Generate budget recommendations
        budget_recommendations = self._generate_budget_recommendations(
            current_cost, forecasted_costs, production_volume
        )
        
        return {
            "current_cost": round(current_cost, 2),
            "forecasted_costs": forecasted_costs,
            "forecast_summary": {
                "average_forecasted_cost": round(sum(f["unit_cost"] for f in forecasted_costs) / len(forecasted_costs), 2),
                "min_forecasted_cost": round(min(f["unit_cost"] for f in forecasted_costs), 2),
                "max_forecasted_cost": round(max(f["unit_cost"] for f in forecasted_costs), 2),
                "cost_volatility": round(max(f["unit_cost"] for f in forecasted_costs) - min(f["unit_cost"] for f in forecasted_costs), 2)
            },
            "price_trends": price_trends,
            "budget_recommendations": budget_recommendations,
            "production_volume": production_volume,
            "forecast_period_months": forecast_months
        }
    
    def _calculate_total_cost(self, bom_items: List[Dict[str, Any]]) -> float:
        """Calculate total cost of BOM."""
        total = 0.0
        from utils.cost_utils import safe_extract_cost, safe_extract_quantity
        
        for item in bom_items:
            part = item.get("part_data", {})
            quantity = safe_extract_quantity(item.get("quantity", 1), default=1)
            cost_est = part.get("cost_estimate", {})
            unit_cost = safe_extract_cost(cost_est, default=0.0)
            total += unit_cost * quantity
        return total
    
    def _forecast_month_cost(self, bom_items: List[Dict[str, Any]], month: int) -> float:
        """Forecast cost for a specific month."""
        total = 0.0
        
        from utils.cost_utils import safe_extract_cost, safe_extract_quantity
        
        for item in bom_items:
            part = item.get("part_data", {})
            quantity = safe_extract_quantity(item.get("quantity", 1), default=1)
            cost_est = part.get("cost_estimate", {})
            unit_cost = safe_extract_cost(cost_est, default=0.0)
            
            # Apply price trend (simplified model)
            # Assume 0.5% monthly increase for components with supply chain risks
            lifecycle_status = part.get("lifecycle_status", "active")
            availability_status = part.get("availability_status", "in_stock")
            
            price_multiplier = 1.0
            if lifecycle_status in ["obsolete", "end_of_life"]:
                price_multiplier = 1.0 + (month * 0.02)  # 2% per month increase
            elif availability_status == "limited":
                price_multiplier = 1.0 + (month * 0.005)  # 0.5% per month increase
            
            total += unit_cost * quantity * price_multiplier
        
        return total
    
    def _analyze_price_trends(self, bom_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze price trends for components."""
        increasing_trend = []
        stable_trend = []
        decreasing_trend = []
        
        for item in bom_items:
            part = item.get("part_data", {})
            lifecycle_status = part.get("lifecycle_status", "active")
            availability_status = part.get("availability_status", "in_stock")
            
            trend = "stable"
            if lifecycle_status in ["obsolete", "end_of_life", "last_time_buy"]:
                trend = "increasing"
                increasing_trend.append({
                    "part_id": part.get("id"),
                    "name": part.get("name"),
                    "reason": f"Lifecycle status: {lifecycle_status}"
                })
            elif availability_status == "limited":
                trend = "increasing"
                increasing_trend.append({
                    "part_id": part.get("id"),
                    "name": part.get("name"),
                    "reason": "Limited availability"
                })
            else:
                stable_trend.append(part.get("id"))
        
        return {
            "increasing_trend_count": len(increasing_trend),
            "stable_trend_count": len(stable_trend),
            "decreasing_trend_count": len(decreasing_trend),
            "increasing_trend_parts": increasing_trend[:10],  # Top 10
            "trend_summary": f"{len(increasing_trend)} component(s) showing price increase risk"
        }
    
    def _generate_budget_recommendations(
        self,
        current_cost: float,
        forecasted_costs: List[Dict[str, Any]],
        production_volume: int
    ) -> List[str]:
        """Generate budget recommendations."""
        recommendations = []
        
        avg_forecasted = sum(f["unit_cost"] for f in forecasted_costs) / len(forecasted_costs)
        max_forecasted = max(f["unit_cost"] for f in forecasted_costs)
        
        if max_forecasted > current_cost * 1.1:
            recommendations.append(f"Cost may increase up to {((max_forecasted - current_cost) / current_cost * 100):.1f}% - budget accordingly")
        
        total_cost_1000 = avg_forecasted * production_volume
        recommendations.append(f"Budget recommendation for {production_volume} units: ${total_cost_1000:.2f} (based on average forecast)")
        
        cost_volatility = max(f["unit_cost"] for f in forecasted_costs) - min(f["unit_cost"] for f in forecasted_costs)
        if cost_volatility > current_cost * 0.05:
            recommendations.append("High cost volatility detected - consider forward purchasing or alternative components")
        
        return recommendations

