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
    
    SYSTEM_PROMPT = """You are an expert PCB design architect with expertise in:
- IPC-2221 design guidelines and best practices
- Modular system architecture design
- Power domain separation (analog, digital, power)
- Signal integrity considerations
- Cost-effective design patterns
- Manufacturing-friendly architectures

Design a modular system architecture from requirements following engineering best practices.

Return a JSON object with:
- anchor_block: Dict with type, description, and key specifications of the main component
- child_blocks: List of Dicts for supporting components (power, interfaces, passives, sensors, connectors, etc.)
- dependencies: List of Dicts showing how blocks depend on each other

CRITICAL RULES:
1. If component_count is specified (e.g., 3), create EXACTLY that many distinct blocks:
   - For "3 components" or "simple PCB with 3 parts": Create 3 diverse blocks (e.g., MCU + Sensor + Power Regulator)
   - For "simple PCB": Suggest appropriate mix (MCU + Power + Connector or Sensor + MCU + Interface)
   - Ensure blocks are diverse - don't create 3x MCU unless explicitly requested

2. For simple/generic requests with component_count:
   - Block 1: Main processing unit (MCU, processor, or primary IC)
   - Block 2: Power management (regulator, power supply, or battery management)
   - Block 3+: Supporting components (sensors, connectors, interfaces, passives)

3. Each block should have:
   - type: Component category (mcu, sensor, power, connector, passive, etc.)
   - name: Descriptive name (e.g., "Main MCU", "Power Regulator", "Temperature Sensor")
   - description: What this block does and why it's needed
   - key_specs: Important specifications (voltage, interfaces, power consumption)

4. Follow engineering best practices:
   - Separate power, digital, and analog domains
   - Consider power sequencing and management
   - Include necessary passives (decoupling caps, pull-ups) as separate blocks if component_count allows
   - Ensure interface compatibility between blocks
   - Consider manufacturability (prefer standard packages, avoid exotic components)

5. Ensure all blocks are distinct and serve different purposes (unless quantity of same type is explicitly requested).

6. Consider cost optimization: Suggest cost-effective component choices when constraints allow.

7. Consider supply chain: Prefer components with good availability and active lifecycle status."""

    def design(self, requirements: Requirements) -> Architecture:
        """Design architecture from requirements"""
        try:
            req_dict = requirements.model_dump()
            component_count = req_dict.get("component_count")
            
            # Build enhanced user prompt with component count emphasis
            user_prompt = f"""Design architecture for these requirements:
{requirements.model_dump_json()}

"""
            if component_count:
                user_prompt += f"IMPORTANT: The user requested {component_count} distinct components. Create EXACTLY {component_count} blocks with diverse types (MCU, Sensor, Power, Connector, etc.). Each block should be a different component category unless explicitly requested otherwise."
            else:
                user_prompt += "Design an appropriate architecture based on the functional requirements. Include all necessary supporting components."
            
            response = self._call_llm(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.5
            )
            data = self._parse_json_response(response)
            
            # Post-process to ensure component_count is respected
            if component_count and component_count > 1:
                total_blocks = 1 + len(data.get("child_blocks", []))  # anchor + children
                if total_blocks < component_count:
                    logger.warning(f"Architecture created {total_blocks} blocks but {component_count} requested. Adding generic blocks.")
                    # Add generic blocks to reach component_count
                    existing_types = {data.get("anchor_block", {}).get("type", "").lower()}
                    existing_types.update([b.get("type", "").lower() for b in data.get("child_blocks", [])])
                    
                    generic_blocks = [
                        {"type": "power", "name": "Power Management", "description": "Power regulation and management"},
                        {"type": "connector", "name": "Connector", "description": "External interface connector"},
                        {"type": "sensor", "name": "Sensor", "description": "Environmental or input sensor"},
                        {"type": "passive", "name": "Passive Components", "description": "Resistors, capacitors, inductors"},
                        {"type": "interface", "name": "Interface IC", "description": "Communication interface IC"}
                    ]
                    
                    for block in generic_blocks:
                        if total_blocks >= component_count:
                            break
                        if block["type"] not in existing_types:
                            if "child_blocks" not in data:
                                data["child_blocks"] = []
                            data["child_blocks"].append(block)
                            existing_types.add(block["type"])
                            total_blocks += 1
                            logger.info(f"Added generic {block['type']} block to meet component_count requirement")
            
            return Architecture(**data)
        except Exception as e:
            logger.error(f"Architecture design error: {e}")
            raise RequirementsExtractionError(f"Failed to design architecture: {e}")

