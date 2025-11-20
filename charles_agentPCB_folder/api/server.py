"""
FastAPI Server for React Visualization
Provides SSE streaming endpoint for component analysis
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add development_demo to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.design_orchestrator import DesignOrchestrator
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
        await asyncio.sleep(0.1)
        
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
        await asyncio.sleep(0.1)
        
        # Step 2: Architecture
        await queue.put({
            "type": "reasoning",
            "componentId": "architecture",
            "componentName": "Architecture Design",
            "reasoning": "Building functional hierarchy and dependency graph. Identifying the anchor component (most connected)...",
            "hierarchyLevel": 0
        })
        await asyncio.sleep(0.1)
        
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
        await asyncio.sleep(0.1)
        
        # Step 3: Select anchor part
        await queue.put({
            "type": "reasoning",
            "componentId": "anchor",
            "componentName": anchor_desc,
            "reasoning": f"Searching part database for {anchor_desc}. Matching interfaces: {', '.join(anchor_block.get('required_interfaces', [])[:3])}" + ("..." if len(anchor_block.get('required_interfaces', [])) > 3 else ""),
            "hierarchyLevel": 0
        })
        await asyncio.sleep(0.1)
        
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
            await asyncio.sleep(0.1)
            
            part_object = part_data_to_part_object(anchor_part)
            await queue.put({
                "type": "selection",
                "componentId": "anchor",
                "componentName": anchor_block.get("description", "Anchor Component"),
                "partData": part_object,
                "hierarchyLevel": 0
            })
            await asyncio.sleep(0.1)
        
        # Step 4: Expand requirements
        expanded_requirements = orchestrator._expand_requirements(anchor_part, architecture)
        
        # Step 5: Select supporting parts
        child_blocks = architecture.get("child_blocks", [])
        hierarchy_level = 1
        
        for block in child_blocks:
            block_type = block.get("type", "")
            block_name = block.get("description", block_type)
            
            # Get constraints for this block
            constraints = architecture.get("constraints_per_block", {}).get(block_type, {})
            required_interfaces = block.get("required_interfaces", [])
            
            await queue.put({
                "type": "reasoning",
                "componentId": block_type,
                "componentName": block_name,
                "reasoning": f"Searching part database for {block_name}. Requirements: {', '.join(required_interfaces[:2])}" + (f" and {len(required_interfaces)-2} more" if len(required_interfaces) > 2 else ""),
                "hierarchyLevel": hierarchy_level
            })
            await asyncio.sleep(0.1)
            
            part = orchestrator._select_supporting_part(block, expanded_requirements, requirements)
            if part:
                part_mpn = part.get("mpn", part.get("id", ""))
                part_manufacturer = part.get("manufacturer", "")
                part_desc = part.get("description", part_mpn)
                
                # Generate reasoning based on actual part data from database
                voltage_info = ""
                voltage_range = part.get("supply_voltage_range", {})
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
                current_max = part.get("current_max", {})
                if current_max:
                    if isinstance(current_max, dict):
                        current_val = current_max.get("max") or current_max.get("typical")
                    else:
                        current_val = current_max
                    if current_val:
                        current_info = f" with max current {current_val}A"
                
                interfaces_info = ""
                interfaces = part.get("interface_type", [])
                if interfaces:
                    if isinstance(interfaces, str):
                        interfaces = [interfaces]
                    interfaces_info = f" Interfaces: {', '.join(interfaces[:3])}" + ("..." if len(interfaces) > 3 else "")
                
                reasoning_msg = f"Found candidate: {part_mpn} from {part_manufacturer}{voltage_info}{current_info}{interfaces_info}. Verifying compatibility with anchor component..."
                
                await queue.put({
                    "type": "reasoning",
                    "componentId": block_type,
                    "componentName": block_name,
                    "reasoning": reasoning_msg,
                    "hierarchyLevel": hierarchy_level
                })
                await asyncio.sleep(0.1)
                # Check compatibility
                if anchor_part:
                    provides_power = block_type == "power" or block.get("depends_on", []) == ["power"]
                    
                    if provides_power:
                        power_compat = orchestrator.compatibility_agent.check_compatibility(
                            anchor_part, part, connection_type="power"
                        )
                        
                        if not power_compat.get("compatible", False):
                            if orchestrator.compatibility_agent.can_be_resolved_with_intermediary(power_compat):
                                await queue.put({
                                    "type": "reasoning",
                                    "componentId": block_type,
                                    "componentName": block_name,
                                    "reasoning": "Voltage mismatch detected, searching for intermediary component...",
                                    "hierarchyLevel": hierarchy_level
                                })
                                await asyncio.sleep(0.1)
                                
                                intermediary = orchestrator._resolve_voltage_mismatch(
                                    anchor_part, part, "power", power_compat
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
                                    await asyncio.sleep(0.1)
                    
                    interface_compat = orchestrator.compatibility_agent.check_compatibility(
                        anchor_part, part, connection_type="interface"
                    )
                    
                    compat_result = {"interface": interface_compat}
                    if provides_power:
                        compat_result["power"] = power_compat
                    orchestrator.design_state["compatibility_results"][block_name] = compat_result
                    
                    # Add compatibility reasoning from agent outputs
                    if interface_compat.get("compatible", True) and power_compat.get("compatible", True):
                        # Use agent's reasoning if available, otherwise generate simple message
                        compat_reasoning = interface_compat.get("reasoning") or power_compat.get("reasoning")
                        if compat_reasoning:
                            await queue.put({
                                "type": "reasoning",
                                "componentId": block_type,
                                "componentName": block_name,
                                "reasoning": compat_reasoning,
                                "hierarchyLevel": hierarchy_level
                            })
                        else:
                            await queue.put({
                                "type": "reasoning",
                                "componentId": block_type,
                                "componentName": block_name,
                                "reasoning": f"Compatibility check passed. {part_mpn} is compatible with anchor component.",
                                "hierarchyLevel": hierarchy_level
                            })
                        await asyncio.sleep(0.1)
                    elif not power_compat.get("compatible", True):
                        # Use agent's reasoning for incompatibility
                        compat_reasoning = power_compat.get("reasoning", "Voltage mismatch detected")
                        await queue.put({
                            "type": "reasoning",
                            "componentId": block_type,
                            "componentName": block_name,
                            "reasoning": compat_reasoning,
                            "hierarchyLevel": hierarchy_level
                        })
                        await asyncio.sleep(0.1)
                    elif not interface_compat.get("compatible", True):
                        # Use agent's reasoning for interface incompatibility
                        compat_reasoning = interface_compat.get("reasoning", "Interface mismatch detected")
                        await queue.put({
                            "type": "reasoning",
                            "componentId": block_type,
                            "componentName": block_name,
                            "reasoning": compat_reasoning,
                            "hierarchyLevel": hierarchy_level
                        })
                        await asyncio.sleep(0.1)
                
                orchestrator.design_state["selected_parts"][block_name] = part
                part_object = part_data_to_part_object(part)
                await queue.put({
                    "type": "selection",
                    "componentId": block_type,
                    "componentName": block_name,
                    "partData": part_object,
                    "hierarchyLevel": hierarchy_level
                })
                await asyncio.sleep(0.1)
                
                # Add external components
                from utils.part_database import get_recommended_external_components
                ext_comps = get_recommended_external_components(part.get("id", ""))
                orchestrator.design_state["external_components"].extend(ext_comps)
            
            hierarchy_level += 1
        
        # Step 6: Enrich with datasheets
        orchestrator._enrich_parts_with_datasheets()
        
        # Step 7: Generate outputs
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
        
        # Design analysis
        await queue.put({
            "type": "reasoning",
            "componentId": "analysis",
            "componentName": "Design Analysis",
            "reasoning": "Performing power consumption analysis, thermal analysis, and design rule checks...",
            "hierarchyLevel": 0
        })
        await asyncio.sleep(0.1)
        
        design_analysis = orchestrator.design_analyzer.analyze_design(
            orchestrator.design_state["selected_parts"],
            connections,
            orchestrator.design_state["compatibility_results"]
        )
        orchestrator.design_state["design_analysis"] = design_analysis
        
        # Mark completion at the end
        await queue.put({
            "type": "complete",
            "message": "Component analysis complete"
        })
        
    except Exception as e:
        await queue.put({
            "type": "error",
            "message": str(e)
        })
        raise


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/mcp/component-analysis")
async def component_analysis(request: Request):
    """SSE endpoint for component analysis."""
    
    body = await request.json()
    query = body.get("query", "")
    context_query_id = body.get("contextQueryId")
    context = body.get("context", "")
    
    if not query:
        return {"error": "Query is required"}, 400
    
    async def event_stream():
        queue = asyncio.Queue()
        orchestrator = StreamingOrchestrator()
        
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
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)

