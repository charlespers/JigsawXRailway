"""
Design Review Agent
Executive-level design review with maturity scoring, risk assessment, and approval workflow
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from agents.design_validator_agent import DesignValidatorAgent
from agents.supply_chain_agent import SupplyChainAgent
from agents.cost_optimizer_agent import CostOptimizerAgent
from agents.thermal_analysis_agent import ThermalAnalysisAgent
from agents.manufacturing_readiness_agent import ManufacturingReadinessAgent


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
        
        # Key metrics
        key_metrics = {
            "total_cost": cost_analysis.get("total_cost", 0),
            "component_count": len(bom_items),
            "total_quantity": sum(item.get("quantity", 1) for item in bom_items),
            "validation_errors": len([i for i in validation.get("issues", []) if i.get("severity") == "error"]),
            "supply_chain_risk_score": supply_chain_analysis.get("overall_risk_score", 0),
            "manufacturing_readiness": manufacturing_readiness.get("overall_readiness", "unknown"),
            "thermal_issues": len(thermal_analysis.get("thermal_hotspots", []))
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            maturity_score, risk_assessment, validation,
            supply_chain_analysis, cost_analysis, thermal_analysis,
            manufacturing_readiness
        )
        
        return {
            "design_maturity_score": round(maturity_score, 1),
            "maturity_level": self._get_maturity_level(maturity_score),
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
        
        # Supply chain (20% weight)
        supply_chain_risk = supply_chain.get("overall_risk_score", 0)
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
        
        # Supply chain risks
        supply_chain_risk = supply_chain.get("overall_risk_score", 0)
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
        design_name = design_metadata.get("design_name", "Design") if design_metadata else "Design"
        total_cost = cost_analysis.get("total_cost", 0)
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
        
        # Medium priority: Supply chain
        if supply_chain.get("overall_risk_score", 0) > 50:
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

