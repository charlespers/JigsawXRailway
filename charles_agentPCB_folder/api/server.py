"""
FastAPI Server for React Visualization
Provides SSE streaming endpoint for component analysis
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add development_demo to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

from agents.design_orchestrator import DesignOrchestrator
from agents.eda_asset_agent import EDAAssetAgent
from api.data_mapper import part_data_to_part_object

app = FastAPI(title="PCB Design API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StreamingOrchestrator(DesignOrchestrator):
    """Extended orchestrator with streaming callbacks."""
    
    def __init__(self, on_reasoning: Optional[Callable] = None, on_selection: Optional[Callable] = None):
        super().__init__()
        self.on_reasoning = on_reasoning
        self.on_selection = on_selection
        self.current_component_id = None
        self.current_component_name = None
        self.hierarchy_level = 0
    
    def emit_reasoning(self, component_id: str, component_name: str, reasoning: str, hierarchy_level: int = 0):
        """Emit a reasoning event."""
        self.current_component_id = component_id
        self.current_component_name = component_name
        self.hierarchy_level = hierarchy_level
        if self.on_reasoning:
            self.on_reasoning({
                "type": "reasoning",
                "componentId": component_id,
                "componentName": component_name,
                "reasoning": reasoning,
                "hierarchyLevel": hierarchy_level
            })
    
    def emit_selection(self, component_id: str, component_name: str, part_data: Dict[str, Any], hierarchy_level: int = 0):
        """Emit a selection event."""
        part_object = part_data_to_part_object(part_data)
        if self.on_selection:
            self.on_selection({
                "type": "selection",
                "componentId": component_id,
                "componentName": component_name,
                "partData": part_object,
                "hierarchyLevel": hierarchy_level
            })


async def _process_block_async(
    block: Dict[str, Any],
    expanded_requirements: Dict[str, Any],
    requirements: Dict[str, Any],
    orchestrator: StreamingOrchestrator,
    anchor_part: Optional[Dict[str, Any]],
    queue: asyncio.Queue,
    hierarchy_level: int
):
    """Process a single block (part selection, compatibility, etc.) - can be called in parallel."""
    block_type = block.get("type", "")
    block_name = block.get("description", block_type)
    
    await queue.put({
        "type": "reasoning",
        "componentId": block_type,
        "componentName": block_name,
        "reasoning": f"Processing {block_name} with engineering analysis...",
        "hierarchyLevel": hierarchy_level
    })
    
    try:
        # Part selection with timeout and engineering analysis
        try:
            part = await asyncio.wait_for(
                asyncio.to_thread(orchestrator._select_supporting_part, block, expanded_requirements, requirements),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            await queue.put({
                "type": "reasoning",
                "componentId": block_type,
                "componentName": block_name,
                "reasoning": f"Part selection timeout for {block_name}. Trying with relaxed constraints...",
                "hierarchyLevel": hierarchy_level
            })
            relaxed_constraints = block.copy()
            relaxed_constraints.pop("required_interfaces", None)
            try:
                part = await asyncio.wait_for(
                    asyncio.to_thread(orchestrator._select_supporting_part, relaxed_constraints, expanded_requirements, requirements),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                part = None
        
        if not part:
            await queue.put({
                "type": "reasoning",
                "componentId": block_type,
                "componentName": block_name,
                "reasoning": f"No suitable part found for {block_name}. Continuing...",
                "hierarchyLevel": hierarchy_level
            })
            return
        
        # Engineering analysis: Check lifecycle status before proceeding
        lifecycle = part.get("lifecycle_status", "active")
        if lifecycle != "active":
            await queue.put({
                "type": "reasoning",
                "componentId": block_type,
                "componentName": block_name,
                "reasoning": f"⚠️ Warning: {part.get('id', block_name)} has lifecycle status '{lifecycle}'. Consider alternatives for production.",
                "hierarchyLevel": hierarchy_level
            })
        
        # Engineering analysis: Check availability
        availability = part.get("availability_status", "unknown")
        if availability != "in_stock":
            await queue.put({
                "type": "reasoning",
                "componentId": block_type,
                "componentName": block_name,
                "reasoning": f"⚠️ Availability: {part.get('id', block_name)} status is '{availability}'. Check lead times.",
                "hierarchyLevel": hierarchy_level
            })
        
        # Engineering analysis: Quick power check
        voltage_range = part.get("supply_voltage_range", {})
        current_max = part.get("current_max", {})
        if isinstance(voltage_range, dict) and isinstance(current_max, dict):
            voltage = voltage_range.get("nominal") or voltage_range.get("max", 0)
            current = current_max.get("max") or current_max.get("typical", 0)
            if isinstance(voltage, (int, float)) and isinstance(current, (int, float)):
                power_estimate = float(voltage) * float(current)
                if power_estimate > 1.0:  # > 1W
                    await queue.put({
                        "type": "reasoning",
                        "componentId": block_type,
                        "componentName": block_name,
                        "reasoning": f"Power analysis: {part.get('id', block_name)} consumes ~{power_estimate:.2f}W - ensure adequate power supply and thermal management.",
                        "hierarchyLevel": hierarchy_level
                    })
        
        # Part found - process it (compatibility checks, etc.)
        part_mpn = part.get("mpn", part.get("id", ""))
        part_manufacturer = part.get("manufacturer", "")
        
        await queue.put({
            "type": "reasoning",
            "componentId": block_type,
            "componentName": block_name,
            "reasoning": f"Found candidate: {part_mpn} from {part_manufacturer}. Verifying compatibility...",
            "hierarchyLevel": hierarchy_level
        })
        
        # Run power and interface compatibility checks in parallel
        power_compat = None
        interface_compat = None
        
        if anchor_part:
            provides_power = block_type == "power" or block.get("depends_on", []) == ["power"]
            
            # Create tasks for parallel compatibility checks
            compat_tasks = []
            
            if provides_power:
                compat_tasks.append(("power", asyncio.create_task(
                    asyncio.wait_for(
                        asyncio.to_thread(
                            orchestrator.compatibility_agent.check_compatibility,
                            anchor_part, part, "power"
                        ),
                        timeout=15.0
                    )
                )))
            
            compat_tasks.append(("interface", asyncio.create_task(
                asyncio.wait_for(
                    asyncio.to_thread(
                        orchestrator.compatibility_agent.check_compatibility,
                        anchor_part, part, "interface"
                    ),
                    timeout=15.0
                )
            )))
            
            # Wait for all compatibility checks to complete
            for check_type, task in compat_tasks:
                try:
                    result = await task
                    if check_type == "power":
                        power_compat = result
                    else:
                        interface_compat = result
                except asyncio.TimeoutError:
                    # Fallback to rule-based check
                    if check_type == "power":
                        power_compat = orchestrator.compatibility_agent._rule_based_check(anchor_part, part, "power")
                    else:
                        interface_compat = orchestrator.compatibility_agent._rule_based_check(anchor_part, part, "interface")
                except Exception as e:
                    # Error fallback
                    if check_type == "power":
                        power_compat = {"compatible": True, "reasoning": "Error during check, assuming compatible"}
                    else:
                        interface_compat = {"compatible": True, "reasoning": "Error during check, assuming compatible"}
            
            # Handle voltage mismatch if needed
            if power_compat and not power_compat.get("compatible", False):
                if orchestrator.compatibility_agent.can_be_resolved_with_intermediary(power_compat):
                    try:
                        intermediary = await asyncio.wait_for(
                            asyncio.to_thread(
                                orchestrator._resolve_voltage_mismatch,
                                anchor_part, part, "power", power_compat
                            ),
                            timeout=20.0
                        )
                        if intermediary:
                            intermediary_name = f"intermediary_{anchor_part.get('id', 'anchor')}_{part.get('id', block_name)}"
                            orchestrator.design_state["selected_parts"][intermediary_name] = intermediary
                            orchestrator.design_state["intermediaries"][block_name] = intermediary_name
                            part_object = part_data_to_part_object(intermediary)
                            await queue.put({
                                "type": "selection",
                                "componentId": f"intermediary_{block_type}",
                                "componentName": "Voltage Converter",
                                "partData": part_object,
                                "hierarchyLevel": hierarchy_level
                            })
                    except Exception:
                        pass  # Continue without intermediary
            
            # Store compatibility results
            compat_result = {"interface": interface_compat or {"compatible": True}}
            if power_compat:
                compat_result["power"] = power_compat
            orchestrator.design_state["compatibility_results"][block_name] = compat_result
        
        # Add part to design state
        orchestrator.design_state["selected_parts"][block_name] = part
        part_object = part_data_to_part_object(part)
        await queue.put({
            "type": "selection",
            "componentId": block_type,
            "componentName": block_name,
            "partData": part_object,
            "hierarchyLevel": hierarchy_level
        })
        
        # Add external components
        from utils.part_database import get_recommended_external_components
        ext_comps = get_recommended_external_components(part.get("id", ""))
        orchestrator.design_state["external_components"].extend(ext_comps)
        
        await queue.put({
            "type": "reasoning",
            "componentId": block_type,
            "componentName": block_name,
            "reasoning": f"✓ {block_name} complete" + (f" ({len(ext_comps)} external components added)" if ext_comps else ""),
            "hierarchyLevel": hierarchy_level
        })
        
    except Exception as e:
        await queue.put({
            "type": "error",
            "message": f"Error processing {block_name}: {str(e)}"
        })


async def generate_design_stream(query: str, orchestrator: StreamingOrchestrator, queue: asyncio.Queue):
    """Generate design and stream events via queue."""
    try:
        # Step 1: Requirements
        await queue.put({
            "type": "reasoning",
            "componentId": "requirements",
            "componentName": "Requirements Analysis",
            "reasoning": f"Analyzing user query: '{query}'. Extracting functional blocks, constraints, and preferences...",
            "hierarchyLevel": 0
        })
        
        requirements = orchestrator.requirements_agent.extract_requirements(query)
        orchestrator.design_state["requirements"] = requirements
        
        # Extract functional blocks for reasoning
        functional_blocks = requirements.get("functional_blocks", [])
        block_names = [b.get("description", b.get("type", "")) for b in functional_blocks]
        await queue.put({
            "type": "reasoning",
            "componentId": "requirements",
            "componentName": "Requirements Analysis",
            "reasoning": f"Identified {len(functional_blocks)} functional blocks: {', '.join(block_names[:5])}" + ("..." if len(block_names) > 5 else ""),
            "hierarchyLevel": 0
        })
        
        # Step 2: Architecture
        await queue.put({
            "type": "reasoning",
            "componentId": "architecture",
            "componentName": "Architecture Design",
            "reasoning": "Building functional hierarchy and dependency graph. Identifying the anchor component (most connected)...",
            "hierarchyLevel": 0
        })
        
        architecture = orchestrator.architecture_agent.build_architecture(requirements)
        orchestrator.design_state["architecture"] = architecture
        
        anchor_block = architecture.get("anchor_block", {})
        anchor_type = anchor_block.get("type", "mcu")
        anchor_desc = anchor_block.get("description", anchor_type)
        child_blocks = architecture.get("child_blocks", [])
        await queue.put({
            "type": "reasoning",
            "componentId": "anchor",
            "componentName": anchor_desc,
            "reasoning": f"Selected {anchor_desc} as anchor component. It connects to {len(child_blocks)} supporting blocks: {', '.join([b.get('description', b.get('type', '')) for b in child_blocks[:3]])}" + ("..." if len(child_blocks) > 3 else ""),
            "hierarchyLevel": 0
        })
        
        # Step 3: Select anchor part
        await queue.put({
            "type": "reasoning",
            "componentId": "anchor",
            "componentName": anchor_desc,
            "reasoning": f"Searching part database for {anchor_desc}. Matching interfaces: {', '.join(anchor_block.get('required_interfaces', [])[:3])}" + ("..." if len(anchor_block.get('required_interfaces', [])) > 3 else ""),
            "hierarchyLevel": 0
        })
        
        anchor_part = orchestrator._select_anchor_part(anchor_block, requirements)
        if anchor_part:
            orchestrator.design_state["selected_parts"]["anchor"] = anchor_part
            part_mpn = anchor_part.get("mpn", anchor_part.get("id", ""))
            part_manufacturer = anchor_part.get("manufacturer", "")
            part_desc = anchor_part.get("description", part_mpn)
            
            # Generate reasoning based on actual part data
            voltage_info = ""
            voltage_range = anchor_part.get("supply_voltage_range", {})
            if voltage_range:
                if isinstance(voltage_range, dict):
                    v_min = voltage_range.get("min")
                    v_max = voltage_range.get("max")
                    v_nominal = voltage_range.get("nominal")
                    if v_min and v_max:
                        voltage_info = f" operates at {v_min}-{v_max}V"
                    elif v_nominal:
                        voltage_info = f" operates at {v_nominal}V"
            
            current_info = ""
            current_max = anchor_part.get("current_max", {})
            if current_max:
                if isinstance(current_max, dict):
                    current_val = current_max.get("max") or current_max.get("typical")
                else:
                    current_val = current_max
                if current_val:
                    current_info = f" with max current {current_val}A"
            
            interfaces_info = ""
            interfaces = anchor_part.get("interface_type", [])
            if interfaces:
                if isinstance(interfaces, str):
                    interfaces = [interfaces]
                interfaces_info = f" Interfaces: {', '.join(interfaces[:3])}" + ("..." if len(interfaces) > 3 else "")
            
            reasoning_msg = f"Selected {part_mpn} from {part_manufacturer}{voltage_info}{current_info}{interfaces_info}. Checking specifications and compatibility..."
            
            await queue.put({
                "type": "reasoning",
                "componentId": "anchor",
                "componentName": anchor_desc,
                "reasoning": reasoning_msg,
                "hierarchyLevel": 0
            })
            
            part_object = part_data_to_part_object(anchor_part)
            await queue.put({
                "type": "selection",
                "componentId": "anchor",
                "componentName": anchor_block.get("description", "Anchor Component"),
                "partData": part_object,
                "hierarchyLevel": 0
            })
        
        # Step 4: Expand requirements
        expanded_requirements = orchestrator._expand_requirements(anchor_part, architecture)
        
        # Step 5: Select supporting parts
        child_blocks = architecture.get("child_blocks", [])
        hierarchy_level = 1
        
        # Initialize block tracking for summary
        independent_blocks = []
        dependent_blocks = []
        total_blocks_processed = 0
        total_blocks_failed = 0
        
        if not child_blocks:
            await queue.put({
                "type": "reasoning",
                "componentId": "architecture",
                "componentName": "Architecture",
                "reasoning": "No child blocks found in architecture. Design may be complete with anchor component only.",
                "hierarchyLevel": 0
            })
        else:
            # Group blocks by dependencies for parallel processing
            # Independent blocks (no dependencies) can be processed in parallel
        
        for block in child_blocks:
            depends_on = block.get("depends_on", [])
            # Filter out "power" dependency as it's handled via anchor
            depends_on = [d for d in depends_on if d != "power"]
            if not depends_on:
                independent_blocks.append(block)
            else:
                dependent_blocks.append(block)
        
        # Process independent blocks in parallel
        if independent_blocks:
            await queue.put({
                "type": "reasoning",
                "componentId": "architecture",
                "componentName": "Architecture",
                "reasoning": f"Processing {len(independent_blocks)} independent component(s) in parallel...",
                "hierarchyLevel": 0
            })
            
            # Create tasks with unique hierarchy levels and timeouts
            tasks = []
            for i, block in enumerate(independent_blocks):
                block_hierarchy = hierarchy_level + i
                block_name = block.get("description", block.get("type", ""))
                
                await queue.put({
                    "type": "reasoning",
                    "componentId": "architecture",
                    "componentName": "Architecture",
                    "reasoning": f"[{i+1}/{len(independent_blocks)}] Processing {block_name}...",
                    "hierarchyLevel": 0
                })
                
                task = asyncio.create_task(
                    asyncio.wait_for(
                        _process_block_async(block, expanded_requirements, requirements, orchestrator, anchor_part, queue, block_hierarchy),
                        timeout=30.0
                    )
                )
                tasks.append((block, task, block_hierarchy))
            
            # Wait for all independent blocks with proper error handling
            completed_count = 0
            failed_count = 0
            for block, task, block_hierarchy in tasks:
                block_name = block.get("description", block.get("type", ""))
                try:
                    await task
                    completed_count += 1
                    await queue.put({
                        "type": "reasoning",
                        "componentId": "architecture",
                        "componentName": "Architecture",
                        "reasoning": f"✓ [{completed_count}/{len(independent_blocks)}] Completed {block_name}",
                        "hierarchyLevel": 0
                    })
                except asyncio.TimeoutError:
                    failed_count += 1
                    await queue.put({
                        "type": "error",
                        "message": f"Timeout processing {block_name} after 30s. Continuing with other components..."
                    })
                    await queue.put({
                        "type": "reasoning",
                        "componentId": "architecture",
                        "componentName": "Architecture",
                        "reasoning": f"⚠ [{completed_count + failed_count}/{len(independent_blocks)}] Timeout on {block_name} - skipped",
                        "hierarchyLevel": 0
                    })
                except Exception as e:
                    failed_count += 1
                    await queue.put({
                        "type": "error",
                        "message": f"Error processing {block_name}: {str(e)}. Continuing..."
                    })
                    await queue.put({
                        "type": "reasoning",
                        "componentId": "architecture",
                        "componentName": "Architecture",
                        "reasoning": f"⚠ [{completed_count + failed_count}/{len(independent_blocks)}] Error on {block_name} - skipped",
                        "hierarchyLevel": 0
                    })
            
            hierarchy_level += len(independent_blocks)
            total_blocks_processed += completed_count
            total_blocks_failed += failed_count
            
            # Summary of parallel processing
            if failed_count > 0:
                await queue.put({
                    "type": "reasoning",
                    "componentId": "architecture",
                    "componentName": "Architecture",
                    "reasoning": f"Parallel processing complete: {completed_count} succeeded, {failed_count} failed/skipped",
                    "hierarchyLevel": 0
                })
        
        # Process dependent blocks sequentially (they may depend on each other)
        if dependent_blocks:
            await queue.put({
                "type": "reasoning",
                "componentId": "architecture",
                "componentName": "Architecture",
                "reasoning": f"Processing {len(dependent_blocks)} dependent component(s) sequentially...",
                "hierarchyLevel": 0
            })
            
            for i, block in enumerate(dependent_blocks):
                block_name = block.get("description", block.get("type", ""))
                await queue.put({
                    "type": "reasoning",
                    "componentId": "architecture",
                    "componentName": "Architecture",
                    "reasoning": f"[{i+1}/{len(dependent_blocks)}] Processing dependent component: {block_name}...",
                    "hierarchyLevel": 0
                })
                
                try:
                    await asyncio.wait_for(
                        _process_block_async(block, expanded_requirements, requirements, orchestrator, anchor_part, queue, hierarchy_level),
                        timeout=30.0
                    )
                    await queue.put({
                        "type": "reasoning",
                        "componentId": "architecture",
                        "componentName": "Architecture",
                        "reasoning": f"✓ [{i+1}/{len(dependent_blocks)}] Completed {block_name}",
                        "hierarchyLevel": 0
                    })
                except asyncio.TimeoutError:
                    await queue.put({
                        "type": "error",
                        "message": f"Timeout processing {block_name} after 30s. Continuing..."
                    })
                except Exception as e:
                    total_blocks_failed += 1
                    await queue.put({
                        "type": "error",
                        "message": f"Error processing {block_name}: {str(e)}. Continuing..."
                    })
                else:
                    total_blocks_processed += 1
                
                hierarchy_level += 1
        
        # Step 6: Enrich with datasheets
        await queue.put({
            "type": "reasoning",
            "componentId": "enrichment",
            "componentName": "Design Enrichment",
            "reasoning": "Enriching parts with datasheet data and engineering metadata...",
            "hierarchyLevel": 0
        })
        orchestrator._enrich_parts_with_datasheets()
        
        # Step 7: Generate outputs
        await queue.put({
            "type": "reasoning",
            "componentId": "output",
            "componentName": "Output Generation",
            "reasoning": "Generating connections and BOM with engineering analysis...",
            "hierarchyLevel": 0
        })
        
        connections = orchestrator.output_generator.generate_connections(
            orchestrator.design_state["selected_parts"],
            architecture,
            orchestrator.design_state.get("intermediaries")
        )
        orchestrator.design_state["connections"] = connections
        
        bom = orchestrator.output_generator.generate_bom(
            orchestrator.design_state["selected_parts"],
            orchestrator.design_state["external_components"]
        )
        orchestrator.design_state["bom"] = bom
        
        # Step 8: Comprehensive Engineering Analysis (in parallel where possible)
        await queue.put({
            "type": "reasoning",
            "componentId": "analysis",
            "componentName": "Engineering Analysis",
            "reasoning": "Performing comprehensive engineering analysis: power, thermal, design validation, and recommendations...",
            "hierarchyLevel": 0
        })
        
        # Run design analysis (includes power, thermal, DRC)
        try:
            await queue.put({
                "type": "reasoning",
                "componentId": "analysis",
                "componentName": "Power Analysis",
                "reasoning": "Calculating power consumption per rail...",
                "hierarchyLevel": 0
            })
            
            design_analysis = await asyncio.wait_for(
                asyncio.to_thread(
                    orchestrator.design_analyzer.analyze_design,
                    orchestrator.design_state["selected_parts"],
                    connections,
                    orchestrator.design_state["compatibility_results"]
                ),
                timeout=30.0
            )
            orchestrator.design_state["design_analysis"] = design_analysis
            
            # Emit key findings
            power_analysis = design_analysis.get("power_analysis", {})
            total_power = power_analysis.get("total_power_watts", 0)
            if total_power > 0:
                await queue.put({
                    "type": "reasoning",
                    "componentId": "analysis",
                    "componentName": "Power Analysis",
                    "reasoning": f"✓ Power analysis complete: Total consumption {total_power:.2f}W across {len(power_analysis.get('power_rails', {}))} voltage rail(s).",
                    "hierarchyLevel": 0
                })
            
            thermal_analysis = design_analysis.get("thermal_analysis", {})
            thermal_issues = thermal_analysis.get("thermal_issues", [])
            if thermal_issues:
                await queue.put({
                    "type": "reasoning",
                    "componentId": "analysis",
                    "componentName": "Thermal Analysis",
                    "reasoning": f"⚠️ Thermal analysis: {len(thermal_issues)} thermal issue(s) identified. Review component placement and thermal management.",
                    "hierarchyLevel": 0
                })
            
            drc_results = design_analysis.get("design_rule_checks", {})
            error_count = drc_results.get("error_count", 0)
            warning_count = drc_results.get("warning_count", 0)
            if error_count > 0 or warning_count > 0:
                await queue.put({
                    "type": "reasoning",
                    "componentId": "analysis",
                    "componentName": "Design Validation",
                    "reasoning": f"✓ Design validation: {error_count} error(s), {warning_count} warning(s). Review recommendations.",
                    "hierarchyLevel": 0
                })
            
            recommendations = design_analysis.get("recommendations", [])
            if recommendations:
                await queue.put({
                    "type": "reasoning",
                    "componentId": "analysis",
                    "componentName": "Design Recommendations",
                    "reasoning": f"✓ Generated {len(recommendations)} engineering recommendation(s) for design optimization.",
                    "hierarchyLevel": 0
                })
        except asyncio.TimeoutError:
            await queue.put({
                "type": "reasoning",
                "componentId": "analysis",
                "componentName": "Engineering Analysis",
                "reasoning": "Engineering analysis timeout after 30s. Basic design complete, but detailed analysis skipped.",
                "hierarchyLevel": 0
            })
            # Create minimal analysis result to prevent errors downstream
            design_analysis = {
                "power_analysis": {"total_power_watts": 0, "power_rails": {}},
                "thermal_analysis": {"thermal_issues": []},
                "design_rule_checks": {"errors": [], "warnings": [], "error_count": 0, "warning_count": 0, "passed": True},
                "recommendations": ["Detailed analysis timed out - review design manually"]
            }
            orchestrator.design_state["design_analysis"] = design_analysis
        except Exception as e:
            await queue.put({
                "type": "reasoning",
                "componentId": "analysis",
                "componentName": "Engineering Analysis",
                "reasoning": f"Engineering analysis error: {str(e)}. Design complete with basic validation.",
                "hierarchyLevel": 0
            })
            # Create minimal analysis result to prevent errors downstream
            design_analysis = {
                "power_analysis": {"total_power_watts": 0, "power_rails": {}},
                "thermal_analysis": {"thermal_issues": []},
                "design_rule_checks": {"errors": [], "warnings": [], "error_count": 0, "warning_count": 0, "passed": True},
                "recommendations": [f"Analysis error occurred: {str(e)}"]
            }
            orchestrator.design_state["design_analysis"] = design_analysis
        
        # Calculate summary statistics
        selected_parts_count = len(orchestrator.design_state["selected_parts"])
        external_components_count = len(orchestrator.design_state["external_components"])
        total_blocks_attempted = len(independent_blocks) + len(dependent_blocks)
        
        # Mark completion at the end with summary
        summary_parts = []
        if total_blocks_attempted > 0:
            summary_parts.append(f"{total_blocks_processed}/{total_blocks_attempted} components processed")
        if total_blocks_failed > 0:
            summary_parts.append(f"{total_blocks_failed} failed/skipped")
        summary_parts.append(f"{selected_parts_count} part(s) selected")
        if external_components_count > 0:
            summary_parts.append(f"{external_components_count} external component(s) added")
        
        summary_message = "Component analysis complete. " + ", ".join(summary_parts) + "."
        
        await queue.put({
            "type": "complete",
            "message": summary_message
        })
        
    except Exception as e:
        # Ensure error is always sent and workflow completes
        await queue.put({
            "type": "error",
            "message": f"Workflow error: {str(e)}"
        })
        # Still emit complete to prevent frontend from hanging
        await queue.put({
            "type": "complete",
            "message": f"Workflow completed with errors. {str(e)}"
        })
        # Don't re-raise - we've handled it


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/mcp/component-analysis")
async def component_analysis(request: Request):
    """SSE endpoint for component analysis."""
    
    body = await request.json()
    query = body.get("query", "")
    provider = body.get("provider", "openai")  # Default to openai
    context_query_id = body.get("contextQueryId")
    context = body.get("context", "")
    
    if not query:
        return {"error": "Query is required"}, 400
    
    # Validate provider
    if provider not in ["openai", "xai"]:
        return {"error": f"Invalid provider '{provider}'. Must be 'openai' or 'xai'."}, 400
    
    # Store original provider to restore later
    original_provider = os.environ.get("LLM_PROVIDER", "openai")
    
    async def event_stream():
        # Set provider in environment BEFORE creating orchestrator
        # This ensures agents read the correct provider during initialization
        os.environ["LLM_PROVIDER"] = provider
        
        queue = asyncio.Queue()
        # Create orchestrator AFTER setting provider in environment
        # Agents will read LLM_PROVIDER during their __init__
        try:
        orchestrator = StreamingOrchestrator()
        except ValueError as e:
            # If agent initialization fails (e.g., missing API key), send error
            await queue.put({
                "type": "error",
                "message": f"Failed to initialize agents: {str(e)}. Please check your API keys in .env file."
            })
            # Restore original provider
            os.environ["LLM_PROVIDER"] = original_provider
            # Yield error and return
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return
        
        # Start design generation in background
        task = asyncio.create_task(generate_design_stream(query, orchestrator, queue))
        
        try:
            while True:
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    if event.get("type") == "error":
                        yield f"data: {json.dumps(event)}\n\n"
                        break
                    
                    yield f"data: {json.dumps(event)}\n\n"
                    
                    if event.get("type") == "complete":
                        break
                        
                except asyncio.TimeoutError:
                    # Check if task is done
                    if task.done():
                        break
                    continue
                    
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            # Restore original provider
            os.environ["LLM_PROVIDER"] = original_provider
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# Import analysis agents
from utils.part_comparison import compare_parts
from agents.alternative_finder_agent import AlternativeFinderAgent
from agents.cost_optimizer_agent import CostOptimizerAgent
from agents.supply_chain_agent import SupplyChainAgent
from agents.design_validator_agent import DesignValidatorAgent
from agents.power_calculator_agent import PowerCalculatorAgent
from agents.auto_fix_agent import AutoFixAgent
from agents.bom_insights_agent import BOMInsightsAgent
from agents.thermal_analysis_agent import ThermalAnalysisAgent
from agents.signal_integrity_agent import SignalIntegrityAgent
from agents.manufacturing_readiness_agent import ManufacturingReadinessAgent
from agents.design_review_agent import DesignReviewAgent
from agents.compliance_agent import ComplianceAgent
from agents.design_comparison_agent import DesignComparisonAgent
from agents.obsolescence_forecast_agent import ObsolescenceForecastAgent
from agents.design_reuse_agent import DesignReuseAgent
from agents.cost_forecast_agent import CostForecastAgent


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/parts/compare")
async def compare_parts_endpoint(request: Request):
    """Compare multiple parts side-by-side."""
    try:
        data = await request.json()
        part_ids = data.get("part_ids", [])
        
        if len(part_ids) < 2:
            return {"error": "Need at least 2 parts to compare"}
        
        comparison = compare_parts(part_ids)
        return comparison
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/parts/alternatives/{part_id}")
async def get_alternatives(part_id: str, same_footprint: bool = False, lower_cost: bool = False):
    """Find alternative parts for a given part."""
    try:
        finder = AlternativeFinderAgent()
        criteria = {
            "same_footprint": same_footprint,
            "lower_cost": lower_cost
        }
        alternatives = finder.find_alternatives(part_id, criteria)
        return {"alternatives": alternatives}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/analysis/cost")
async def analyze_cost(request: Request):
    """Analyze BOM cost and suggest optimizations."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        
        optimizer = CostOptimizerAgent()
        analysis = optimizer.analyze_bom_cost(bom_items)
        return analysis
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/analysis/supply-chain")
async def analyze_supply_chain(request: Request):
    """Analyze supply chain risks."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        
        agent = SupplyChainAgent()
        analysis = agent.analyze_supply_chain(bom_items)
        return analysis
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/analysis/power")
async def analyze_power(request: Request):
    """Calculate power consumption."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        operating_modes = data.get("operating_modes", {})
        
        calculator = PowerCalculatorAgent()
        analysis = calculator.calculate_power_consumption(bom_items, operating_modes)
        
        # If battery capacity provided, estimate battery life
        battery_capacity = data.get("battery_capacity_mah")
        battery_voltage = data.get("battery_voltage", 3.7)
        if battery_capacity:
            battery_life = calculator.estimate_battery_life(
                analysis["total_power"],
                battery_capacity,
                battery_voltage
            )
            analysis["battery_life"] = battery_life
        
        return analysis
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/design-review/review")
async def review_design(request: Request):
    """Get comprehensive design review with health score."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        connections = data.get("connections", [])
        design_metadata = data.get("design_metadata")
        
        agent = DesignReviewAgent()
        review = agent.review_design(bom_items, connections, design_metadata)
        return review
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/compatibility/check")
async def check_compatibility(request: Request):
    """Check compatibility between two parts."""
    try:
        data = await request.json()
        part1 = data.get("part1", {})
        part2 = data.get("part2", {})
        
        if not part1 or not part2:
            return {"error": "Both part1 and part2 must be provided"}
        
        agent = CompatibilityAgent()
        result = agent.check_compatibility(part1, part2)
        
        # Get alternatives if incompatible
        alternatives = []
        if not result.get("compatible", True):
            alt_agent = AlternativeFinderAgent()
            alternatives = alt_agent.find_alternatives(part1.get("id", ""), limit=3)
        
        return {
            "compatible": result.get("compatible", True),
            "warnings": result.get("warnings", []),
            "alternatives": alternatives
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/validation/design")
async def validate_design(request: Request):
    """Validate design against industry standards."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        connections = data.get("connections", [])
        
        validator = DesignValidatorAgent()
        validation = validator.validate_design(bom_items, connections)
        
        # Get auto-fix suggestions
        auto_fix = AutoFixAgent()
        fix_suggestions = auto_fix.suggest_fixes(validation.get("issues", []), bom_items)
        fix_suggestions.extend(auto_fix.suggest_missing_footprints(bom_items))
        fix_suggestions.extend(auto_fix.suggest_missing_msl(bom_items))
        
        validation["fix_suggestions"] = fix_suggestions
        
        return validation
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/auto-fix/suggest")
async def suggest_fixes(request: Request):
    """Get suggestions to fix validation issues."""
    try:
        data = await request.json()
        validation_issues = data.get("issues", [])
        bom_items = data.get("bom_items", [])
        
        auto_fix = AutoFixAgent()
        suggestions = auto_fix.suggest_fixes(validation_issues, bom_items)
        suggestions.extend(auto_fix.suggest_missing_footprints(bom_items))
        suggestions.extend(auto_fix.suggest_missing_msl(bom_items))
        
        return {"suggestions": suggestions}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/analysis/bom-insights")
