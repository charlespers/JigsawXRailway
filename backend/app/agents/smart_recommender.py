"""
Smart Recommender Agent
Proactively suggests parts based on design context
"""
import logging
from typing import Dict, List, Any, Optional
from app.domain.part_database import get_part_database
from app.agents.base import BaseAgent
from app.agents.compatibility import CompatibilityAgent

logger = logging.getLogger(__name__)


class SmartRecommenderAgent(BaseAgent):
    """
    Proactively suggests parts based on what's already selected.
    
    Solves: Designer selects MCU → Recommends compatible power regulator,
            crystal, passives, connectors automatically
    """
    
    SYSTEM_PROMPT = """You are an expert PCB design advisor with knowledge of:
- IPC design standards and best practices
- Component compatibility and interface requirements
- Power management and distribution
- Signal integrity and EMI/EMC considerations
- Manufacturing and assembly requirements
- Cost optimization strategies

Based on selected parts, suggest complementary components following engineering best practices.

Consider:
1. What supporting parts are typically needed? (power management, passives, connectors, protection)
2. What's compatible with selected parts? (voltage levels, interfaces, packages)
3. What's missing for a complete design? (decoupling caps, pull-ups, crystals, protection circuits)
4. Manufacturing considerations: Are all necessary passives included? Are packages manufacturable?
5. Cost optimization: Can cheaper alternatives be suggested without compromising functionality?
6. Supply chain: Are suggested parts readily available with good lifecycle status?

Return JSON with suggestions:
{
  "suggestions": [
    {
      "component_type": "power_regulator",
      "reason": "why this is needed (engineering justification)",
      "priority": "critical/high/medium/low",
      "query": "natural language query to find this part",
      "engineering_notes": "Technical considerations (voltage compatibility, current rating, etc.)"
    }
  ],
  "warnings": ["any warnings about missing components or compatibility issues"],
  "recommendations": ["design recommendations following IPC standards and best practices"],
  "completeness_score": 0-100,
  "manufacturing_readiness": "ready/needs_review/not_ready"
}

Focus on:
- Completeness: Ensure design has all necessary components
- Compatibility: All parts work together (voltage, interfaces, etc.)
- Manufacturability: Design can be easily assembled
- Cost-effectiveness: Suggest cost-optimized alternatives when appropriate
- Standards compliance: Follow IPC guidelines"""

    def __init__(self):
        super().__init__()
        self.db = get_part_database()
        self.compat_agent = CompatibilityAgent()
    
    def recommend(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        design_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recommend complementary parts based on selection.
        
        This is MAGICAL - understands what's missing and suggests it!
        """
        try:
            # Analyze what's selected
            analysis = self._analyze_selection(selected_parts)
            
            # Use LLM to generate recommendations
            context_str = self._build_context(selected_parts, design_context)
            
            user_prompt = f"""
Selected Parts:
{context_str}

Design Context:
{design_context or "Standard design"}

Analyze what's missing and suggest complementary components. Consider:
- Power management (regulators, filters)
- Clock sources (crystals, oscillators)
- Passives (decoupling caps, pull-ups)
- Connectors and interfaces
- Protection components (TVS, fuses)
- Any critical missing pieces

Be specific about why each suggestion is needed.
"""
            
            response = self._call_llm(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.5
            )
            
            recommendations = self._parse_json_response(response)
            
            # Enhance with database knowledge
            enhanced = self._enhance_recommendations(
                recommendations,
                selected_parts,
                analysis
            )
            
            return {
                "selected_parts_analysis": analysis,
                "suggestions": enhanced["suggestions"],
                "warnings": enhanced["warnings"],
                "recommendations": enhanced["recommendations"],
                "completeness_score": self._calculate_completeness(selected_parts, enhanced)
            }
            
        except Exception as e:
            logger.error(f"Recommendation error: {e}", exc_info=True)
            return {
                "suggestions": [],
                "warnings": [f"Recommendation error: {e}"],
                "recommendations": []
            }
    
    def _analyze_selection(self, parts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze what's been selected"""
        analysis = {
            "has_mcu": False,
            "has_power": False,
            "has_connector": False,
            "has_crystal": False,
            "has_passives": False,
            "voltage_requirements": [],
            "interface_requirements": [],
            "power_consumption": None
        }
        
        for part_name, part in parts.items():
            category = part.get("category", "").lower()
            
            if "mcu" in category:
                analysis["has_mcu"] = True
                # Extract voltage requirement
                voltage = self._extract_voltage(part)
                if voltage:
                    analysis["voltage_requirements"].append(voltage)
                
                # Extract interfaces
                interfaces = part.get("interface_type", [])
                if isinstance(interfaces, str):
                    interfaces = [interfaces]
                analysis["interface_requirements"].extend(interfaces)
            
            elif "power" in category or "regulator" in category:
                analysis["has_power"] = True
            
            elif "connector" in category:
                analysis["has_connector"] = True
            
            elif "crystal" in category:
                analysis["has_crystal"] = True
            
            elif "passive" in category:
                analysis["has_passives"] = True
        
        return analysis
    
    def _enhance_recommendations(
        self,
        recommendations: Dict[str, Any],
        selected_parts: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance LLM recommendations with database knowledge"""
        enhanced_suggestions = []
        
        for suggestion in recommendations.get("suggestions", []):
            # Add specific part recommendations from database
            query = suggestion.get("query", "")
            if query:
                # Search database for matching parts
                candidates = self._search_for_suggestion(query, selected_parts)
                suggestion["candidate_parts"] = candidates[:3]  # Top 3 matches
            
            enhanced_suggestions.append(suggestion)
        
        # Add critical missing components based on analysis
        if analysis["has_mcu"] and not analysis["has_power"]:
            enhanced_suggestions.append({
                "component_type": "power_regulator",
                "reason": "MCU requires regulated power supply",
                "priority": "critical",
                "query": f"{analysis['voltage_requirements'][0] if analysis['voltage_requirements'] else '3.3'}V regulator",
                "candidate_parts": []
            })
        
        if analysis["has_mcu"] and not analysis["has_crystal"]:
            enhanced_suggestions.append({
                "component_type": "crystal",
                "reason": "MCU typically requires external crystal for accurate timing",
                "priority": "high",
                "query": "32.768kHz crystal or MCU frequency crystal",
                "candidate_parts": []
            })
        
        return {
            "suggestions": enhanced_suggestions,
            "warnings": recommendations.get("warnings", []),
            "recommendations": recommendations.get("recommendations", [])
        }
    
    def _search_for_suggestion(
        self,
        query: str,
        selected_parts: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Search database for suggestion"""
        # Simplified - in production, use intelligent matcher
        all_parts = self.db.get_all_parts()
        
        # Simple keyword matching
        query_lower = query.lower()
        matches = []
        
        for part in all_parts[:50]:  # Limit search
            name = part.get("name", "").lower()
            desc = part.get("description", "").lower()
            category = part.get("category", "").lower()
            
            score = 0
            if any(word in name for word in query_lower.split()):
                score += 2
            if any(word in desc for word in query_lower.split()):
                score += 1
            if any(word in category for word in query_lower.split()):
                score += 1
            
            if score > 0:
                matches.append((part, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return [part for part, score in matches[:5]]
    
    def _calculate_completeness(
        self,
        selected: Dict[str, Any],
        recommendations: Dict[str, Any]
    ) -> float:
        """Calculate design completeness score (0-100)"""
        critical_suggestions = [
            s for s in recommendations["suggestions"]
            if s.get("priority") == "critical"
        ]
        
        if not critical_suggestions:
            return 100.0  # No critical missing parts
        
        # Penalize for each critical missing part
        return max(0, 100 - len(critical_suggestions) * 20)
    
    def _extract_voltage(self, part: Dict[str, Any]) -> Optional[float]:
        supply = part.get("supply_voltage_range", {})
        if isinstance(supply, dict):
            return supply.get("nominal") or supply.get("max") or supply.get("min")
        return None
    
    def _build_context(self, parts: Dict[str, Any], context: Optional[Dict]) -> str:
        """Build context string"""
        lines = []
        for role, part in parts.items():
            lines.append(f"{role}: {part.get('name', 'Unknown')} ({part.get('category', 'unknown')})")
        return "\n".join(lines)

