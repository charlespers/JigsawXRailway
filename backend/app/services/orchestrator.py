"""
Design orchestrator service
Coordinates all agents to generate complete PCB design
"""
import logging
from typing import Dict, Any
from app.agents.requirements import RequirementsAgent
from app.agents.architecture import ArchitectureAgent
from app.agents.part_selection import PartSelectionAgent
from app.agents.compatibility import CompatibilityAgent
from app.agents.bom_generator import BOMGenerator
from app.domain.models import Design, Requirements, Architecture
from app.core.exceptions import PCBDesignException

logger = logging.getLogger(__name__)


class DesignOrchestrator:
    """Orchestrates the complete PCB design generation process"""
    
    def __init__(self):
        self.requirements_agent = RequirementsAgent()
        self.architecture_agent = ArchitectureAgent()
        self.part_selection_agent = PartSelectionAgent()
        self.compatibility_agent = CompatibilityAgent()
        self.bom_generator = BOMGenerator()
    
    def generate_design(self, query: str) -> Design:
        """
        Generate complete PCB design from user query
        
        Args:
            query: Natural language description (e.g., "temperature sensor with WiFi and USB-C")
        
        Returns:
            Complete Design with requirements, architecture, parts, connections, and BOM
        """
        try:
            # Step 1: Extract requirements
            logger.info(f"Extracting requirements from query: {query}")
            requirements = self.requirements_agent.extract(query)
            
            # Step 2: Design architecture
            logger.info("Designing system architecture")
            architecture = self.architecture_agent.design(requirements)
            
            # Step 3: Select anchor part
            logger.info("Selecting anchor part")
            anchor_block_dict = architecture.anchor_block if isinstance(architecture.anchor_block, dict) else architecture.anchor_block.model_dump()
            anchor_part = self.part_selection_agent.select_anchor_part(
                anchor_block_dict,
                requirements.model_dump()
            )
            
            if not anchor_part:
                raise PCBDesignException("Failed to select anchor part")
            
            selected_parts = {"anchor": anchor_part}
            
            # Step 4: Select supporting parts
            logger.info("Selecting supporting parts")
            supporting_parts = self.part_selection_agent.select_supporting_parts(
                anchor_part,
                architecture.child_blocks,
                requirements.model_dump()
            )
            selected_parts.update(supporting_parts)
            
            # Step 5: Check compatibility
            logger.info("Checking part compatibility")
            for part_name, part in selected_parts.items():
                if part_name != "anchor":
                    compat = self.compatibility_agent.check_compatibility(
                        anchor_part,
                        part,
                        "power" if "power" in part_name.lower() else "signal"
                    )
                    if not compat["compatible"]:
                        logger.warning(f"Compatibility issues for {part_name}: {compat['issues']}")
            
            # Step 6: Generate connections
            logger.info("Generating netlist connections")
            connections = self.bom_generator.generate_connections(
                selected_parts,
                architecture.model_dump()
            )
            
            # Step 7: Generate BOM
            logger.info("Generating BOM")
            bom = self.bom_generator.generate(selected_parts, connections)
            
            # Create complete design (parts remain as dicts for flexibility)
            design = Design(
                requirements=requirements,
                architecture=architecture,
                selected_parts=selected_parts,
                connections=connections,
                bom=bom,
                design_metadata={
                    "query": query,
                    "total_components": len(selected_parts)
                }
            )
            
            logger.info(f"Design generation complete: {len(selected_parts)} parts, {len(connections)} nets")
            return design
            
        except Exception as e:
            logger.error(f"Design generation error: {e}", exc_info=True)
            raise PCBDesignException(f"Failed to generate design: {e}")

