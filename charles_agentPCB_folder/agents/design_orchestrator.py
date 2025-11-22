"""
Design Orchestrator
Coordinates all agents through the 7-step design process
"""

from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.requirements_agent import RequirementsAgent
from agents.architecture_agent import ArchitectureAgent
from agents.part_search_agent import PartSearchAgent
from agents.compatibility_agent import CompatibilityAgent
from agents.datasheet_agent import DatasheetAgent
from agents.output_generator import OutputGenerator
from agents.intermediary_agent import IntermediaryAgent
from agents.reasoning_agent import ReasoningAgent
from agents.design_analyzer import DesignAnalyzer
from utils.part_database import get_recommended_external_components


class DesignOrchestrator:
    """Orchestrates the complete design generation process."""
    
    def __init__(self):
        self.requirements_agent = RequirementsAgent()
        self.architecture_agent = ArchitectureAgent()
        self.part_search_agent = PartSearchAgent()
        self.compatibility_agent = CompatibilityAgent()
        self.datasheet_agent = DatasheetAgent()
        self.output_generator = OutputGenerator()
        self.intermediary_agent = IntermediaryAgent()
        self.reasoning_agent = ReasoningAgent()
        self.design_analyzer = DesignAnalyzer()
        
        self.design_state = {
            "requirements": None,
            "architecture": None,
            "selected_parts": {},
            "external_components": [],
            "compatibility_results": {},
            "intermediaries": {},  # Track added intermediaries
            "connections": [],
            "bom": {},
            "design_analysis": {}
        }
    
    def generate_design(self, query: str) -> Dict[str, Any]:
        """
        Generate a complete PCB design from a natural language query.
        
        Args:
            query: Natural language description (e.g., "temperature sensor with wifi and 5V-USBC")
        
        Returns:
            Complete design with architecture, parts, connections, and BOM
        """
        try:
            # Step 1: Extract requirements
            requirements = self.requirements_agent.extract_requirements(query)
            self.design_state["requirements"] = requirements
            
            # Step 2: Build architecture
            architecture = self.architecture_agent.build_architecture(requirements)
            self.design_state["architecture"] = architecture
            
            # Step 3: Select anchor part
            anchor_block = architecture.get("anchor_block", {})
            anchor_part = self._select_anchor_part(anchor_block, requirements)
            if anchor_part:
                self.design_state["selected_parts"]["anchor"] = anchor_part
            
            # Step 4: Expand requirements around anchor
            expanded_requirements = self._expand_requirements(anchor_part, architecture)
            
            # Step 5: Select supporting parts with compatibility checks
            child_blocks = architecture.get("child_blocks", [])
            for block in child_blocks:
                block_type = block.get("type", "")
                block_name = block.get("description", block_type)
                
                # Search for parts matching this block
                part = self._select_supporting_part(block, expanded_requirements, requirements)
                if part:
                    # Check compatibility with anchor
                    if anchor_part:
                        # Determine if anchor provides power to this part
                        # (typically only for power blocks or when explicitly connected)
                        provides_power = block_type == "power" or block.get("depends_on", []) == ["power"]
                        
                        power_compat = None
                        if provides_power:
                            # Check power compatibility
                            power_compat = self.compatibility_agent.check_compatibility(
                                anchor_part, part, connection_type="power"
                            )
                            
                            # If power compatibility fails due to voltage mismatch, try to resolve
                            if not power_compat.get("compatible", False):
                                if self.compatibility_agent.can_be_resolved_with_intermediary(power_compat):
                                    # Try to resolve voltage mismatch with intermediary
                                    intermediary = self._resolve_voltage_mismatch(
                                        anchor_part, part, "power", power_compat
                                    )
                                    if intermediary:
                                        # Add intermediary to design
                                        intermediary_name = f"intermediary_{anchor_part.get('id', 'anchor')}_{part.get('id', block_name)}"
                                        self.design_state["selected_parts"][intermediary_name] = intermediary
                                        self.design_state["intermediaries"][block_name] = intermediary_name
                                        
                                        # Re-check compatibility through intermediary
                                        compat_via_intermediary = self.compatibility_agent.check_compatibility(
                                            intermediary, part, connection_type="power"
                                        )
                                        if compat_via_intermediary.get("compatible", False):
                                            # Add external components for intermediary
                                            ext_comps = get_recommended_external_components(intermediary.get("id", ""))
                                            self.design_state["external_components"].extend(ext_comps)
                                        else:
                                            # Still incompatible even with intermediary
                                            continue
                                    else:
                                        # Could not find suitable intermediary
                                        continue
                                else:
                                    # Incompatibility cannot be resolved with intermediary
                                    continue
                        
                        # Check interface compatibility (for communication interfaces)
                        interface_compat = self.compatibility_agent.check_compatibility(
                            anchor_part, part, connection_type="interface"
                        )
                        
                        # Store compatibility results
                        compat_result = {"interface": interface_compat}
                        if power_compat:
                            compat_result["power"] = power_compat
                        self.design_state["compatibility_results"][block_name] = compat_result
                        
                        # Check interface compatibility
                        if not interface_compat.get("compatible", False):
                            # Interface mismatch - try to resolve if it's a voltage level issue
                            if "level_shifter" in interface_compat.get("required_buffers", []):
                                # Try to find level shifter
                                # Get IO voltage levels
                                anchor_io = anchor_part.get("io_voltage_levels", {})
                                target_io = part.get("io_voltage_levels", {})
                                anchor_voltage = anchor_io.get("logic_high_min") or anchor_io.get("nominal", 3.3)
                                target_voltage = target_io.get("logic_high_min") or target_io.get("nominal", 5.0)
                                
                                voltage_gap = {
                                    "source_voltage": anchor_voltage,
                                    "target_min": target_voltage - 0.5,
                                    "target_max": target_voltage + 0.5,
                                    "target_nominal": target_voltage
                                }
                                level_shifters = self.intermediary_agent.find_intermediary(
                                    anchor_part, part, "signal", voltage_gap
                                )
                                if level_shifters:
                                    # Use first level shifter
                                    level_shifter = level_shifters[0]
                                    intermediary_name = f"level_shifter_{anchor_part.get('id', 'anchor')}_{part.get('id', block_name)}"
                                    self.design_state["selected_parts"][intermediary_name] = level_shifter
                                    self.design_state["intermediaries"][f"{block_name}_signal"] = intermediary_name
                            else:
                                # Other interface incompatibility - skip
                                continue
                    
                    self.design_state["selected_parts"][block_name] = part
                    
                    # Add external components from application template
                    ext_comps = get_recommended_external_components(part.get("id", ""))
                    self.design_state["external_components"].extend(ext_comps)
            
            # Step 6: Use datasheet data for missing fields
            self._enrich_parts_with_datasheets()
            
            # Step 7: Generate outputs
            connections = self.output_generator.generate_connections(
                self.design_state["selected_parts"],
                architecture,
                self.design_state.get("intermediaries")
            )
            self.design_state["connections"] = connections
            
            bom = self.output_generator.generate_bom(
                self.design_state["selected_parts"],
                self.design_state["external_components"],
                connections  # Pass connections for test point generation
            )
            self.design_state["bom"] = bom
            
            # Perform design analysis
            design_analysis = self.design_analyzer.analyze_design(
                self.design_state["selected_parts"],
                connections,
                self.design_state["compatibility_results"]
            )
            self.design_state["design_analysis"] = design_analysis
            
            return {
                "query": query,
                "requirements": requirements,
                "architecture": architecture,
                "selected_parts": self.design_state["selected_parts"],
                "external_components": self.design_state["external_components"],
                "compatibility_results": self.design_state["compatibility_results"],
                "intermediaries": self.design_state["intermediaries"],
                "connections": connections,
                "bom": bom,
                "design_analysis": design_analysis
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "query": query,
                "design_state": self.design_state
            }
    
    def _select_anchor_part(
        self,
        anchor_block: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Select the anchor part (most connected component)."""
        block_type = anchor_block.get("type", "")
        required_interfaces = anchor_block.get("required_interfaces", [])
        
        # Build search constraints
        constraints = {
            "interface_type": required_interfaces,
            "lifecycle_status": "active",
            "availability_status": "in_stock"
        }
        
        # Add voltage constraint if specified
        if "constraints" in requirements:
            req_constraints = requirements["constraints"]
            if "voltage" in req_constraints:
                voltage = req_constraints["voltage"]
                if "outputs" in voltage:
                    output_volts = voltage["outputs"]
                    if output_volts:
                        # Use first output voltage
                        volt_str = output_volts[0]
                        volt_value = float(volt_str.replace("V", ""))
                        constraints["supply_voltage_range"] = {
                            "nominal": volt_value
                        }
        
        preferences = requirements.get("preferences", {})
        
        # Search and rank
        ranked = self.part_search_agent.search_and_rank(
            category=block_type,
            constraints=constraints,
            preferences=preferences
        )
        
        if ranked:
            return ranked[0]["part"]
        return None
    
    def _expand_requirements(
        self,
        anchor_part: Optional[Dict[str, Any]],
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Expand requirements based on selected anchor part."""
        expanded = {}
        
        if not anchor_part:
            return expanded
        
        # Get anchor's power requirements
        supply_voltage = anchor_part.get("supply_voltage_range", {})
        if supply_voltage:
            expanded["power_output_voltage"] = supply_voltage.get("nominal") or supply_voltage.get("value")
        
        # Get anchor's current requirements
        current_max = anchor_part.get("current_max", {})
        if isinstance(current_max, dict):
            expanded["power_output_current_min"] = current_max.get("max") or current_max.get("typical", 0)
        else:
            expanded["power_output_current_min"] = current_max or 0
        
        # Add margin (typically 20-30%)
        if "power_output_current_min" in expanded:
            expanded["power_output_current_min"] *= 1.3
        
        # Get anchor's interfaces
        interfaces = anchor_part.get("interface_type", [])
        if isinstance(interfaces, str):
            interfaces = [interfaces]
        expanded["available_interfaces"] = interfaces
        
        return expanded
    
    def _select_supporting_part(
        self,
        block: Dict[str, Any],
        expanded_requirements: Dict[str, Any],
        original_requirements: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Select a supporting part for a child block."""
        block_type = block.get("type", "")
        
        # Map block types to part categories
        category_map = {
            "power": "regulator_ldo",
            "sensor": "sensor_temperature",
            "connector": "connector_usb_c",
            "debug": "connector"
        }
        
        category = category_map.get(block_type, block_type)
        
        # Build constraints
        constraints = {
            "lifecycle_status": "active",
            "availability_status": "in_stock"
        }
        
        # Add interface constraint
        required_interfaces = block.get("required_interfaces", [])
        if required_interfaces:
            constraints["interface_type"] = required_interfaces
        
        # Add voltage constraints
        if block_type == "power":
            # Power block needs specific input/output voltages
            constraints["supply_voltage_range"] = {
                "min": 4.5,
                "max": 15.0
            }
            # Output voltage from expanded requirements
            if "power_output_voltage" in expanded_requirements:
                # This will be checked in compatibility, not search
                pass
        
        preferences = original_requirements.get("preferences", {})
        
        # Search and rank
        ranked = self.part_search_agent.search_and_rank(
            category=category,
            constraints=constraints,
            preferences=preferences
        )
        
        if not ranked:
            return None
        
        # Engineering analysis: Evaluate top candidates with engineering criteria
        # Score candidates based on multiple engineering factors
        scored_candidates = []
        for candidate in ranked[:5]:  # Evaluate top 5 candidates
            part = candidate["part"]
            score = candidate.get("score", 0.0)
            
            # Engineering scoring factors
            # 1. Lifecycle status (prefer active)
            lifecycle = part.get("lifecycle_status", "unknown")
            if lifecycle == "active":
                score += 20
            elif lifecycle in ["eol", "obsolete", "nrnd"]:
                score -= 50
            
            # 2. Availability (prefer in stock)
            availability = part.get("availability_status", "unknown")
            if availability == "in_stock":
                score += 15
            elif availability in ["limited", "backorder"]:
                score -= 10
            
            # 3. Power efficiency (lower power is better for battery applications)
            voltage_range = part.get("supply_voltage_range", {})
            current_max = part.get("current_max", {})
            if isinstance(voltage_range, dict) and isinstance(current_max, dict):
                voltage = voltage_range.get("nominal") or voltage_range.get("max", 0)
                current = current_max.get("typical") or current_max.get("max", 0)
                if isinstance(voltage, (int, float)) and isinstance(current, (int, float)):
                    power = float(voltage) * float(current)
                    # Lower power gets bonus (for battery-powered designs)
                    if power < 0.1:  # < 100mW
                        score += 10
                    elif power > 1.0:  # > 1W
                        score -= 5
            
            # 4. Package preference (SMT preferred for modern designs)
            package = part.get("package", "").upper()
            if any(pkg in package for pkg in ["QFN", "QFP", "SOT", "0603", "0805", "1206"]):
                score += 5
            elif "DIP" in package or "THROUGH" in package:
                score -= 5  # Through-hole is less preferred
            
            # 5. Thermal characteristics (lower thermal resistance is better)
            thermal_resistance = part.get("thermal_resistance", {})
            if isinstance(thermal_resistance, dict):
                theta_ja = thermal_resistance.get("theta_ja") or thermal_resistance.get("junction_to_ambient")
                if theta_ja and isinstance(theta_ja, (int, float)):
                    if theta_ja < 50:  # Good thermal performance
                        score += 5
                    elif theta_ja > 100:  # Poor thermal performance
                        score -= 5
            
            # 6. Cost consideration (prefer lower cost if available)
            cost_estimate = part.get("cost_estimate", {})
            if isinstance(cost_estimate, dict):
                cost = cost_estimate.get("value") or cost_estimate.get("unit", 0)
                if isinstance(cost, (int, float)):
                    if cost < 1.0:  # Low cost
                        score += 5
                    elif cost > 10.0:  # High cost
                        score -= 5
            
            # 7. Documentation quality (parts with recommended external components are better)
            if part.get("recommended_external_components"):
                score += 10
            
            scored_candidates.append({
                "part": part,
                "score": score
            })
        
        # Sort by engineering score (highest first)
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Return best engineering candidate
        if scored_candidates:
            return scored_candidates[0]["part"]
        
        # Fallback to original ranking
        return ranked[0]["part"]
    
    def _enrich_parts_with_datasheets(self):
        """Enrich all selected parts with datasheet data."""
        enriched_parts = {}
        for block_name, part_data in self.design_state["selected_parts"].items():
            part_id = part_data.get("id", "")
            if part_id:
                enriched = self.datasheet_agent.enrich_part(part_id)
                if enriched:
                    enriched_parts[block_name] = enriched
                else:
                    enriched_parts[block_name] = part_data
            else:
                enriched_parts[block_name] = part_data
        
        self.design_state["selected_parts"] = enriched_parts
    
    def _resolve_voltage_mismatch(
        self,
        source_part: Dict[str, Any],
        target_part: Dict[str, Any],
        connection_type: str,
        compat_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve voltage mismatch by finding and evaluating intermediary components.
        
        Args:
            source_part: Source component
            target_part: Target component
            connection_type: "power" or "signal"
            compat_result: Compatibility check result with voltage_gap
        
        Returns:
            Selected intermediary part, or None if no suitable intermediary found
        """
        voltage_gap = compat_result.get("voltage_gap")
        if not voltage_gap:
            return None
        
        # Find candidate intermediaries
        candidates = self.intermediary_agent.find_intermediary(
            source_part, target_part, connection_type, voltage_gap
        )
        
        if not candidates:
            return None
        
        # Evaluate each candidate
        best_candidate = None
        best_score = -1.0
        
        for candidate in candidates[:5]:  # Evaluate top 5 candidates
            feasibility = self.reasoning_agent.evaluate_intermediary_feasibility(
                source_part, candidate, target_part
            )
            
            if feasibility.get("feasible", False):
                score = feasibility.get("feasibility_score", 0.0)
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
        
        return best_candidate
    
    def _get_output_voltage(self, part: Dict[str, Any]) -> Optional[float]:
        """Extract output voltage from part."""
        output_voltage = part.get("output_voltage")
        if output_voltage:
            if isinstance(output_voltage, dict):
                return output_voltage.get("nominal") or output_voltage.get("value")
            return float(output_voltage)
        
        # Try supply voltage range
        supply_range = part.get("supply_voltage_range")
        if supply_range:
            return supply_range.get("nominal") or supply_range.get("value")
        
        return None

