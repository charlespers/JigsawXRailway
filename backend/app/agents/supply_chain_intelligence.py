"""
Supply Chain Intelligence Agent
Warns about availability, lead times, obsolescence risks
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SupplyChainIntelligenceAgent:
    """
    Provides supply chain intelligence and risk assessment.
    
    Solves: "Will these parts be available? Are there obsolescence risks?"
    """
    
    def analyze_supply_chain(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        bom: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze supply chain risks for selected parts.
        
        Returns availability status, lead times, obsolescence risks, recommendations.
        """
        analysis = {
            "overall_risk": "low",
            "availability_summary": {},
            "lead_time_summary": {},
            "obsolescence_risks": [],
            "supply_chain_warnings": [],
            "recommendations": [],
            "part_details": []
        }
        
        in_stock_count = 0
        out_of_stock_count = 0
        obsolete_count = 0
        long_lead_time_count = 0
        
        for part_name, part in selected_parts.items():
            part_analysis = self._analyze_part_supply_chain(part)
            analysis["part_details"].append({
                "part_name": part_name,
                **part_analysis
            })
            
            # Aggregate statistics
            if part_analysis["availability_status"] == "in_stock":
                in_stock_count += 1
            elif part_analysis["availability_status"] == "out_of_stock":
                out_of_stock_count += 1
            
            if part_analysis["lifecycle_status"] == "obsolete":
                obsolete_count += 1
                analysis["obsolescence_risks"].append({
                    "part": part_name,
                    "risk": "high",
                    "reason": "Part is obsolete",
                    "recommendation": "Find alternative immediately"
                })
            
            if part_analysis.get("lead_time_days", 0) > 30:
                long_lead_time_count += 1
                analysis["supply_chain_warnings"].append(
                    f"{part_name}: Long lead time ({part_analysis['lead_time_days']} days)"
                )
        
        # Overall risk assessment
        total_parts = len(selected_parts)
        if obsolete_count > 0:
            analysis["overall_risk"] = "critical"
        elif out_of_stock_count > total_parts * 0.3:
            analysis["overall_risk"] = "high"
        elif long_lead_time_count > total_parts * 0.5:
            analysis["overall_risk"] = "medium"
        
        analysis["availability_summary"] = {
            "in_stock": in_stock_count,
            "out_of_stock": out_of_stock_count,
            "obsolete": obsolete_count,
            "total": total_parts,
            "availability_percent": (in_stock_count / total_parts * 100) if total_parts > 0 else 0
        }
        
        # Generate recommendations
        if obsolete_count > 0:
            analysis["recommendations"].append(
                f"🚨 CRITICAL: {obsolete_count} obsolete part(s) detected - "
                "Find alternatives immediately"
            )
        
        if out_of_stock_count > 0:
            analysis["recommendations"].append(
                f"⚠️ {out_of_stock_count} part(s) out of stock - "
                "Consider alternatives or plan for lead time"
            )
        
        if long_lead_time_count > 0:
            analysis["recommendations"].append(
                f"📅 {long_lead_time_count} part(s) with long lead times - "
                "Plan procurement early"
            )
        
        if analysis["overall_risk"] == "low":
            analysis["recommendations"].append("✅ Supply chain looks healthy")
        
        return analysis
    
    def _analyze_part_supply_chain(self, part: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze supply chain for a single part"""
        availability = part.get("availability_status", "unknown")
        lifecycle = part.get("lifecycle_status", "unknown")
        lead_time = part.get("lead_time_days", 0)
        
        # Risk assessment
        risk_factors = []
        risk_level = "low"
        
        if lifecycle == "obsolete":
            risk_factors.append("obsolete")
            risk_level = "critical"
        elif lifecycle != "active":
            risk_factors.append("lifecycle_concern")
            risk_level = "medium"
        
        if availability != "in_stock":
            risk_factors.append("availability_issue")
            if risk_level == "low":
                risk_level = "medium"
        
        if lead_time > 60:
            risk_factors.append("long_lead_time")
            if risk_level == "low":
                risk_level = "medium"
        
        return {
            "availability_status": availability,
            "lifecycle_status": lifecycle,
            "lead_time_days": lead_time,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": self._get_supply_chain_recommendation(
                availability, lifecycle, lead_time
            )
        }
    
    def _get_supply_chain_recommendation(
        self,
        availability: str,
        lifecycle: str,
        lead_time: int
    ) -> str:
        """Get recommendation based on supply chain status"""
        if lifecycle == "obsolete":
            return "Find alternative immediately - part is obsolete"
        elif availability != "in_stock":
            return f"Part not in stock - lead time: {lead_time} days"
        elif lead_time > 30:
            return f"Plan procurement early - {lead_time} day lead time"
        else:
            return "Supply chain looks good"

