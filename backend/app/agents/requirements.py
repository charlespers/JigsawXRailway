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
    
    SYSTEM_PROMPT = """You are an expert PCB design engineer with deep knowledge of:
- IPC standards (IPC-2221 for design, IPC-7351 for footprints, IPC-2581 for BOM)
- Industry best practices for component selection
- Cost optimization strategies
- Manufacturing considerations (DFM, assembly complexity)
- Supply chain and lifecycle management
- Power management and thermal design
- Signal integrity and EMI/EMC considerations

Extract structured requirements from natural language queries about PCB designs.

Return a JSON object with:
- functional_requirements: List of functional requirements (e.g., ["temperature sensing", "WiFi connectivity"])
- power_requirements: Dict with voltage (V), current (A), power source type, power budget constraints
- interface_requirements: List of interfaces needed (e.g., ["I2C", "SPI", "USB-C"])
- environmental_requirements: Dict with temperature range, humidity, operating conditions
- constraints: Dict with size, cost, compliance requirements (RoHS, IPC standards), manufacturability needs
- component_count: Integer number of distinct components requested (e.g., "3 components" -> 3, "simple PCB with 5 parts" -> 5, "a few components" -> 3-4)

CRITICAL: Extract component_count from phrases like:
- "3 components" -> 3
- "simple PCB with X parts" -> extract X
- "a few components" -> 3-4 (use 3 as default)
- "several components" -> 4-6 (use 4 as default)
- "multiple components" -> 3-5 (use 3 as default)
- If no quantity mentioned, set component_count to null

Consider engineering context:
- Cost constraints: Extract budget limits, cost optimization needs
- Manufacturing: Note if design needs to be manufacturable, assembly-friendly
- Standards: Identify IPC compliance needs, RoHS requirements
- Power: Extract power consumption limits, battery operation needs
- Environment: Extract operating conditions (temperature, humidity, harsh environments)

Be precise and extract all technical specifications mentioned, especially component quantities and engineering constraints."""

    def extract(self, query: str) -> Requirements:
        """Extract requirements from query"""
        try:
            user_prompt = f"""Extract requirements from this query: {query}

Pay special attention to:
1. Component count/quantity (e.g., "3 components", "5 parts", "a few components")
2. Functional requirements (what the PCB should do)
3. Technical specifications (voltage, interfaces, etc.)
4. Constraints (cost, size, etc.)

Return a complete JSON object with all extracted requirements."""
            response = self._call_llm(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3
            )
            data = self._parse_json_response(response)
            
            # Validate component_count if present
            if "component_count" in data and data["component_count"] is not None:
                try:
                    component_count = int(data["component_count"])
                    if component_count < 1:
                        logger.warning(f"Invalid component_count {component_count}, setting to None")
                        data["component_count"] = None
                    else:
                        data["component_count"] = component_count
                        logger.info(f"Extracted component_count: {component_count}")
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse component_count: {data.get('component_count')}")
                    data["component_count"] = None
            
            return Requirements(**data)
        except Exception as e:
            logger.error(f"Requirements extraction error: {e}")
            raise RequirementsExtractionError(f"Failed to extract requirements: {e}")

