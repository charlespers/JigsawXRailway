"""
Architecture design agent
Designs system architecture from requirements
"""
import logging
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.domain.models import Architecture, Requirements
from app.core.exceptions import RequirementsExtractionError

logger = logging.getLogger(__name__)


class ArchitectureAgent(BaseAgent):
    """Designs system architecture from requirements"""
    
    SYSTEM_PROMPT = """You are an expert PCB design architect. Design a modular system architecture from requirements.

Return a JSON object with:
- anchor_block: Dict with type, description, and key specifications of the main component
- child_blocks: List of Dicts for supporting components (power, interfaces, passives)
- dependencies: List of Dicts showing how blocks depend on each other

Follow engineering best practices: separate power, digital, analog domains."""

    def design(self, requirements: Requirements) -> Architecture:
        """Design architecture from requirements"""
        try:
            req_json = requirements.model_dump_json()
            user_prompt = f"Design architecture for these requirements:\n{req_json}"
            response = self._call_llm(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.5
            )
            data = self._parse_json_response(response)
            return Architecture(**data)
        except Exception as e:
            logger.error(f"Architecture design error: {e}")
            raise RequirementsExtractionError(f"Failed to design architecture: {e}")

