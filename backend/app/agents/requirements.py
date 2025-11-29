"""
Requirements extraction agent
Extracts structured requirements from natural language queries
"""
import logging
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.domain.models import Requirements
from app.core.exceptions import RequirementsExtractionError

logger = logging.getLogger(__name__)


class RequirementsAgent(BaseAgent):
    """Extracts structured requirements from user queries"""
    
    SYSTEM_PROMPT = """You are an expert PCB design engineer. Extract structured requirements from natural language queries about PCB designs.

Return a JSON object with:
- functional_requirements: List of functional requirements (e.g., ["temperature sensing", "WiFi connectivity"])
- power_requirements: Dict with voltage (V), current (A), power source type
- interface_requirements: List of interfaces needed (e.g., ["I2C", "SPI", "USB-C"])
- environmental_requirements: Dict with temperature range, humidity, etc.
- constraints: Dict with size, cost, compliance requirements

Be precise and extract all technical specifications mentioned."""

    def extract(self, query: str) -> Requirements:
        """Extract requirements from query"""
        try:
            user_prompt = f"Extract requirements from this query: {query}"
            response = self._call_llm(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3
            )
            data = self._parse_json_response(response)
            return Requirements(**data)
        except Exception as e:
            logger.error(f"Requirements extraction error: {e}")
            raise RequirementsExtractionError(f"Failed to extract requirements: {e}")

