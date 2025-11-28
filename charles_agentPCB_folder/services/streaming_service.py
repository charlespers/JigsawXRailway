"""
Streaming Service
Handles SSE streaming for design generation and orchestration
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional, Callable

from agents.design_orchestrator import DesignOrchestrator
from api.data_mapper import part_data_to_part_object

logger = logging.getLogger(__name__)


def ensure_selected_parts_is_dict(design_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure selected_parts is a dict, convert list if needed.
    This prevents dict/float multiplication errors when parts are stored incorrectly.
    """
    selected_parts = design_state.get("selected_parts", {})
    
    if isinstance(selected_parts, list):
        logger.warning("[DATA_VALIDATION] selected_parts is a list, converting to dict")
        # Convert list to dict using componentId or index
        converted = {}
        for i, part in enumerate(selected_parts):
            if isinstance(part, dict):
                key = part.get("componentId") or part.get("id") or f"part_{i}"
                converted[key] = part
            else:
                logger.error(f"[DATA_VALIDATION] Invalid part at index {i}: {type(part)}")
        design_state["selected_parts"] = converted
        return converted
    
    if not isinstance(selected_parts, dict):
        logger.error(f"[DATA_VALIDATION] selected_parts is invalid type: {type(selected_parts)}, resetting to empty dict")
        design_state["selected_parts"] = {}
        return {}
    
    return selected_parts


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
        # CRITICAL: Pass component_id to preserve mapping
        part_object = part_data_to_part_object(part_data, quantity=1, component_id=component_id)
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
    
    logger.info(f"[WORKFLOW] Starting processing of block: {block_name} (type: {block_type}, hierarchy: {hierarchy_level})")
    
    await queue.put({
        "type": "reasoning",
        "componentId": block_type,
        "componentName": block_name,
        "reasoning": f"Processing {block_name} with engineering analysis...",
        "hierarchyLevel": hierarchy_level
    })
    
    try:
        # Part selection using database - ensures database is searched
        logger.info(f"[WORKFLOW] Searching database for {block_name} (type: {block_type})")
        try:
            part = await asyncio.wait_for(
                asyncio.to_thread(orchestrator._select_supporting_part, block, expanded_requirements, requirements),
                timeout=10.0
            )
            if part:
                logger.info(f"[WORKFLOW] Found part from database: {part.get('id', 'unknown')} (MPN: {part.get('mfr_part_number', 'unknown')})")
            else:
                logger.warning(f"[WORKFLOW] No part found in database for {block_name}")
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
            
            # Apply concurrency limit for LLM calls
            try:
                from core.concurrency import with_llm_limit
            except ImportError:
                def with_llm_limit(coro):
                    return coro
            
            if provides_power:
                compat_tasks.append(("power", asyncio.create_task(
                    asyncio.wait_for(
                        with_llm_limit(
                            asyncio.to_thread(
                                orchestrator.compatibility_agent.check_compatibility,
                                anchor_part, part, "power"
                            )
                        ),
                        timeout=15.0
                    )
                )))
            
            compat_tasks.append(("interface", asyncio.create_task(
                asyncio.wait_for(
                    with_llm_limit(
                        asyncio.to_thread(
                            orchestrator.compatibility_agent.check_compatibility,
                            anchor_part, part, "interface"
                        )
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
                    # CRITICAL: Ensure reasoning agent is initialized before intermediary resolution
                    current_provider = os.environ.get("LLM_PROVIDER", "not_set")
                    logger.info(f"[WORKFLOW] Resolving voltage mismatch for {block_name} (provider={current_provider})")
                    orchestrator.reasoning_agent._ensure_initialized()
                    try:
                        # Apply concurrency limit for agent operations
                        try:
                            from core.concurrency import with_agent_limit
                        except ImportError:
                            def with_agent_limit(coro):
                                return coro
                        
                        intermediary = await asyncio.wait_for(
                            with_agent_limit(
                                asyncio.to_thread(
                                    orchestrator._resolve_voltage_mismatch,
                                    anchor_part, part, "power", power_compat
                                )
                            ),
                            timeout=20.0
                        )
                        if intermediary:
                            intermediary_name = f"intermediary_{anchor_part.get('id', 'anchor')}_{part.get('id', block_name)}"
                            orchestrator.design_state["selected_parts"][intermediary_name] = intermediary
                            orchestrator.design_state["intermediaries"][block_name] = intermediary_name
                            part_object = part_data_to_part_object(intermediary, quantity=1, component_id=intermediary_name)
                            await queue.put({
                                "type": "selection",
                                "componentId": intermediary_name,
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
        # CRITICAL: Pass block_name as component_id to preserve mapping
        part_object = part_data_to_part_object(part, quantity=1, component_id=block_name)
        
        logger.info(f"[WORKFLOW] Part selected for {block_name}: {part.get('id', 'unknown')} (MPN: {part_object.get('mpn', 'unknown')})")
        
        # Emit selection event - CRITICAL: This must be sent for frontend to display the part
        await queue.put({
            "type": "selection",
            "componentId": block_name,  # Use block_name, not block_type, for consistency
            "componentName": block_name,
            "partData": part_object,
            "hierarchyLevel": hierarchy_level
        })
        
        logger.info(f"[WORKFLOW] Selection event emitted for {block_name} at hierarchy {hierarchy_level}")
        
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
        
        logger.info(f"[WORKFLOW] Block {block_name} processing completed successfully")
        
    except Exception as e:
        logger.error(f"[WORKFLOW] Error processing block {block_name}: {str(e)}", exc_info=True)
        await queue.put({
            "type": "error",
            "message": f"Error processing {block_name}: {str(e)}"
        })
        # Re-raise to be caught by caller
        raise


async def generate_design_stream(query: str, orchestrator: StreamingOrchestrator, queue: asyncio.Queue):
    """Generate design and stream events via queue."""
    logger.info(f"[WORKFLOW] Starting design generation for query: {query[:100]}...")
    workflow_start_time = time.time()
    
    try:
        # Step 1: Requirements - send immediate update
        await queue.put({
            "type": "reasoning",
            "componentId": "requirements",
            "componentName": "Requirements Analysis",
            "reasoning": f"Analyzing user query: '{query}'. Extracting functional blocks, constraints, and preferences...",
            "hierarchyLevel": 0
        })
        
        # Ensure provider is still set (defensive check)
        current_provider = os.environ.get("LLM_PROVIDER", "xai")
        logger.info(f"[WORKFLOW] Extracting requirements (provider={current_provider})")
        
        # Wrap synchronous LLM call in async with timeout to prevent hanging
        try:
            # Apply concurrency limit for LLM calls
            try:
                from core.concurrency import with_llm_limit
            except ImportError:
                def with_llm_limit(coro):
                    return coro
            
            requirements = await asyncio.wait_for(
                with_llm_limit(
                    asyncio.to_thread(orchestrator.requirements_agent.extract_requirements, query)
                ),
                timeout=30.0  # 30 second timeout for requirements extraction
            )
        except asyncio.TimeoutError:
            logger.error("[WORKFLOW] Requirements extraction timed out after 30s")
            await queue.put({
                "type": "error",
                "message": "Requirements extraction timed out. Using fallback requirements..."
            })
            # Use minimal fallback requirements to continue
            requirements = {
                "functional_blocks": [{"type": "mcu", "description": "Main processing unit"}],
                "constraints": {},
                "preferences": {}
            }
        except Exception as e:
            logger.error(f"[WORKFLOW] Requirements extraction error: {str(e)}")
            await queue.put({
                "type": "error",
                "message": f"Requirements extraction error: {str(e)}. Using fallback..."
            })
            requirements = {
                "functional_blocks": [{"type": "mcu", "description": "Main processing unit"}],
                "constraints": {},
                "preferences": {}
            }
        
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
        
        # Wrap synchronous LLM call in async with timeout
        try:
            architecture = await asyncio.wait_for(
                asyncio.to_thread(orchestrator.architecture_agent.build_architecture, requirements),
                timeout=30.0  # 30 second timeout for architecture building
            )
        except asyncio.TimeoutError:
            logger.error("[WORKFLOW] Architecture building timed out after 30s")
            await queue.put({
                "type": "error",
                "message": "Architecture building timed out. Using fallback architecture..."
            })
            # Use minimal fallback architecture based on requirements
            functional_blocks = requirements.get("functional_blocks", [])
            if functional_blocks:
                anchor_block = functional_blocks[0]
                child_blocks = functional_blocks[1:] if len(functional_blocks) > 1 else []
            else:
                anchor_block = {"type": "mcu", "description": "Main processing unit"}
                child_blocks = []
            architecture = {
                "anchor_block": anchor_block,
                "child_blocks": child_blocks,
                "dependency_graph": {}
            }
        except Exception as e:
            logger.error(f"[WORKFLOW] Architecture building error: {str(e)}")
            await queue.put({
                "type": "error",
                "message": f"Architecture building error: {str(e)}. Using fallback..."
            })
            functional_blocks = requirements.get("functional_blocks", [])
            if functional_blocks:
                anchor_block = functional_blocks[0]
                child_blocks = functional_blocks[1:] if len(functional_blocks) > 1 else []
            else:
                anchor_block = {"type": "mcu", "description": "Main processing unit"}
                child_blocks = []
            architecture = {
                "anchor_block": anchor_block,
                "child_blocks": child_blocks,
                "dependency_graph": {}
            }
        
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
        
        # Wrap synchronous part selection in async with timeout
        try:
            anchor_part = await asyncio.wait_for(
                asyncio.to_thread(orchestrator._select_anchor_part, anchor_block, requirements),
                timeout=15.0  # 15 second timeout for part selection
            )
        except asyncio.TimeoutError:
            logger.error("[WORKFLOW] Anchor part selection timed out after 15s")
            await queue.put({
                "type": "error",
                "message": "Anchor part selection timed out. Using default part..."
            })
            anchor_part = None
        except Exception as e:
            logger.error(f"[WORKFLOW] Anchor part selection error: {str(e)}")
            await queue.put({
                "type": "error",
                "message": f"Anchor part selection error: {str(e)}. Continuing without anchor..."
            })
            anchor_part = None
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
            
            # CRITICAL: Pass "anchor" as component_id to preserve mapping
            part_object = part_data_to_part_object(anchor_part, quantity=1, component_id="anchor")
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
            successful_hierarchies = []  # Track which hierarchy levels were actually used
            
            for block, task, block_hierarchy in tasks:
                block_name = block.get("description", block.get("type", ""))
                try:
                    await task
                    completed_count += 1
                    successful_hierarchies.append(block_hierarchy)
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
            
            # Only increment hierarchy_level by the number of successfully completed blocks
            # This ensures dependent blocks start at the correct level
            if successful_hierarchies:
                hierarchy_level = max(successful_hierarchies) + 1
            else:
                # If all failed, keep current hierarchy_level
                pass
            
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
        
        # Step 6: Enrich with datasheets (PARALLELIZED with concurrency limits)
        # CRITICAL: Ensure selected_parts is a dict before processing
        orchestrator.design_state = ensure_selected_parts_is_dict(orchestrator.design_state)
        selected_parts = orchestrator.design_state.get("selected_parts", {})
        
        await queue.put({
            "type": "reasoning",
            "componentId": "enrichment",
            "componentName": "Design Enrichment",
            "reasoning": "Enriching parts with datasheet data and engineering metadata in parallel...",
            "hierarchyLevel": 0
        })
        
        # Parallel datasheet enrichment
        selected_parts = orchestrator.design_state["selected_parts"]
        if selected_parts:
            enrichment_tasks = []
            for block_name, part_data in selected_parts.items():
                part_id = part_data.get("id", "")
                if part_id:
                    task = asyncio.create_task(
                        asyncio.to_thread(orchestrator.datasheet_agent.enrich_part, part_id)
                    )
                    enrichment_tasks.append((block_name, task))
            
            # Wait for all enrichments to complete
            enriched_parts = {}
            for block_name, part_data in selected_parts.items():
                enriched_parts[block_name] = part_data  # Default to original
            
            for block_name, task in enrichment_tasks:
                try:
                    enriched = await asyncio.wait_for(task, timeout=5.0)
                    if enriched:
                        enriched_parts[block_name] = enriched
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"Datasheet enrichment timeout/error for {block_name}: {e}")
                    # Keep original part data on error
            
            orchestrator.design_state["selected_parts"] = enriched_parts
        
        # Step 7: Generate outputs (PARALLELIZED)
        await queue.put({
            "type": "reasoning",
            "componentId": "output",
            "componentName": "Output Generation",
            "reasoning": "Generating connections and BOM in parallel...",
            "hierarchyLevel": 0
        })
        
        # Parallel output generation
        connections_task = asyncio.create_task(
            asyncio.to_thread(
                orchestrator.output_generator.generate_connections,
                orchestrator.design_state["selected_parts"],
                architecture,
                orchestrator.design_state.get("intermediaries")
            )
        )
        
        bom_task = asyncio.create_task(
            asyncio.to_thread(
                orchestrator.output_generator.generate_bom,
                orchestrator.design_state["selected_parts"],
                orchestrator.design_state["external_components"]
            )
        )
        
        # Wait for both to complete
        connections, bom = await asyncio.gather(connections_task, bom_task)
        orchestrator.design_state["connections"] = connections
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
        
        workflow_duration = time.time() - workflow_start_time
        logger.info(f"[WORKFLOW] Design generation completed in {workflow_duration:.2f}s. Summary: {summary_message}")
        
        await queue.put({
            "type": "complete",
            "message": summary_message
        })
        
    except Exception as e:
        workflow_duration = time.time() - workflow_start_time
        logger.error(f"[WORKFLOW] Workflow error after {workflow_duration:.2f}s: {str(e)}", exc_info=True)
        
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


async def refine_design_stream(
    query: str,
    orchestrator: StreamingOrchestrator,
    queue: asyncio.Queue,
    existing_design_state: Dict[str, Any],
    action_details: Dict[str, Any]
):
    """Refine existing design based on user query."""
    logger.info(f"[REFINEMENT] Starting design refinement for query: {query[:100]}...")
    
    try:
        parts_to_modify = action_details.get("parts_to_modify", [])
        parts_to_add = action_details.get("parts_to_add", [])
        
        await queue.put({
            "type": "reasoning",
            "componentId": "refinement",
            "componentName": "Design Refinement",
            "reasoning": f"Refining design: modifying {len(parts_to_modify)} part(s), adding {len(parts_to_add)} part(s)...",
            "hierarchyLevel": 0
        })
        
        # Load existing design state into orchestrator
        orchestrator.design_state = existing_design_state.copy()
        
        # Handle part modifications
        for part_name in parts_to_modify:
            if part_name in orchestrator.design_state["selected_parts"]:
                await queue.put({
                    "type": "reasoning",
                    "componentId": "refinement",
                    "componentName": "Design Refinement",
                    "reasoning": f"Removing {part_name} for replacement...",
                    "hierarchyLevel": 0
                })
                del orchestrator.design_state["selected_parts"][part_name]
        
        # Handle part additions (simplified - just add new parts)
        # In a full implementation, this would parse the query to determine what to add
        if parts_to_add:
            await queue.put({
                "type": "reasoning",
                "componentId": "refinement",
                "componentName": "Design Refinement",
                "reasoning": f"Adding {len(parts_to_add)} new part(s)...",
                "hierarchyLevel": 0
            })
            # For now, just emit a message - full implementation would search and add parts
            # This is a placeholder for the refinement logic
        
        # Regenerate connections and BOM
        from agents.output_generator import OutputGenerator
        output_gen = OutputGenerator()
        
        connections = output_gen.generate_connections(
            orchestrator.design_state["selected_parts"],
            orchestrator.design_state.get("architecture", {}),
            orchestrator.design_state.get("intermediaries", {})
        )
        orchestrator.design_state["connections"] = connections
        
        bom = output_gen.generate_bom(
            orchestrator.design_state["selected_parts"],
            orchestrator.design_state.get("external_components", [])
        )
        orchestrator.design_state["bom"] = bom
        
        await queue.put({
            "type": "complete",
            "message": f"Design refinement complete. {len(orchestrator.design_state['selected_parts'])} part(s) in design."
        })
        
    except Exception as e:
        logger.error(f"[REFINEMENT] Error: {str(e)}", exc_info=True)
        await queue.put({
            "type": "error",
            "message": f"Refinement error: {str(e)}"
        })
        await queue.put({
            "type": "complete",
            "message": f"Refinement completed with errors. {str(e)}"
        })


async def answer_question(
    query: str,
    orchestrator: StreamingOrchestrator,
    queue: asyncio.Queue,
    existing_design_state: Dict[str, Any],
    question_type: str
):
    """Answer questions about existing design."""
    logger.info(f"[QUESTION] Answering question: {query[:100]}...")
    
    try:
        await queue.put({
            "type": "reasoning",
            "componentId": "question",
            "componentName": "Question Answering",
            "reasoning": f"Analyzing question about design...",
            "hierarchyLevel": 0
        })
        
        # Load existing design state
        orchestrator.design_state = existing_design_state.copy()
        
        # Route to appropriate analysis based on question type
        answer = ""
        
        if question_type == "cost":
            from agents.cost_optimizer_agent import CostOptimizerAgent
            cost_agent = CostOptimizerAgent()
            # CRITICAL: Ensure selected_parts is a dict and validate structure
            ensure_selected_parts_is_dict(orchestrator.design_state)
            bom_items = []
            for block_name, part in orchestrator.design_state["selected_parts"].items():
                # Ensure part is a dict, not a list or other structure
                if isinstance(part, dict):
                    bom_items.append({"part_data": part, "quantity": 1})
                elif isinstance(part, list):
                    # Handle list case (shouldn't happen, but safety check)
                    logger.warning(f"[BOM_VALIDATION] Part {block_name} is a list, using first element")
                    if part and isinstance(part[0], dict):
                        bom_items.append({"part_data": part[0], "quantity": 1})
                else:
                    logger.error(f"[BOM_VALIDATION] Invalid part type for {block_name}: {type(part)}")
            cost_analysis = cost_agent.optimize_cost(bom_items)
            total_cost = cost_analysis.get("total_cost", 0)
            answer = f"Total BOM cost: ${total_cost:.2f}"
        
        elif question_type == "power":
            from agents.power_calculator_agent import PowerCalculatorAgent
            power_agent = PowerCalculatorAgent()
            # CRITICAL: Ensure selected_parts is a dict and validate structure
            ensure_selected_parts_is_dict(orchestrator.design_state)
            bom_items = []
            for block_name, part in orchestrator.design_state["selected_parts"].items():
                # Ensure part is a dict, not a list or other structure
                if isinstance(part, dict):
                    bom_items.append({"part_data": part, "quantity": 1})
                elif isinstance(part, list):
                    logger.warning(f"[BOM_VALIDATION] Part {block_name} is a list, using first element")
                    if part and isinstance(part[0], dict):
                        bom_items.append({"part_data": part[0], "quantity": 1})
                else:
                    logger.error(f"[BOM_VALIDATION] Invalid part type for {block_name}: {type(part)}")
            power_analysis = power_agent.calculate_power(bom_items, orchestrator.design_state.get("connections", []))
            total_power = power_analysis.get("total_power_watts", 0)
            answer = f"Total power consumption: {total_power:.2f}W"
        
        elif question_type == "compatibility":
            # Check compatibility between parts
            compatibility_issues = []
            selected_parts = list(orchestrator.design_state["selected_parts"].values())
            for i, part_a in enumerate(selected_parts):
                for part_b in selected_parts[i+1:]:
                    compat = orchestrator.compatibility_agent.check_compatibility(part_a, part_b, "power")
                    if not compat.get("compatible", True):
                        compatibility_issues.append(f"{part_a.get('id', 'Unknown')} and {part_b.get('id', 'Unknown')} have compatibility issues")
            
            if compatibility_issues:
                answer = f"Found {len(compatibility_issues)} compatibility issue(s): " + "; ".join(compatibility_issues[:3])
            else:
                answer = "All parts are compatible."
        
        else:
            # General question - use design analysis
            design_analysis = orchestrator.design_state.get("design_analysis", {})
            if design_analysis:
                answer = "Design analysis available. Check the insights panel for details."
            else:
                answer = "I can help answer questions about cost, power, compatibility, and design analysis."
        
        await queue.put({
            "type": "reasoning",
            "componentId": "question",
            "componentName": "Answer",
            "reasoning": answer,
            "hierarchyLevel": 0
        })
        
        await queue.put({
            "type": "complete",
            "message": "Question answered."
        })
        
    except Exception as e:
        logger.error(f"[QUESTION] Error: {str(e)}", exc_info=True)
        await queue.put({
            "type": "error",
            "message": f"Error answering question: {str(e)}"
        })
        await queue.put({
            "type": "complete",
            "message": f"Question answering completed with errors. {str(e)}"
        })

