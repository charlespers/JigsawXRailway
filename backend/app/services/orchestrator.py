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
from app.agents.power_analyzer import PowerAnalyzerAgent
from app.agents.dfm_checker import DFMCheckerAgent
from app.agents.supply_chain_intelligence import SupplyChainIntelligenceAgent
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
        self.power_analyzer = PowerAnalyzerAgent()
        self.dfm_checker = DFMCheckerAgent()
        self.supply_chain = SupplyChainIntelligenceAgent()
    
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
                # Check if database is empty
                from app.domain.part_database import get_part_database
                db = get_part_database()
                all_parts = db.get_all_parts()
                if len(all_parts) == 0:
                    raise PCBDesignException(
                        "Parts database is empty. No parts available for selection. "
                        "Please ensure app/data/parts/*.json files are deployed."
                    )
                raise PCBDesignException("Failed to select anchor part - no matching parts found in database")
            
            selected_parts = {"anchor": anchor_part}
            
            # Step 4: Select supporting parts
            logger.info("Selecting supporting parts")
            supporting_parts = self.part_selection_agent.select_supporting_parts(
                anchor_part,
                architecture.child_blocks,
                requirements.model_dump()
            )
            selected_parts.update(supporting_parts)
            
            # Validate component count if specified
            component_count = requirements.component_count
            if component_count and component_count > 0:
                total_selected = len(selected_parts)
                if total_selected < component_count:
                    logger.warning(
                        f"Selected {total_selected} parts but {component_count} requested. "
                        f"Architecture created {len(architecture.child_blocks)} child blocks."
                    )
                elif total_selected > component_count:
                    logger.info(
                        f"Selected {total_selected} parts (more than requested {component_count}). "
                        "This is acceptable as supporting components were added."
                    )
                else:
                    logger.info(f"Successfully selected {total_selected} parts matching component_count requirement")
            
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
            
            # Step 8: Power analysis
            logger.info("Analyzing power budget")
            power_analysis = self.power_analyzer.analyze_power_budget(selected_parts)
            design.design_metadata["power_analysis"] = power_analysis
            
            # Step 9: DFM check
            logger.info("Checking manufacturability")
            dfm_analysis = self.dfm_checker.check_design(bom, selected_parts)
            design.design_metadata["dfm_analysis"] = dfm_analysis
            
            # Step 10: Supply chain analysis
            logger.info("Analyzing supply chain")
            supply_chain_analysis = self.supply_chain.analyze_supply_chain(selected_parts, bom.model_dump())
            design.design_metadata["supply_chain_analysis"] = supply_chain_analysis
            
            logger.info(f"Design generation complete: {len(selected_parts)} parts, {len(connections)} nets")
            logger.info(f"Power budget: {power_analysis['total_power_watts']}W, DFM score: {dfm_analysis['dfm_score']}/100")
            logger.info(f"Supply chain risk: {supply_chain_analysis['overall_risk']}")
            return design
            
        except Exception as e:
            logger.error(f"Design generation error: {e}", exc_info=True)
            raise PCBDesignException(f"Failed to generate design: {e}")

