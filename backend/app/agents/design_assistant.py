"""
Conversational Design Assistant Agent
Magical conversational interface that helps designers refine requirements
"""
import logging
from typing import Dict, List, Any, Optional
from app.agents.base import BaseAgent
from app.core.exceptions import RequirementsExtractionError

logger = logging.getLogger(__name__)


class DesignAssistantAgent(BaseAgent):
    """
    Conversational design assistant that helps refine requirements.
    
    Solves: Designer says "I need a sensor" → Assistant asks clarifying questions
            → Designer refines → Perfect parts found
    """
    
    SYSTEM_PROMPT = """You are a helpful PCB design assistant. Your job is to help designers clarify their requirements through intelligent questions.

When a designer gives a vague query, ask 2-3 targeted questions to understand:
1. What exactly does the part need to do?
2. What are the critical constraints (power, cost, size)?
3. What's the design context (battery-powered, industrial, consumer)?

Be conversational, helpful, and ask ONE question at a time to guide the conversation naturally.

Return JSON:
{
  "needs_clarification": true/false,
  "clarifying_question": "What's your question?",
  "suggested_refinements": ["refinement 1", "refinement 2"],
  "confidence": 0.0-1.0,
  "refined_query": "refined version if confidence is high"
}"""

    def assist(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Assist designer by asking clarifying questions or refining query.
        
        Args:
            query: Current user query
            conversation_history: Previous conversation turns
        
        Returns:
            Assistant response with questions or refined query
        """
        try:
            history_str = self._format_history(conversation_history or [])
            
            user_prompt = f"""
Current Query: {query}

Conversation History:
{history_str}

Analyze if this query needs clarification. If it's vague, ask ONE helpful question.
If it's clear, provide a refined version with all implicit requirements made explicit.
"""
            
            response = self._call_llm(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.7  # More creative for conversations
            )
            
            result = self._parse_json_response(response)
            
            return {
                "query": query,
                "needs_clarification": result.get("needs_clarification", False),
                "clarifying_question": result.get("clarifying_question"),
                "suggested_refinements": result.get("suggested_refinements", []),
                "confidence": result.get("confidence", 0.0),
                "refined_query": result.get("refined_query", query),
                "assistant_message": self._generate_message(result)
            }
            
        except Exception as e:
            logger.error(f"Design assistant error: {e}")
            raise RequirementsExtractionError(f"Assistant error: {e}")
    
    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history"""
        if not history:
            return "No previous conversation"
        
        formatted = []
        for turn in history[-5:]:  # Last 5 turns
            role = turn.get("role", "user")
            content = turn.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted)
    
    def _generate_message(self, result: Dict[str, Any]) -> str:
        """Generate friendly assistant message"""
        if result.get("needs_clarification"):
            return result.get("clarifying_question", "Could you provide more details?")
        else:
            return f"I understand! Here's a refined version: {result.get('refined_query', '')}"