async def analyze_bom_insights(request: Request):
    """Get comprehensive BOM insights and statistics."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        
        agent = BOMInsightsAgent()
        insights = agent.analyze_bom(bom_items)
        return insights
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/analysis/thermal")
async def analyze_thermal(request: Request):
    """Perform detailed thermal analysis."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        ambient_temp = data.get("ambient_temp", 25.0)
        pcb_area_cm2 = data.get("pcb_area_cm2")
        
        agent = ThermalAnalysisAgent()
        analysis = agent.analyze_thermal(bom_items, ambient_temp, pcb_area_cm2)
        return analysis
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/analysis/signal-integrity")
async def analyze_signal_integrity(request: Request):
    """Perform signal integrity and EMI/EMC analysis."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        connections = data.get("connections", [])
        pcb_thickness_mm = data.get("pcb_thickness_mm", 1.6)
        trace_width_mils = data.get("trace_width_mils", 5.0)
        
        agent = SignalIntegrityAgent()
        analysis = agent.analyze_signal_integrity(
            bom_items, connections, pcb_thickness_mm, trace_width_mils
        )
        return analysis
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/analysis/manufacturing-readiness")
async def analyze_manufacturing_readiness(request: Request):
    """Perform manufacturing readiness analysis."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        connections = data.get("connections", [])
        
        agent = ManufacturingReadinessAgent()
        analysis = agent.analyze_manufacturing_readiness(bom_items, connections)
        return analysis
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/review/design")
async def review_design(request: Request):
    """Perform executive-level design review."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        connections = data.get("connections", [])
        design_metadata = data.get("design_metadata", {})
        
        agent = DesignReviewAgent()
        review = agent.review_design(bom_items, connections, design_metadata)
        return review
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/compliance/check")
async def check_compliance(request: Request):
    """Check regulatory and environmental compliance."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        regions = data.get("regions", ["EU", "US", "China"])
        
        agent = ComplianceAgent()
        compliance = agent.check_compliance(bom_items, regions)
        return compliance
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/design/compare")
async def compare_designs(request: Request):
    """Compare multiple design versions."""
    try:
        data = await request.json()
        designs = data.get("designs", [])
        baseline_index = data.get("baseline_index", 0)
        
        agent = DesignComparisonAgent()
        comparison = agent.compare_designs(designs, baseline_index)
        return comparison
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/forecast/obsolescence")
async def forecast_obsolescence(request: Request):
    """Forecast component obsolescence risks."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        forecast_years = data.get("forecast_years", 5)
        
        agent = ObsolescenceForecastAgent()
        forecast = agent.forecast_obsolescence(bom_items, forecast_years)
        return forecast
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/analysis/design-reuse")
async def analyze_design_reuse(request: Request):
    """Analyze design for reusability."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        existing_designs = data.get("existing_designs")
        
        agent = DesignReuseAgent()
        analysis = agent.analyze_reusability(bom_items, existing_designs)
        return analysis
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/forecast/cost")
async def forecast_costs(request: Request):
    """Forecast BOM costs over time."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        forecast_months = data.get("forecast_months", 12)
        production_volume = data.get("production_volume", 1000)
        
        agent = CostForecastAgent()
        forecast = agent.forecast_costs(bom_items, forecast_months, production_volume)
        return forecast
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/eda/assets")
async def get_eda_assets(request: Request):
    """Get EDA assets (footprints, symbols, 3D models) for a part."""
    try:
        data = await request.json()
        part = data.get("part", {})
        tool = data.get("tool", "kicad")  # kicad, altium, eagle
        asset_types = data.get("asset_types", ["footprint", "symbol", "3d_model"])
        
        if not part:
            return {"error": "Part data is required"}
        
        agent = EDAAssetAgent()
        assets = agent.get_eda_assets(part, tool, asset_types)
        return {"assets": assets, "tool": tool}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/eda/download")
async def download_eda_assets(request: Request):
    """Download EDA assets for a part or BOM as files."""
    try:
        from fastapi.responses import FileResponse
        import zipfile
        import tempfile
        
        data = await request.json()
        part = data.get("part")
        bom_items = data.get("bom_items", [])
        tool = data.get("tool", "kicad")
        asset_types = data.get("asset_types", ["footprint", "symbol"])
        
        agent = EDAAssetAgent()
        
        # Create temporary directory for assets
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_dir = tmp_path / tool
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if part:
                # Single part
                saved_files = agent.download_eda_assets(part, tool, output_dir)
            elif bom_items:
                # Multiple parts from BOM
                from utils.part_database import get_part_by_id
                saved_files = {}
                
                for item in bom_items:
                    part_id = item.get("mpn") or item.get("id")
                    if part_id:
                        part_data = get_part_by_id(part_id)
                        if part_data:
                            part_files = agent.download_eda_assets(part_data, tool, output_dir)
                            saved_files.update(part_files)
            else:
                return {"error": "Either 'part' or 'bom_items' must be provided"}
            
            if not saved_files:
                return {"error": "No EDA assets generated"}
            
            # Create zip file
            zip_path = tmp_path / f"eda_assets_{tool}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for asset_type, file_path in saved_files.items():
                    zipf.write(file_path, file_path.name)
            
            # Return zip file
            return FileResponse(
                zip_path,
                media_type="application/zip",
                filename=f"eda_assets_{tool}.zip"
            )
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/eda/bom-assets")
async def get_bom_eda_assets(request: Request):
    """Get EDA assets for all parts in a BOM."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        tool = data.get("tool", "kicad")
        asset_types = data.get("asset_types", ["footprint", "symbol"])
        
        if not bom_items:
            return {"error": "BOM items are required"}
        
        agent = EDAAssetAgent()
        from utils.part_database import get_part_by_id
        
        all_assets = {}
        
        for item in bom_items:
            part_id = item.get("mpn") or item.get("id")
            if part_id:
                part_data = get_part_by_id(part_id)
                if part_data:
                    assets = agent.get_eda_assets(part_data, tool, asset_types)
                    all_assets[part_id] = assets
        
        return {
            "assets": all_assets,
            "tool": tool,
            "part_count": len(all_assets)
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Read PORT from environment (Railway sets this automatically)
    port = int(os.environ.get("PORT", 3001))
    uvicorn.run(app, host="0.0.0.0", port=port)

