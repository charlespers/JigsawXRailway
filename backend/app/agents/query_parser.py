"""
Smart query parser agent
Extracts specifications from natural language queries using LLM
"""
import logging
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.core.exceptions import RequirementsExtractionError

logger = logging.getLogger(__name__)


class QueryParserAgent(BaseAgent):
    """
    Parses natural language queries to extract exact specifications.
    Solves: "I need a 3.3V regulator with 500mA output and I2C interface"
    """
    
    SYSTEM_PROMPT = """You are an expert PCB component specification parser. Extract exact technical specifications from natural language queries.

Return a JSON object with these fields (use null if not specified):
- voltage_min, voltage_max: Voltage range in volts
- current_min, current_max: Current range in amps
- power_min, power_max: Power range in watts
- interfaces: List of interfaces (e.g., ["I2C", "SPI", "USB-C", "WiFi"])
- package: Package type (e.g., "QFN", "SOIC", "SOT23")
- footprint: IPC-7351 footprint name
- temp_min, temp_max: Operating temperature range in Celsius
- rohs_compliant: Boolean for RoHS requirement
- category: Component category (mcu, sensor, power, connector, etc.)

Be precise and extract all technical specifications mentioned. If a value is approximate, use reasonable bounds."""

    def parse_specifications(self, query: str) -> Dict[str, Any]:
        """
        Parse query to extract specifications
        
        Args:
            query: Natural language query (e.g., "I need a 3.3V regulator with 500mA and I2C")
        
        Returns:
            Dictionary with extracted specifications
        """
        try:
            user_prompt = f"Extract specifications from this query: {query}"
            response = self._call_llm(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.2  # Low temperature for precise extraction
            )
            specs = self._parse_json_response(response)
            
            # Clean and validate specifications
            cleaned_specs = {}
            for key, value in specs.items():
                if value is not None:
                    cleaned_specs[key] = value
            
            logger.info(f"Parsed specifications: {cleaned_specs}")
            return cleaned_specs
            
        except Exception as e:
            logger.error(f"Query parsing error: {e}")
            raise RequirementsExtractionError(f"Failed to parse query: {e}")

