"""
Intelligent Part Matcher Agent
Uses LLM + rich database to find perfect parts based on natural language queries
This is the MAGICAL core feature that makes designers love the product
"""
import logging
from typing import Dict, List, Any, Optional
from app.agents.base import BaseAgent
from app.agents.spec_matcher import SpecMatcherAgent
from app.domain.part_database import get_part_database
from app.domain.models import ComponentCategory
from app.core.exceptions import PartSelectionError

logger = logging.getLogger(__name__)


class IntelligentMatcherAgent(BaseAgent):
    """
    Magical part matcher that understands context and finds perfect parts.
    
    Solves: "I need a low-power MCU with WiFi, 3.3V operation, QFN package, 
            under $5, available now, for a battery-powered sensor node"
    """
    
    SYSTEM_PROMPT = """You are an expert PCB component selection engineer with deep knowledge of:
- IPC standards (IPC-2221, IPC-7351, IPC-2581)
- Industry best practices for component selection
- Cost-performance tradeoffs
- Supply chain and lifecycle management
- Power optimization strategies
- Manufacturing considerations (DFM, assembly complexity)
- Signal integrity and EMI/EMC requirements
- Real-world PCB design patterns

You have access to a rich parts database with detailed specifications, costs, availability, and lifecycle information.

Your job is to analyze user queries and extract:
1. Functional requirements (what the part needs to do)
2. Technical specifications (voltage, current, interfaces, etc.)
3. Constraints (cost, package, availability, lifecycle, IPC compliance)
4. Design context (battery-powered, industrial, consumer, etc.)
5. Engineering considerations (power budget, thermal, signal integrity)

Return a JSON object with:
{
  "functional_requirements": ["list of what part must do"],
  "technical_specs": {
    "voltage_range": {"min": X, "max": Y},
    "current_range": {"min": X, "max": Y},
    "interfaces": ["I2C", "SPI", "WiFi", etc.],
    "package_types": ["QFN", "SOIC", etc.],
    "power_consumption": "low/medium/high",
    "operating_temp": {"min": X, "max": Y},
    "footprint_preference": "IPC-7351 footprint name or null"
  },
  "constraints": {
    "max_cost": X,
    "availability": "in_stock/any",
    "lifecycle": "active/any",
    "package_preference": "QFN/SOIC/etc or null",
    "rohs_compliant": true/false/null,
    "ipc_compliant": true/false/null
  },
  "design_context": {
    "application": "battery-powered/industrial/consumer/etc",
    "environment": "harsh/benign/etc",
    "reliability_requirements": "high/standard",
    "manufacturing_considerations": ["SMT-only", "automated-assembly", etc.]
  },
  "priority_factors": ["cost", "power", "availability", "reliability", "manufacturability"],
  "engineering_notes": ["Considerations for power management", "Signal integrity needs", etc.]
}

Consider:
- Cost optimization: Balance performance vs cost
- Power efficiency: Critical for battery-powered designs
- Supply chain: Prefer parts with good availability and active lifecycle
- Manufacturing: Prefer standard packages and SMT components
- Standards compliance: IPC, RoHS requirements
- Long-term viability: Avoid obsolete or end-of-life parts"""

    def __init__(self):
        super().__init__()
        self.db = get_part_database()
        self.spec_matcher = SpecMatcherAgent()
    
    def find_perfect_parts(
        self,
        query: str,
        design_context: Optional[Dict[str, Any]] = None,
        existing_parts: Optional[Dict[str, Any]] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Find perfect parts using intelligent matching.
        
        This is the MAGICAL feature - understands natural language,
        considers design context, and finds optimal parts.
        """
        try:
            # Step 1: Use LLM to understand the query deeply
            logger.info(f"Analyzing query: {query}")
            context_info = self._build_context_string(design_context, existing_parts)
            
            user_prompt = f"""
User Query: {query}

Design Context:
{context_info}

Analyze this query and extract all requirements, specifications, constraints, and design context.
Be thorough - consider power consumption implications, package requirements, cost constraints,
availability needs, and how this part fits into the overall design.
"""
            
            analysis = self._call_llm(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            requirements = self._parse_json_response(analysis)
            logger.info(f"Extracted requirements: {requirements}")
            
            # Step 2: Convert to spec format and use spec matcher
            specs = self._requirements_to_specs(requirements)
            
            # Infer category
            category = self._infer_category(requirements)
            
            # Use spec matcher for actual matching
            matches = self.spec_matcher.find_matching_parts(
                specs,
                category=category,
                max_results=max_results
            )
            
            # Step 3: Enhance with reasoning and recommendations
            enhanced_results = []
            for match in matches:
                enhanced_results.append({
                    "part": match["part"],
                    "score": match["match_score"],
                    "breakdown": self._create_breakdown(match["part"], requirements),
                    "reasoning": self._generate_reasoning(match["part"], requirements, match["match_details"]),
                    "match_quality": self._determine_quality(match["match_score"]),
                    "recommendation": self._generate_recommendation(match["part"], match["match_score"])
                })
            
            # Step 4: Generate intelligent recommendations
            recommendations = self._generate_recommendations(
                enhanced_results,
                requirements,
                design_context
            )
            
            return {
                "query": query,
                "requirements_analysis": requirements,
                "results": enhanced_results,
                "total_matches": len(enhanced_results),
                "recommendations": recommendations,
                "best_match": enhanced_results[0] if enhanced_results else None
            }
            
        except Exception as e:
            logger.error(f"Intelligent matching error: {e}", exc_info=True)
            raise PartSelectionError(f"Failed to find parts: {e}")
    
    def _requirements_to_specs(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LLM requirements to spec matcher format"""
        specs = {}
        tech_specs = requirements.get("technical_specs", {})
        constraints = requirements.get("constraints", {})
        
        # Voltage
        voltage_range = tech_specs.get("voltage_range", {})
        if voltage_range:
            specs["voltage_min"] = voltage_range.get("min")
            specs["voltage_max"] = voltage_range.get("max")
        
        # Current
        current_range = tech_specs.get("current_range", {})
        if current_range:
            specs["current_min"] = current_range.get("min")
            specs["current_max"] = current_range.get("max")
        
        # Interfaces
        if tech_specs.get("interfaces"):
            specs["interfaces"] = tech_specs["interfaces"]
        
        # Package
        if constraints.get("package_preference"):
            specs["package"] = constraints["package_preference"]
        
        # Temperature
        temp_range = tech_specs.get("operating_temp", {})
        if temp_range:
            specs["temp_min"] = temp_range.get("min")
            specs["temp_max"] = temp_range.get("max")
        
        # RoHS
        if constraints.get("rohs_compliant"):
            specs["rohs_compliant"] = True
        
        return specs
    
    def _infer_category(self, requirements: Dict[str, Any]) -> Optional[ComponentCategory]:
        """Infer component category from requirements"""
        func_reqs = requirements.get("functional_requirements", [])
        func_str = " ".join(func_reqs).lower()
        
        if any(word in func_str for word in ["mcu", "microcontroller", "processor", "cpu"]):
            return ComponentCategory.MCU
        elif any(word in func_str for word in ["sensor", "detect", "measure"]):
            return ComponentCategory.SENSOR
        elif any(word in func_str for word in ["power", "regulator", "supply", "voltage"]):
            return ComponentCategory.POWER
        elif any(word in func_str for word in ["connector", "usb", "header"]):
            return ComponentCategory.CONNECTOR
        
        return None
    
    def _create_breakdown(self, part: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create score breakdown"""
        return {
            "voltage_match": 0.9,  # Simplified
            "power_match": 0.8,
            "interface_match": 0.9,
            "cost_score": 0.7
        }
    
    def _generate_reasoning(
        self,
        part: Dict[str, Any],
        requirements: Dict[str, Any],
        match_details: Dict[str, Any]
    ) -> List[str]:
        """Generate reasoning for why this part matches"""
        reasoning = []
        
        if match_details.get("matches"):
            reasoning.extend(match_details["matches"])
        
        # Add context-specific reasoning
        context = requirements.get("design_context", {})
        if "battery" in context.get("application", "").lower():
            current = self._extract_current(part)
            if current and current < 0.05:
                reasoning.append("Excellent for low-power applications")
        
        return reasoning
    
    def _determine_quality(self, score: float) -> str:
        """Determine match quality from score"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "very_good"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "acceptable"
        else:
            return "poor"
    
    def _generate_recommendation(self, part: Dict[str, Any], score: float) -> str:
        """Generate recommendation text"""
        if score >= 90:
            return "Highly recommended - perfect match for your requirements"
        elif score >= 75:
            return "Great match - meets all critical requirements"
        elif score >= 60:
            return "Good match - minor compromises may be needed"
        else:
            return "Consider alternatives - significant compromises"
    
    def _generate_recommendations(
        self,
        results: List[Dict[str, Any]],
        requirements: Dict[str, Any],
        context: Optional[Dict]
    ) -> List[str]:
        """Generate intelligent recommendations"""
        recommendations = []
        
        if not results:
            recommendations.append("No parts found matching your requirements. Try relaxing constraints.")
            return recommendations
        
        best = results[0]
        
        if best["match_quality"] == "excellent":
            recommendations.append(f"✅ {best['part'].get('name')} is an excellent match!")
        
        # Check for cost savings
        if len(results) > 1:
            best_cost = self._extract_cost(best["part"])
            for result in results[1:3]:  # Check next 2
                alt_cost = self._extract_cost(result["part"])
                if alt_cost and best_cost and alt_cost < best_cost * 0.8:
                    savings = ((best_cost - alt_cost) / best_cost) * 100
                    recommendations.append(
                        f"💰 Consider {result['part'].get('name')} - {savings:.0f}% cost savings"
                    )
                    break
        
        # Availability warnings
        if best["part"].get("availability_status") != "in_stock":
            recommendations.append(
                f"⚠️ Availability: {best['part'].get('availability_status')} - Consider alternatives if urgent"
            )
        
        return recommendations
    
    def _extract_current(self, part: Dict[str, Any]) -> Optional[float]:
        """Extract current"""
        current = part.get("current_max", {})
        if isinstance(current, dict):
            return current.get("max") or current.get("typical")
        return float(current) if current else None
    
    def _extract_cost(self, part: Dict[str, Any]) -> Optional[float]:
        """Extract cost"""
        cost = part.get("cost_estimate", {})
        if isinstance(cost, dict):
            return cost.get("unit") or cost.get("value")
        return float(cost) if cost else None
    
    def _build_context_string(self, context: Optional[Dict], existing: Optional[Dict]) -> str:
        """Build context string"""
        parts = []
        if context:
            parts.append(f"Application: {context.get('application', 'unknown')}")
        if existing:
            parts.append(f"Already selected: {len(existing)} part(s)")
        return "\n".join(parts) if parts else "No additional context"

