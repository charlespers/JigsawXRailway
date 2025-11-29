"""
Design Review Agent
Executive-level design review with maturity scoring, risk assessment, and approval workflow
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from agents.analysis.design_validator_agent import DesignValidatorAgent
from agents.analysis.supply_chain_agent import SupplyChainAgent
from agents.analysis.cost_optimizer_agent import CostOptimizerAgent
from agents.analysis.thermal_analysis_agent import ThermalAnalysisAgent
from agents.analysis.manufacturing_readiness_agent import ManufacturingReadinessAgent


class DesignReviewAgent:
    """Provides executive-level design review and approval workflow."""
    
    def __init__(self):
        self.validator = DesignValidatorAgent()
        self.supply_chain = SupplyChainAgent()
        self.cost_optimizer = CostOptimizerAgent()
        self.thermal = ThermalAnalysisAgent()
        self.manufacturing = ManufacturingReadinessAgent()
    
    def review_design(
        self,
        bom_items: List[Dict[str, Any]],
        connections: Optional[List[Dict[str, Any]]] = None,
        design_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive executive-level design review.
        
        Args:
            bom_items: List of BOM items
            connections: Optional list of connections
            design_metadata: Optional metadata (design_name, version, project_id, etc.)
        
        Returns:
            Dictionary with comprehensive review:
            {
                "design_maturity_score": float (0-100),
                "risk_assessment": Dict,
                "approval_status": str,
                "executive_summary": str,
                "key_metrics": Dict,
                "recommendations": List[str],
                "review_timestamp": str
            }
        """
        # Run all analysis agents
        validation = self.validator.validate_design(bom_items, connections)
        supply_chain_analysis = self.supply_chain.analyze_supply_chain(bom_items)
        cost_analysis = self.cost_optimizer.analyze_bom_cost(bom_items)
        thermal_analysis = self.thermal.analyze_thermal(bom_items)
        manufacturing_readiness = self.manufacturing.analyze_manufacturing_readiness(bom_items, connections)
        
        # Calculate design maturity score (0-100)
        maturity_score = self._calculate_maturity_score(
            validation, supply_chain_analysis, cost_analysis, 
            thermal_analysis, manufacturing_readiness
        )
        
        # Risk assessment
        risk_assessment = self._assess_risks(
            validation, supply_chain_analysis, cost_analysis,
            thermal_analysis, manufacturing_readiness
        )
        
        # Determine approval status
        approval_status = self._determine_approval_status(maturity_score, risk_assessment)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            maturity_score, risk_assessment, cost_analysis, 
            supply_chain_analysis, design_metadata
        )
        
        # Key metrics - use safe extraction for numeric values
        from utils.cost_utils import safe_extract_cost
        total_cost_raw = cost_analysis.get("total_cost", 0)
        total_cost = safe_extract_cost(total_cost_raw, default=0.0) if isinstance(total_cost_raw, dict) else float(total_cost_raw) if total_cost_raw else 0.0
        
        risk_score_raw = supply_chain_analysis.get("risk_score") or supply_chain_analysis.get("overall_risk_score", 0)
        risk_score = float(risk_score_raw) if isinstance(risk_score_raw, (int, float)) else 0.0
        
        key_metrics = {
            "total_cost": total_cost,
            "component_count": len(bom_items),
            "total_quantity": sum(item.get("quantity", 1) for item in bom_items),
            "validation_errors": len([i for i in validation.get("issues", []) if i.get("severity") == "error"]),
            "supply_chain_risk_score": risk_score,
            "manufacturing_readiness": manufacturing_readiness.get("overall_readiness", "unknown"),
            "thermal_issues": len(thermal_analysis.get("thermal_hotspots", []))
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            maturity_score, risk_assessment, validation,
            supply_chain_analysis, cost_analysis, thermal_analysis,
            manufacturing_readiness
        )
        
        # Calculate design health score (more user-friendly than maturity)
        health_score = self._calculate_health_score(
            maturity_score, validation, supply_chain_analysis,
            cost_analysis, thermal_analysis, manufacturing_readiness
        )
        
        return {
            "design_maturity_score": round(maturity_score, 1),
            "design_health_score": round(health_score, 1),
            "maturity_level": self._get_maturity_level(maturity_score),
            "health_level": self._get_health_level(health_score),
            "health_breakdown": self._get_health_breakdown(
                validation, supply_chain_analysis, cost_analysis,
                thermal_analysis, manufacturing_readiness
            ),
            "risk_assessment": risk_assessment,
            "approval_status": approval_status,
            "approval_required": approval_status in ["requires_review", "not_approved"],
            "executive_summary": executive_summary,
            "key_metrics": key_metrics,
            "detailed_analysis": {
                "validation": validation,
                "supply_chain": supply_chain_analysis,
                "cost": cost_analysis,
                "thermal": thermal_analysis,
                "manufacturing": manufacturing_readiness
            },
            "recommendations": recommendations,
            "review_timestamp": datetime.now().isoformat(),
            "design_metadata": design_metadata or {}
        }
    
    def _calculate_maturity_score(
        self,
        validation: Dict[str, Any],
        supply_chain: Dict[str, Any],
        cost: Dict[str, Any],
        thermal: Dict[str, Any],
        manufacturing: Dict[str, Any]
    ) -> float:
        """Calculate design maturity score (0-100)."""
        score = 100.0
        
        # Validation (30% weight)
        validation_errors = len([i for i in validation.get("issues", []) if i.get("severity") == "error"])
        validation_warnings = len(validation.get("warnings", []))
        score -= (validation_errors * 10) + (validation_warnings * 2)
        
        # Supply chain (20% weight) - use safe extraction
        from agents.design.design_analyzer import safe_float_extract
        supply_chain_risk_raw = supply_chain.get("risk_score") or supply_chain.get("overall_risk_score", 0)
        supply_chain_risk = safe_float_extract(supply_chain_risk_raw, default=0.0, context="supply_chain_risk_score")
        score -= supply_chain_risk * 2
        
        # Manufacturing readiness (20% weight)
        manufacturing_status = manufacturing.get("overall_readiness", "not_ready")
        if manufacturing_status == "not_ready":
            score -= 20
        elif manufacturing_status == "needs_review":
            score -= 10
        
        # Thermal (15% weight)
        thermal_issues = len(thermal.get("thermal_hotspots", []))
        score -= thermal_issues * 3
        
        # Cost optimization (15% weight)
        optimization_opportunities = len(cost.get("optimization_opportunities", []))
        score -= min(optimization_opportunities * 1, 15)
        
        return max(0.0, min(100.0, score))
    
    def _assess_risks(
        self,
        validation: Dict[str, Any],
        supply_chain: Dict[str, Any],
        cost: Dict[str, Any],
        thermal: Dict[str, Any],
        manufacturing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall design risks."""
        risks = []
        risk_score = 0
        
        # Technical risks
        validation_errors = len([i for i in validation.get("issues", []) if i.get("severity") == "error"])
        if validation_errors > 0:
            risks.append({
                "category": "technical",
                "severity": "high",
                "description": f"{validation_errors} validation error(s) must be resolved",
                "impact": "Design may not function correctly"
            })
            risk_score += 30
        
        thermal_critical = sum(1 for h in thermal.get("thermal_hotspots", []) if h.get("severity") == "critical")
        if thermal_critical > 0:
            risks.append({
                "category": "thermal",
                "severity": "high",
                "description": f"{thermal_critical} component(s) exceed thermal limits",
                "impact": "Component failure risk"
            })
            risk_score += 25
        
        # Supply chain risks - use safe extraction
        from agents.design.design_analyzer import safe_float_extract
        supply_chain_risk_raw = supply_chain.get("risk_score") or supply_chain.get("overall_risk_score", 0)
        supply_chain_risk = safe_float_extract(supply_chain_risk_raw, default=0.0, context="supply_chain_risk_score")
        if supply_chain_risk > 50:
            risks.append({
                "category": "supply_chain",
                "severity": "medium",
                "description": "High supply chain risk detected",
                "impact": "Potential production delays or cost increases"
            })
            risk_score += 20
        
        # Manufacturing risks
        manufacturing_status = manufacturing.get("overall_readiness", "not_ready")
        if manufacturing_status == "not_ready":
            risks.append({
                "category": "manufacturing",
                "severity": "high",
                "description": "Design not ready for manufacturing",
                "impact": "Production delays and increased costs"
            })
            risk_score += 25
        
        return {
            "overall_risk_score": min(100, risk_score),
            "risk_level": "high" if risk_score > 60 else "medium" if risk_score > 30 else "low",
            "risks": risks,
            "risk_count": len(risks)
        }
    
    def _determine_approval_status(self, maturity_score: float, risk_assessment: Dict[str, Any]) -> str:
        """Determine design approval status."""
        risk_level = risk_assessment.get("risk_level", "low")
        
        if maturity_score >= 80 and risk_level == "low":
            return "approved"
        elif maturity_score >= 60 and risk_level in ["low", "medium"]:
            return "approved_with_conditions"
        elif maturity_score >= 40:
            return "requires_review"
        else:
            return "not_approved"
    
    def _generate_executive_summary(
        self,
        maturity_score: float,
        risk_assessment: Dict[str, Any],
        cost_analysis: Dict[str, Any],
        supply_chain: Dict[str, Any],
        design_metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Generate executive summary."""
        from utils.cost_utils import safe_extract_cost
        
        design_name = design_metadata.get("design_name", "Design") if design_metadata else "Design"
        total_cost_raw = cost_analysis.get("total_cost", 0)
        total_cost = safe_extract_cost(total_cost_raw, default=0.0) if isinstance(total_cost_raw, dict) else float(total_cost_raw) if total_cost_raw else 0.0
        component_count = cost_analysis.get("cost_by_category", {})
        
        summary = f"{design_name} Review Summary:\n\n"
        summary += f"Design Maturity Score: {maturity_score:.1f}/100 ({self._get_maturity_level(maturity_score)})\n"
        summary += f"Approval Status: {self._determine_approval_status(maturity_score, risk_assessment).replace('_', ' ').title()}\n"
        summary += f"Total BOM Cost: ${total_cost:.2f}\n"
        summary += f"Risk Level: {risk_assessment.get('risk_level', 'unknown').title()}\n"
        summary += f"Identified Risks: {risk_assessment.get('risk_count', 0)}\n"
        
        if risk_assessment.get("risk_count", 0) > 0:
            summary += "\nKey Risks:\n"
            for risk in risk_assessment.get("risks", [])[:3]:
                summary += f"- {risk['description']} ({risk['severity']} severity)\n"
        
        return summary
    
    def _get_maturity_level(self, score: float) -> str:
        """Get maturity level from score."""
        if score >= 80:
            return "Production Ready"
        elif score >= 60:
            return "Near Production"
        elif score >= 40:
            return "Needs Improvement"
        else:
            return "Not Ready"
    
    def _generate_recommendations(
        self,
        maturity_score: float,
        risk_assessment: Dict[str, Any],
        validation: Dict[str, Any],
        supply_chain: Dict[str, Any],
        cost: Dict[str, Any],
        thermal: Dict[str, Any],
        manufacturing: Dict[str, Any]
    ) -> List[str]:
        """Generate prioritized recommendations."""
        recommendations = []
        
        # High priority: Validation errors
        validation_errors = len([i for i in validation.get("issues", []) if i.get("severity") == "error"])
        if validation_errors > 0:
            recommendations.append(f"URGENT: Resolve {validation_errors} validation error(s) before proceeding")
        
        # High priority: Manufacturing readiness
        if manufacturing.get("overall_readiness") == "not_ready":
            recommendations.append("URGENT: Address manufacturing readiness issues")
        
        # Medium priority: Thermal issues
        thermal_critical = sum(1 for h in thermal.get("thermal_hotspots", []) if h.get("severity") == "critical")
        if thermal_critical > 0:
            recommendations.append(f"Address {thermal_critical} critical thermal issue(s)")
        
        # Medium priority: Supply chain - use safe extraction
        from agents.design.design_analyzer import safe_float_extract
        supply_risk_raw = supply_chain.get("risk_score") or supply_chain.get("overall_risk_score", 0)
        supply_risk = safe_float_extract(supply_risk_raw, default=0.0, context="supply_chain_risk_score")
        if supply_risk > 50:
            recommendations.append("Review supply chain risks and consider alternative components")
        
        # Low priority: Cost optimization
        optimization_opportunities = len(cost.get("optimization_opportunities", []))
        if optimization_opportunities > 0:
            recommendations.append(f"Consider {optimization_opportunities} cost optimization opportunity(ies)")
        
        # General recommendations based on maturity score
        if maturity_score < 60:
            recommendations.append("Design requires significant improvements before production")
        elif maturity_score < 80:
            recommendations.append("Design is close to production-ready but needs refinement")
        
        return recommendations
    
    def _calculate_health_score(
        self,
        maturity_score: float,
        validation: Dict[str, Any],
        supply_chain: Dict[str, Any],
        cost: Dict[str, Any],
        thermal: Dict[str, Any],
        manufacturing: Dict[str, Any]
    ) -> float:
        """Calculate design health score (0-100) with category breakdown."""
        # Start with maturity score as base
        health = maturity_score
        
        # Adjust based on critical issues
        validation_errors = len([i for i in validation.get("issues", []) if i.get("severity") == "error"])
        health -= validation_errors * 5  # -5 points per error
        
        # Adjust for supply chain risks - use safe extraction
        from agents.design.design_analyzer import safe_float_extract
        supply_risk_raw = supply_chain.get("risk_score") or supply_chain.get("overall_risk_score", 0)
        supply_risk = safe_float_extract(supply_risk_raw, default=0.0, context="supply_chain_risk_score")
        if supply_risk > 70:
            health -= 10
        elif supply_risk > 50:
            health -= 5
        
        # Adjust for manufacturing readiness
        mfg_readiness = manufacturing.get("overall_readiness", "unknown")
        if mfg_readiness == "not_ready":
            health -= 15
        elif mfg_readiness == "needs_improvement":
            health -= 8
        
        # Adjust for thermal issues
        thermal_critical = sum(1 for h in thermal.get("thermal_hotspots", []) if h.get("severity") == "critical")
        if thermal_critical > 0:
            health -= thermal_critical * 3
        
        return max(0.0, min(100.0, health))
    
    def _get_health_level(self, score: float) -> str:
        """Get health level description."""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Needs Improvement"
        else:
            return "Critical"
    
    def _get_health_breakdown(
        self,
        validation: Dict[str, Any],
        supply_chain: Dict[str, Any],
        cost: Dict[str, Any],
        thermal: Dict[str, Any],
        manufacturing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get health score breakdown by category."""
        breakdown = {}
        
        # Validation health (0-100)
        validation_errors = len([i for i in validation.get("issues", []) if i.get("severity") == "error"])
        validation_warnings = len([i for i in validation.get("issues", []) if i.get("severity") == "warning"])
        validation_score = max(0, 100 - (validation_errors * 20) - (validation_warnings * 5))
        breakdown["validation"] = {
            "score": round(validation_score, 1),
            "status": "excellent" if validation_score >= 90 else "good" if validation_score >= 70 else "needs_improvement",
            "errors": validation_errors,
            "warnings": validation_warnings
        }
        
        # Supply chain health (0-100) - use safe extraction
        from agents.design.design_analyzer import safe_float_extract
        supply_risk_raw = supply_chain.get("risk_score") or supply_chain.get("overall_risk_score", 0)
        supply_risk = safe_float_extract(supply_risk_raw, default=0.0, context="supply_chain_risk_score")
        supply_score = max(0, 100 - supply_risk)
        breakdown["supply_chain"] = {
            "score": round(supply_score, 1),
            "status": "excellent" if supply_score >= 80 else "good" if supply_score >= 60 else "needs_improvement",
            "risk_score": supply_risk
        }
        
        # Manufacturing health (0-100)
        mfg_readiness = manufacturing.get("overall_readiness", "unknown")
        mfg_score = {
            "ready": 100,
            "needs_improvement": 70,
            "not_ready": 30,
            "unknown": 50
        }.get(mfg_readiness, 50)
        breakdown["manufacturing"] = {
            "score": round(mfg_score, 1),
            "status": mfg_readiness,
            "readiness": mfg_readiness
        }
        
        # Thermal health (0-100)
        thermal_issues = thermal.get("thermal_hotspots", [])
        thermal_critical = sum(1 for h in thermal_issues if h.get("severity") == "critical")
        thermal_warning = sum(1 for h in thermal_issues if h.get("severity") == "warning")
        thermal_score = max(0, 100 - (thermal_critical * 15) - (thermal_warning * 5))
        breakdown["thermal"] = {
            "score": round(thermal_score, 1),
            "status": "excellent" if thermal_score >= 90 else "good" if thermal_score >= 70 else "needs_improvement",
            "critical_issues": thermal_critical,
            "warnings": thermal_warning
        }
        
        # Cost health (0-100) - based on optimization opportunities
        cost_opps = len(cost.get("optimization_opportunities", []))
        cost_score = max(0, 100 - (cost_opps * 5))
        breakdown["cost"] = {
            "score": round(cost_score, 1),
            "status": "excellent" if cost_score >= 90 else "good" if cost_score >= 70 else "needs_improvement",
            "optimization_opportunities": cost_opps
        }
        
        return breakdown

