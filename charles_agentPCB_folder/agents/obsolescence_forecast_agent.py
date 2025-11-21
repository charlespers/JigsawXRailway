"""
Obsolescence Forecast Agent
Component lifecycle forecasting and obsolescence risk analysis
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta


class ObsolescenceForecastAgent:
    """Forecasts component obsolescence and analyzes lifecycle risks."""
    
    def forecast_obsolescence(
        self,
        bom_items: List[Dict[str, Any]],
        forecast_years: int = 5
    ) -> Dict[str, Any]:
        """
        Forecast component obsolescence risks.
        
        Args:
            bom_items: List of BOM items
            forecast_years: Number of years to forecast (default 5)
        
        Returns:
            Dictionary with obsolescence forecast:
            {
                "obsolescence_risks": List[Dict],
                "lifecycle_summary": Dict,
                "recommendations": List[str],
                "forecast_period_years": int
            }
        """
        obsolescence_risks = []
        lifecycle_summary = defaultdict(int)
        
        forecast_date = datetime.now() + timedelta(days=forecast_years * 365)
        
        for item in bom_items:
            part = item.get("part_data", {})
            lifecycle_status = part.get("lifecycle_status", "active")
            part_id = part.get("id")
            manufacturer = part.get("manufacturer", "")
            
            lifecycle_summary[lifecycle_status] += item.get("quantity", 1)
            
            # Assess obsolescence risk
            risk_level = self._assess_obsolescence_risk(lifecycle_status, part)
            
            if risk_level != "low":
                obsolescence_risks.append({
                    "part_id": part_id,
                    "name": part.get("name"),
                    "manufacturer": manufacturer,
                    "lifecycle_status": lifecycle_status,
                    "risk_level": risk_level,
                    "estimated_obsolescence_date": self._estimate_obsolescence_date(lifecycle_status),
                    "recommendation": self._get_obsolescence_recommendation(lifecycle_status, risk_level),
                    "quantity": item.get("quantity", 1)
                })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(obsolescence_risks, lifecycle_summary)
        
        return {
            "obsolescence_risks": obsolescence_risks,
            "lifecycle_summary": dict(lifecycle_summary),
            "risk_summary": {
                "high_risk_count": sum(1 for r in obsolescence_risks if r.get("risk_level") == "high"),
                "medium_risk_count": sum(1 for r in obsolescence_risks if r.get("risk_level") == "medium"),
                "low_risk_count": len(bom_items) - len(obsolescence_risks)
            },
            "recommendations": recommendations,
            "forecast_period_years": forecast_years,
            "forecast_date": forecast_date.isoformat()
        }
    
    def _assess_obsolescence_risk(self, lifecycle_status: str, part: Dict[str, Any]) -> str:
        """Assess obsolescence risk level."""
        lifecycle_status_lower = lifecycle_status.lower()
        
        if lifecycle_status_lower in ["obsolete", "end_of_life", "not_recommended"]:
            return "high"
        elif lifecycle_status_lower in ["last_time_buy", "not_for_new_designs"]:
            return "medium"
        elif lifecycle_status_lower == "active":
            # Check if part is old (based on availability or other indicators)
            availability = part.get("availability_status", "in_stock")
            if availability == "limited":
                return "medium"
            return "low"
        else:
            return "medium"
    
    def _estimate_obsolescence_date(self, lifecycle_status: str) -> Optional[str]:
        """Estimate obsolescence date based on lifecycle status."""
        lifecycle_status_lower = lifecycle_status.lower()
        
        if lifecycle_status_lower == "obsolete":
            return "Already obsolete"
        elif lifecycle_status_lower == "end_of_life":
            return (datetime.now() + timedelta(days=180)).isoformat()  # ~6 months
        elif lifecycle_status_lower == "last_time_buy":
            return (datetime.now() + timedelta(days=365)).isoformat()  # ~1 year
        elif lifecycle_status_lower == "not_for_new_designs":
            return (datetime.now() + timedelta(days=730)).isoformat()  # ~2 years
        else:
            return None
    
    def _get_obsolescence_recommendation(self, lifecycle_status: str, risk_level: str) -> str:
        """Get recommendation for obsolescence risk."""
        if risk_level == "high":
            return "URGENT: Find alternative component immediately"
        elif risk_level == "medium":
            return "Plan for component replacement within forecast period"
        else:
            return "Component appears stable for forecast period"
    
    def _generate_recommendations(
        self,
        obsolescence_risks: List[Dict[str, Any]],
        lifecycle_summary: Dict[str, int]
    ) -> List[str]:
        """Generate obsolescence recommendations."""
        recommendations = []
        
        high_risk_count = sum(1 for r in obsolescence_risks if r.get("risk_level") == "high")
        medium_risk_count = sum(1 for r in obsolescence_risks if r.get("risk_level") == "medium")
        
        if high_risk_count > 0:
            recommendations.append(f"URGENT: {high_risk_count} component(s) at high obsolescence risk - immediate action required")
        
        if medium_risk_count > 0:
            recommendations.append(f"{medium_risk_count} component(s) at medium obsolescence risk - plan for replacement")
        
        obsolete_count = lifecycle_summary.get("obsolete", 0)
        if obsolete_count > 0:
            recommendations.append(f"{obsolete_count} component(s) already obsolete - must be replaced")
        
        if not recommendations:
            recommendations.append("All components appear stable for the forecast period")
        
        recommendations.append("Maintain alternative component list for high-risk parts")
        recommendations.append("Consider multi-sourcing for critical components")
        
        return recommendations

