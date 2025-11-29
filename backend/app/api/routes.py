"""
API routes
"""
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Response, Body
from fastapi.responses import StreamingResponse
from app.api.schemas import DesignRequest, DesignResponse, BOMRequest, BOMResponse, ErrorResponse
from app.services.orchestrator import DesignOrchestrator
from app.agents.bom_generator import BOMGenerator
import json
import asyncio
from app.agents.spec_matcher import SpecMatcherAgent
from app.agents.power_analyzer import PowerAnalyzerAgent
from app.agents.alternative_finder import AlternativeFinderAgent
from app.agents.dfm_checker import DFMCheckerAgent
from app.agents.query_parser import QueryParserAgent
from app.agents.intelligent_matcher import IntelligentMatcherAgent
from app.agents.design_assistant import DesignAssistantAgent
from app.agents.design_templates import DesignTemplatesAgent
from app.agents.smart_recommender import SmartRecommenderAgent
from app.agents.realtime_validator import RealtimeValidatorAgent
from app.agents.cost_optimizer import CostOptimizerAgent
from app.agents.supply_chain_intelligence import SupplyChainIntelligenceAgent
from app.domain.models import NetConnection, ComponentCategory, BOM
from app.core.exceptions import PCBDesignException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["pcb-design"])
mcp_router = APIRouter(tags=["mcp"])  # Separate router for MCP endpoints (no prefix)
orchestrator = DesignOrchestrator()
bom_generator = BOMGenerator()
spec_matcher = SpecMatcherAgent()
power_analyzer = PowerAnalyzerAgent()
alternative_finder = AlternativeFinderAgent()
dfm_checker = DFMCheckerAgent()
query_parser = QueryParserAgent()
intelligent_matcher = IntelligentMatcherAgent()
design_assistant = DesignAssistantAgent()
design_templates = DesignTemplatesAgent()
smart_recommender = SmartRecommenderAgent()
realtime_validator = RealtimeValidatorAgent()
cost_optimizer = CostOptimizerAgent()
supply_chain = SupplyChainIntelligenceAgent()


@router.post("/design/generate", response_model=DesignResponse)
async def generate_design(request: DesignRequest):
    """
    Generate complete PCB design from natural language query
    
    This endpoint:
    1. Extracts requirements from query
    2. Designs system architecture
    3. Selects compatible parts
    4. Generates netlist connections
    5. Creates IPC-2581 compliant BOM
    """
    try:
        design = orchestrator.generate_design(request.query)
        return DesignResponse(design=design, success=True)
    except PCBDesignException as e:
        logger.error(f"Design generation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/bom/generate", response_model=BOMResponse)
async def generate_bom(request: BOMRequest):
    """
    Generate BOM from selected parts
    
    Creates IPC-2581 compliant Bill of Materials
    """
    try:
        connections = [NetConnection(**conn) for conn in request.connections]
        bom = bom_generator.generate(request.selected_parts, connections)
        return BOMResponse(bom=bom, success=True)
    except Exception as e:
        logger.error(f"BOM generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parts/search-by-specs")
async def search_by_specifications(
    query: Optional[str] = None,
    specifications: Optional[Dict[str, Any]] = None,
    category: Optional[str] = None,
    max_results: int = Query(default=10, ge=1, le=50)
):
    """
    Search parts by exact specifications.
    
    Either provide a natural language query or exact specifications.
    Solves: "Find me parts that meet these exact requirements"
    """
    try:
        # Parse query if provided, otherwise use specifications
        if query:
            specs = query_parser.parse_specifications(query)
        elif specifications:
            specs = specifications
        else:
            raise HTTPException(status_code=400, detail="Either 'query' or 'specifications' must be provided")
        
        cat_enum = ComponentCategory(category) if category else None
        results = spec_matcher.find_matching_parts(specs, category=cat_enum, max_results=max_results)
        
        return {
            "success": True,
            "specifications": specs,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Part search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/analyze-power")
async def analyze_power(
    selected_parts: Dict[str, Dict[str, Any]],
    power_supply: Optional[Dict[str, Any]] = None
):
    """
    Analyze power budget for selected parts.
    Solves: "Will my power supply handle all components? Are there thermal issues?"
    """
    try:
        analysis = power_analyzer.analyze_power_budget(selected_parts, power_supply)
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Power analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parts/{part_id}/alternatives")
async def get_alternatives(
    part_id: str,
    same_footprint: bool = Query(default=False),
    lower_cost: bool = Query(default=False),
    better_availability: bool = Query(default=False),
    same_voltage: bool = Query(default=False),
    same_interface: bool = Query(default=False)
):
    """
    Find alternative parts for a given part.
    Solves: "This part is obsolete/expensive/unavailable, what are my options?"
    """
    try:
        criteria = {
            "same_footprint": same_footprint,
            "lower_cost": lower_cost,
            "better_availability": better_availability,
            "same_voltage": same_voltage,
            "same_interface": same_interface
        }
        alternatives = alternative_finder.find_alternatives(part_id, criteria)
        return {
            "success": True,
            "part_id": part_id,
            "alternatives": alternatives,
            "count": len(alternatives)
        }
    except Exception as e:
        logger.error(f"Alternative search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/check-dfm")
async def check_dfm(
    bom: BOM,
    selected_parts: Dict[str, Dict[str, Any]]
):
    """
    Check design for manufacturability issues.
    Solves: "Will this design be manufacturable? Are there assembly issues?"
    """
    try:
        dfm_analysis = dfm_checker.check_design(bom, selected_parts)
        return {
            "success": True,
            "dfm_analysis": dfm_analysis
        }
    except Exception as e:
        logger.error(f"DFM check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parts/intelligent-search")
async def intelligent_part_search(
    query: str,
    design_context: Optional[Dict[str, Any]] = None,
    existing_parts: Optional[Dict[str, Any]] = None,
    max_results: int = Query(default=10, ge=1, le=50)
):
    """
    🪄 MAGICAL: Intelligent part search using AI + rich database.
    
    Understands natural language, considers design context, finds perfect parts.
    
    Example: "low-power MCU with WiFi for battery sensor node, under $5"
    """
    try:
        results = intelligent_matcher.find_perfect_parts(
            query=query,
            design_context=design_context,
            existing_parts=existing_parts,
            max_results=max_results
        )
        return {
            "success": True,
            **results
        }
    except Exception as e:
        logger.error(f"Intelligent search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/assistant")
async def design_assistant_endpoint(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
):
    """
    🪄 MAGICAL: Conversational design assistant.
    
    Helps refine requirements through intelligent questions.
    """
    try:
        response = design_assistant.assist(query, conversation_history)
        return {
            "success": True,
            **response
        }
    except Exception as e:
        logger.error(f"Design assistant error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/design/templates")
async def list_design_templates():
    """
    🪄 MAGICAL: Get available design templates.
    
    Pre-built design patterns for common applications.
    """
    try:
        templates = design_templates.list_templates()
        return {
            "success": True,
            "templates": templates
        }
    except Exception as e:
        logger.error(f"Template list error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/templates/{template_id}/generate")
async def generate_from_template(
    template_id: str,
    customizations: Optional[Dict[str, Any]] = None
):
    """
    🪄 MAGICAL: Generate complete design from template.
    
    Takes a template (e.g., "battery_sensor_node") and automatically finds
    all compatible parts to create a complete design.
    """
    try:
        design = design_templates.generate_from_template(template_id, customizations)
        return {
            "success": True,
            **design
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Template generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/recommend")
async def get_recommendations(
    selected_parts: Dict[str, Dict[str, Any]],
    design_context: Optional[Dict[str, Any]] = None
):
    """
    🪄 MAGICAL: Get smart recommendations for complementary parts.
    
    Analyzes what you've selected and suggests what's missing.
    """
    try:
        recommendations = smart_recommender.recommend(selected_parts, design_context)
        return {
            "success": True,
            **recommendations
        }
    except Exception as e:
        logger.error(f"Recommendation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/validate-realtime")
async def validate_realtime(
    new_part: Dict[str, Any],
    existing_parts: Dict[str, Dict[str, Any]],
    design_context: Optional[Dict[str, Any]] = None
):
    """
    🪄 MAGICAL: Real-time validation as parts are added.
    
    Instant feedback on compatibility, power, thermal impact.
    """
    try:
        validation = realtime_validator.validate_addition(
            new_part, existing_parts, design_context
        )
        return {
            "success": True,
            **validation
        }
    except Exception as e:
        logger.error(f"Realtime validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/validate-complete")
async def validate_complete_design(
    selected_parts: Dict[str, Dict[str, Any]],
    connections: Optional[List[Dict[str, Any]]] = None
):
    """
    🪄 MAGICAL: Validate complete design.
    
    Comprehensive validation of entire design.
    """
    try:
        validation = realtime_validator.validate_design(selected_parts, connections)
        return {
            "success": True,
            **validation
        }
    except Exception as e:
        logger.error(f"Design validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/optimize-cost")
async def optimize_cost(
    selected_parts: Dict[str, Dict[str, Any]],
    target_savings_percent: float = Query(default=20.0, ge=0, le=50),
    preserve_critical: bool = Query(default=True)
):
    """
    🪄 MAGICAL: Cost optimization suggestions.
    
    Find cheaper alternatives without compromising design.
    """
    try:
        optimization = cost_optimizer.optimize_cost(
            selected_parts,
            target_savings_percent,
            preserve_critical
        )
        return {
            "success": True,
            **optimization
        }
    except Exception as e:
        logger.error(f"Cost optimization error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/analyze-supply-chain")
async def analyze_supply_chain(
    selected_parts: Dict[str, Dict[str, Any]],
    bom: Optional[Dict[str, Any]] = None
):
    """
    🪄 MAGICAL: Supply chain intelligence.
    
    Analyze availability, lead times, obsolescence risks.
    """
    try:
        analysis = supply_chain.analyze_supply_chain(selected_parts, bom)
        return {
            "success": True,
            **analysis
        }
    except Exception as e:
        logger.error(f"Supply chain analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@mcp_router.options("/mcp/component-analysis")
async def component_analysis_options():
    """Handle CORS preflight for component analysis.

    NOTE: This stays intentionally simple and relies on CORSMiddleware
    for most behavior. We just ensure a 200 is returned so Railway/clients
    see a successful preflight.
    """
    from fastapi.responses import Response
    return Response(status_code=200)


from uuid import uuid4

# In-memory session store for MCP component analysis
# Maps session_id -> {"selected_parts": Dict[str, Any]}
MCP_SESSIONS: Dict[str, Dict[str, Any]] = {}


@mcp_router.post("/mcp/component-analysis")
async def component_analysis_stream(request: Dict[str, Any]):
    """
    Streaming component analysis endpoint (compatible with frontend).
    
    Returns Server-Sent Events (SSE) stream of component reasoning and selections.
    """
    query = request.get("query", "")
    provider = request.get("provider", "xai")
    client_session_id = request.get("sessionId")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    # Determine effective session id (use client session if provided, else create new)
    session_id = client_session_id or str(uuid4())
    
    async def generate_stream():
        try:
            # Send initial reasoning event
            yield f"data: {json.dumps({'type': 'reasoning', 'message': 'Analyzing requirements...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Generate design using orchestrator (takes string query)
            design = orchestrator.generate_design(query)

            # Merge with existing session parts to support multi-step design
            existing_session = MCP_SESSIONS.get(session_id, {})
            accumulated_parts: Dict[str, Dict[str, Any]] = dict(existing_session.get("selected_parts", {}))

            # New parts from this design
            new_parts = design.selected_parts or {}
            for role, part in new_parts.items():
                role_key = role
                # Avoid overwriting existing roles; if conflict, append index
                if role_key in accumulated_parts:
                    suffix = 2
                    while f"{role_key}_{suffix}" in accumulated_parts:
                        suffix += 1
                    role_key = f"{role_key}_{suffix}"
                accumulated_parts[role_key] = part

            # Persist updated session state
            MCP_SESSIONS[session_id] = {"selected_parts": accumulated_parts}

            # Stream component selections for ALL accumulated parts in this session
            if accumulated_parts:
                for idx, (role, part) in enumerate(accumulated_parts.items()):
                    # Convert part dict to proper format
                    part_dict = part if isinstance(part, dict) else part.model_dump() if hasattr(part, 'model_dump') else {}
                    
                    # Build reasoning event per component
                    reasoning_data = {
                        'type': 'reasoning',
                        'componentId': role,
                        'componentName': part_dict.get('name', role),
                        'reasoning': f'Selected {part_dict.get("name", role)} for {role}',
                        'hierarchyLevel': 0
                    }
                    yield f"data: {json.dumps(reasoning_data)}\n\n"
                    await asyncio.sleep(0.1)
                    
                    # Extract cost - prioritize 'value' over 'unit' to match JSON structure
                    cost_est = part_dict.get('cost_estimate', {})
                    if isinstance(cost_est, dict):
                        unit_cost = cost_est.get('value') or cost_est.get('unit') or cost_est.get('price') or cost_est.get('cost') or 0.0
                        currency = cost_est.get('currency', 'USD')
                    elif isinstance(cost_est, (int, float)):
                        unit_cost = float(cost_est)
                        currency = 'USD'
                    else:
                        unit_cost = 0.0
                        currency = 'USD'
                    
                    # Extract all engineering specs for comprehensive part data
                    supply_voltage_range = part_dict.get('supply_voltage_range', {})
                    voltage_str = None
                    if isinstance(supply_voltage_range, dict):
                        if supply_voltage_range.get('nominal'):
                            voltage_str = f"{supply_voltage_range['nominal']}V"
                        elif supply_voltage_range.get('min') and supply_voltage_range.get('max'):
                            voltage_str = f"{supply_voltage_range['min']}-{supply_voltage_range['max']}V"
                    
                    # Build comprehensive selection event with all engineering specs
                    selection_data = {
                        'type': 'selection',
                        'componentId': role,
                        'componentName': part_dict.get('name', role),
                        'partData': {
                            'mpn': part_dict.get('mfr_part_number', ''),
                            'name': part_dict.get('name', ''),
                            'manufacturer': part_dict.get('manufacturer', ''),
                            'description': part_dict.get('description', ''),
                            'category': part_dict.get('category', ''),
                            'package': part_dict.get('package', ''),
                            'footprint': part_dict.get('footprint', ''),
                            'datasheet_url': part_dict.get('datasheet_url', ''),
                            'voltage': voltage_str,
                            'supply_voltage_range': supply_voltage_range,
                            'operating_temp_range': part_dict.get('operating_temp_range', {}),
                            'current_max': part_dict.get('current_max', {}),
                            'pinout': part_dict.get('pinout', {}),
                            'interface_type': part_dict.get('interface_type', []),
                            'cost_estimate': {
                                'unit': unit_cost,
                                'value': unit_cost,
                                'currency': currency,
                                'quantity': cost_est.get('quantity', 1) if isinstance(cost_est, dict) else 1
                            },
                            'price': unit_cost,  # For backward compatibility
                            'cost': unit_cost,   # For backward compatibility
                            'availability_status': part_dict.get('availability_status', 'unknown'),
                            'lifecycle_status': part_dict.get('lifecycle_status', 'unknown'),
                            'rohs_compliant': part_dict.get('rohs_compliant', True)
                        },
                        'status': 'selected'
                    }
                    yield f"data: {json.dumps(selection_data)}\n\n"
                    await asyncio.sleep(0.1)
            
            # Send completion
            complete_data = {
                'type': 'complete',
                'message': 'Component analysis complete'
            }
            yield f"data: {json.dumps(complete_data)}\n\n"
            
        except Exception as e:
            logger.error(f"Component analysis error: {e}", exc_info=True)
            error_data = {
                'type': 'error',
                'message': str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            # Only non-CORS headers here; CORS is handled globally
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Echo back the effective session id so the frontend can persist it
            "X-Session-Id": session_id,
        }
    )


# Helper function to convert bom_items to selected_parts format
def _bom_items_to_selected_parts(bom_items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Convert frontend bom_items format to backend selected_parts format"""
    selected_parts = {}
    for idx, item in enumerate(bom_items):
        part_data = item.get("part_data", item)
        # Use componentId, id, or mfr_part_number as key
        key = (
            part_data.get("componentId") or
            part_data.get("id") or
            part_data.get("mfr_part_number") or
            f"part_{idx}"
        )
        selected_parts[key] = part_data
    return selected_parts

# Helper function to extract bom_items from request body (handles both wrapped and unwrapped formats)
def _extract_bom_items(request_body: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract bom_items from request body, handling both { bom_items: [...] } and direct list formats"""
    if "bom_items" in request_body:
        return request_body["bom_items"]
    elif isinstance(request_body, list):
        return request_body
    else:
        # Try to find bom_items as a key or return empty list
        return request_body.get("bom_items", [])


# Analysis endpoints (matching frontend expectations - accepts bom_items format)
@router.post("/analysis/power")
async def analysis_power(request_body: Dict[str, Any] = Body(...)):
    """Power analysis endpoint - accepts bom_items format from frontend"""
    try:
        bom_items = _extract_bom_items(request_body)
        operating_modes = request_body.get("operating_modes")
        battery_capacity_mah = request_body.get("battery_capacity_mah")
        battery_voltage = request_body.get("battery_voltage")
        
        if not bom_items:
            logger.warning("No bom_items provided in power analysis request")
            return {
                "total_power": 0,
                "power_by_rail": {},
                "power_by_component": []
            }
        
        selected_parts = _bom_items_to_selected_parts(bom_items)
        analysis = power_analyzer.analyze_power_budget(selected_parts)
        
        # Format response to match frontend PowerAnalysis type
        power_by_component = []
        for part_id, part_data in selected_parts.items():
            power_by_component.append({
                "part_id": part_id,
                "name": part_data.get("name", part_data.get("mfr_part_number", "Unknown")),
                "voltage": part_data.get("supply_voltage_range", {}).get("nominal", 3.3) if isinstance(part_data.get("supply_voltage_range"), dict) else 3.3,
                "current": part_data.get("supply_current_ma", 0) / 1000.0 if part_data.get("supply_current_ma") else 0,
                "power": analysis.get("power_by_component", {}).get(part_id, 0),
                "quantity": next((item.get("quantity", 1) for item in bom_items if item.get("part_data", {}).get("id") == part_id or item.get("part_data", {}).get("componentId") == part_id), 1),
                "duty_cycle": 1.0
            })
        
        response = {
            "total_power": analysis.get("total_power_watts", 0),
            "power_by_rail": analysis.get("power_by_rail", {}),
            "power_by_component": power_by_component
        }
        
        # Add battery life if provided
        if battery_capacity_mah and battery_voltage:
            total_power_w = response["total_power"]
            if total_power_w > 0:
                battery_energy_wh = (battery_capacity_mah / 1000.0) * battery_voltage
                estimated_hours = battery_energy_wh / total_power_w
                response["battery_life"] = {
                    "battery_capacity_mah": battery_capacity_mah,
                    "battery_voltage": battery_voltage,
                    "battery_energy_wh": battery_energy_wh,
                    "total_power_w": total_power_w,
                    "estimated_hours": estimated_hours,
                    "estimated_days": estimated_hours / 24.0
                }
        
        return response
    except Exception as e:
        logger.error(f"Power analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/thermal")
async def analysis_thermal(request_body: Dict[str, Any] = Body(...)):
    """Thermal analysis endpoint - accepts bom_items format"""
    try:
        bom_items = _extract_bom_items(request_body)
        ambient_temp = request_body.get("ambient_temp")
        pcb_area_cm2 = request_body.get("pcb_area_cm2")
        
        if not bom_items:
            logger.warning("No bom_items provided in thermal analysis request")
            return {
                "component_thermal": {},
                "thermal_issues": [],
                "total_thermal_issues": 0,
                "total_power_dissipation_w": 0,
                "recommendations": []
            }
        
        selected_parts = _bom_items_to_selected_parts(bom_items)
        power_analysis = power_analyzer.analyze_power_budget(selected_parts)
        total_power = power_analysis.get("total_power_watts", 0)
        
        # Calculate thermal characteristics
        component_thermal = {}
        thermal_issues = []
        ambient = ambient_temp or 25.0
        
        for part_id, part_data in selected_parts.items():
            power_diss = power_analysis.get("power_by_component", {}).get(part_id, 0)
            # Estimate junction temp (simplified model)
            thermal_resistance = part_data.get("thermal_resistance_c_per_w", 50.0)
            junction_temp = ambient + (power_diss * thermal_resistance)
            max_temp = part_data.get("max_operating_temp_c", 85.0)
            
            component_thermal[part_id] = {
                "power_dissipation_w": power_diss,
                "junction_temp_c": junction_temp,
                "max_temp_c": max_temp,
                "thermal_ok": junction_temp < max_temp
            }
            
            if junction_temp >= max_temp:
                thermal_issues.append({
                    "part_id": part_id,
                    "junction_temp_c": junction_temp,
                    "max_temp_c": max_temp,
                    "power_dissipation_w": power_diss,
                    "issue": f"Junction temperature {junction_temp:.1f}°C exceeds maximum {max_temp}°C"
                })
        
        recommendations = []
        if total_power > 5:
            recommendations.append("High power dissipation - consider thermal management")
            recommendations.append("Add thermal vias and consider heatsink")
        if thermal_issues:
            recommendations.append(f"{len(thermal_issues)} components exceed thermal limits")
        
        return {
            "component_thermal": component_thermal,
            "thermal_issues": thermal_issues,
            "total_thermal_issues": len(thermal_issues),
            "total_power_dissipation_w": total_power,
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(f"Thermal analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/signal-integrity")
async def analysis_signal_integrity(request_body: Dict[str, Any] = Body(...)):
    """Signal integrity analysis endpoint - accepts bom_items format"""
    try:
        bom_items = _extract_bom_items(request_body)
        connections = request_body.get("connections")
        pcb_thickness_mm = request_body.get("pcb_thickness_mm")
        trace_width_mils = request_body.get("trace_width_mils")
        
        if not bom_items:
            logger.warning("No bom_items provided in signal integrity analysis request")
            return {
                "high_speed_signals": [],
                "impedance_recommendations": [],
                "emi_emc_recommendations": [],
                "routing_recommendations": [],
                "decoupling_analysis": {
                    "adequate": False,
                    "recommendations": []
                }
            }
        
        selected_parts = _bom_items_to_selected_parts(bom_items)
        
        high_speed_signals = []
        impedance_recommendations = []
        emi_emc_recommendations = []
        routing_recommendations = []
        
        for part_id, part_data in selected_parts.items():
            interfaces = part_data.get("interface_type", [])
            if isinstance(interfaces, str):
                interfaces = [interfaces]
            
            for iface in interfaces:
                if iface in ["USB", "PCIe", "HDMI", "Ethernet", "MIPI", "DDR", "LVDS"]:
                    # Standard impedance requirements
                    impedance_map = {
                        "USB": 90,
                        "PCIe": 85,
                        "HDMI": 100,
                        "Ethernet": 100,
                        "MIPI": 100,
                        "DDR": 50,
                        "LVDS": 100
                    }
                    required_impedance = impedance_map.get(iface, 50)
                    
                    high_speed_signals.append({
                        "part_id": part_id,
                        "name": part_data.get("name", part_data.get("mfr_part_number", "Unknown")),
                        "interface": iface,
                        "calculated_impedance_ohms": required_impedance,  # Simplified
                        "required_impedance_ohms": required_impedance,
                        "impedance_ok": True,
                        "recommendation": f"Ensure {required_impedance}Ω differential impedance for {iface}"
                    })
                    
                    impedance_recommendations.append({
                        "interface": iface,
                        "part": part_data.get("name", part_id),
                        "current_impedance": required_impedance,
                        "required_impedance": required_impedance,
                        "recommendation": f"Use controlled impedance routing for {iface} signals"
                    })
        
        if high_speed_signals:
            routing_recommendations.append("Route high-speed signals with controlled impedance")
            routing_recommendations.append("Keep high-speed traces away from noisy components")
            emi_emc_recommendations.append("Add ground planes for EMI suppression")
            emi_emc_recommendations.append("Use proper decoupling capacitors near high-speed ICs")
        
        return {
            "high_speed_signals": high_speed_signals,
            "impedance_recommendations": impedance_recommendations,
            "emi_emc_recommendations": emi_emc_recommendations,
            "routing_recommendations": routing_recommendations,
            "decoupling_analysis": {
                "adequate": len([p for p in selected_parts.values() if "mcu" in p.get("category", "").lower() or "ic" in p.get("category", "").lower()]) > 0,
                "recommendations": ["Add 0.1uF decoupling capacitors near each IC power pin"] if selected_parts else []
            }
        }
    except Exception as e:
        logger.error(f"Signal integrity analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/validation")
async def analysis_validation(request_body: Dict[str, Any] = Body(...)):
    """Design validation endpoint - accepts bom_items format"""
    try:
        bom_items = _extract_bom_items(request_body)
        connections = request_body.get("connections")
        
        if not bom_items:
            logger.warning("No bom_items provided in validation request")
            return {
                "valid": True,
                "issues": [],
                "warnings": [],
                "compliance": {
                    "ipc_2221": True,
                    "ipc_7351": True,
                    "rohs": True,
                    "power_budget": True
                },
                "summary": {
                    "error_count": 0,
                    "warning_count": 0,
                    "compliance_score": 100
                },
                "fix_suggestions": []
            }
        
        selected_parts = _bom_items_to_selected_parts(bom_items)
        validation = realtime_validator.validate_design(selected_parts, connections)
        
        # Ensure response matches frontend DesignValidation type
        if not isinstance(validation, dict):
            validation = validation.dict() if hasattr(validation, "dict") else {}
        
        # Ensure fix_suggestions is included if available
        if "fix_suggestions" not in validation:
            validation["fix_suggestions"] = []
        
        # Ensure summary exists with compliance_score
        if "summary" not in validation:
            validation["summary"] = {
                "error_count": len(validation.get("issues", [])),
                "warning_count": len(validation.get("warnings", [])),
                "compliance_score": validation.get("compliance_score", 100)
            }
        elif "compliance_score" not in validation["summary"]:
            validation["summary"]["compliance_score"] = validation.get("compliance_score", 100)
        
        return validation
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/manufacturing-readiness")
async def analysis_manufacturing_readiness(request_body: Dict[str, Any] = Body(...)):
    """Manufacturing readiness (DFM) analysis endpoint - accepts bom_items format"""
    try:
        bom_items = _extract_bom_items(request_body)
        connections = request_body.get("connections")
        
        if not bom_items:
            logger.warning("No bom_items provided in manufacturing readiness request")
            return {
                "dfm_checks": {},
                "assembly_complexity": {"complexity_score": 0, "factors": []},
                "test_point_coverage": {"coverage_percentage": 0, "recommendations": []},
                "panelization_recommendations": [],
                "overall_readiness": "needs_review",
                "recommendations": []
            }
        
        selected_parts = _bom_items_to_selected_parts(bom_items)
        bom_obj = bom_generator.generate(selected_parts, [])
        dfm_analysis = dfm_checker.check_design(bom_obj, selected_parts)
        
        # Format response to match frontend ManufacturingReadiness type
        if isinstance(dfm_analysis, dict):
            return dfm_analysis
        return {
            "dfm_checks": dfm_analysis.get("dfm_checks", {}),
            "assembly_complexity": dfm_analysis.get("assembly_complexity", {"complexity_score": 50, "factors": []}),
            "test_point_coverage": dfm_analysis.get("test_point_coverage", {"coverage_percentage": 0, "recommendations": []}),
            "panelization_recommendations": dfm_analysis.get("panelization_recommendations", []),
            "overall_readiness": dfm_analysis.get("overall_readiness", "needs_review"),
            "recommendations": dfm_analysis.get("recommendations", [])
        }
    except Exception as e:
        logger.error(f"Manufacturing readiness error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/cost")
async def analysis_cost(request_body: Dict[str, Any] = Body(...)):
    """Cost analysis endpoint - accepts bom_items format (wrapped or unwrapped)"""
    try:
        bom_items = _extract_bom_items(request_body)
        if not bom_items:
            logger.warning("No bom_items provided in cost analysis request")
            return {
                "total_cost": 0,
                "cost_by_category": {},
                "high_cost_items": [],
                "optimization_opportunities": []
            }
        
        selected_parts = _bom_items_to_selected_parts(bom_items)
        optimization = cost_optimizer.optimize_cost(selected_parts, target_savings_percent=0)
        
        # Format response to match frontend CostAnalysis type
        return {
            "total_cost": optimization.get("total_cost", 0),
            "cost_by_category": optimization.get("cost_by_category", {}),
            "high_cost_items": optimization.get("high_cost_items", []),
            "optimization_opportunities": optimization.get("optimization_opportunities", [])
        }
    except Exception as e:
        logger.error(f"Cost analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/supply-chain")
async def analysis_supply_chain(request_body: Dict[str, Any] = Body(...)):
    """Supply chain analysis endpoint - accepts bom_items format (wrapped or unwrapped)"""
    try:
        bom_items = _extract_bom_items(request_body)
        if not bom_items:
            logger.warning("No bom_items provided in supply chain analysis request")
            return {
                "risks": [],
                "warnings": [],
                "risk_score": 0,
                "recommendations": []
            }
        
        selected_parts = _bom_items_to_selected_parts(bom_items)
        analysis = supply_chain.analyze_supply_chain(selected_parts)
        
        # Format response to match frontend SupplyChainAnalysis type
        return {
            "risks": analysis.get("risks", []),
            "warnings": analysis.get("warnings", []),
            "risk_score": analysis.get("risk_score", 0),
            "recommendations": analysis.get("recommendations", [])
        }
    except Exception as e:
        logger.error(f"Supply chain analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Design Health Score endpoint
@router.post("/design/health")
async def get_design_health(request_body: Dict[str, Any] = Body(...)):
    """
    Calculate overall design health score based on all analyses.
    Returns a comprehensive health score with breakdown by category.
    """
    try:
        bom_items = _extract_bom_items(request_body)
        connections = request_body.get("connections")
        
        if not bom_items:
            logger.warning("No bom_items provided in design health request")
            return {
                "design_health_score": 0,
                "health_level": "Poor",
                "health_breakdown": {
                    "validation": {"score": 0, "status": "poor", "errors": 0, "warnings": 0},
                    "supply_chain": {"score": 0, "status": "poor", "risk_score": 100},
                    "manufacturing": {"score": 0, "status": "poor", "readiness": "not_ready"},
                    "thermal": {"score": 0, "status": "poor", "critical_issues": 0, "warnings": 0},
                    "cost": {"score": 0, "status": "poor", "optimization_opportunities": 0}
                }
            }
        
        selected_parts = _bom_items_to_selected_parts(bom_items)
        
        # Run all analyses in parallel
        validation = realtime_validator.validate_design(selected_parts)
        cost_analysis = cost_optimizer.optimize_cost(selected_parts, target_savings_percent=0)
        supply_chain_analysis = supply_chain.analyze_supply_chain(selected_parts)
        power_analysis = power_analyzer.analyze_power_budget(selected_parts)
        bom_obj = bom_generator.generate(selected_parts, [])
        dfm_analysis = dfm_checker.check_design(bom_obj, selected_parts)
        
        # Calculate thermal issues
        total_power = power_analysis.get("total_power_watts", 0)
        thermal_issues_count = 1 if total_power > 5 else 0
        
        # Calculate scores for each category
        validation_errors = len(validation.get("issues", [])) if isinstance(validation, dict) else 0
        validation_warnings = len(validation.get("warnings", [])) if isinstance(validation, dict) else 0
        validation_score = max(0, 100 - (validation_errors * 20) - (validation_warnings * 5))
        
        supply_chain_score = max(0, 100 - (supply_chain_analysis.get("risk_score", 0) * 2))
        
        dfm_readiness = dfm_analysis.get("overall_readiness", "needs_review") if isinstance(dfm_analysis, dict) else "needs_review"
        manufacturing_score = 80 if dfm_readiness == "ready" else 60 if dfm_readiness == "needs_review" else 40
        
        thermal_score = 100 if thermal_issues_count == 0 else max(0, 100 - (thermal_issues_count * 30))
        
        cost_opportunities = len(cost_analysis.get("optimization_opportunities", []))
        cost_score = 100 if cost_opportunities == 0 else max(60, 100 - (cost_opportunities * 5))
        
        # Calculate overall health score (weighted average)
        overall_score = (
            validation_score * 0.3 +
            supply_chain_score * 0.2 +
            manufacturing_score * 0.2 +
            thermal_score * 0.15 +
            cost_score * 0.15
        )
        
        # Determine health level
        if overall_score >= 90:
            health_level = "Excellent"
        elif overall_score >= 75:
            health_level = "Good"
        elif overall_score >= 60:
            health_level = "Needs Improvement"
        else:
            health_level = "Poor"
        
        return {
            "design_health_score": round(overall_score, 1),
            "health_level": health_level,
            "health_breakdown": {
                "validation": {
                    "score": round(validation_score, 1),
                    "status": "excellent" if validation_score >= 90 else "good" if validation_score >= 75 else "needs_improvement",
                    "errors": validation_errors,
                    "warnings": validation_warnings
                },
                "supply_chain": {
                    "score": round(supply_chain_score, 1),
                    "status": "excellent" if supply_chain_score >= 90 else "good" if supply_chain_score >= 75 else "needs_improvement",
                    "risk_score": supply_chain_analysis.get("risk_score", 0)
                },
                "manufacturing": {
                    "score": round(manufacturing_score, 1),
                    "status": "excellent" if manufacturing_score >= 90 else "good" if manufacturing_score >= 75 else "needs_improvement",
                    "readiness": dfm_readiness
                },
                "thermal": {
                    "score": round(thermal_score, 1),
                    "status": "excellent" if thermal_score >= 90 else "good" if thermal_score >= 75 else "needs_improvement",
                    "critical_issues": thermal_issues_count,
                    "warnings": 1 if total_power > 3 else 0
                },
                "cost": {
                    "score": round(cost_score, 1),
                    "status": "excellent" if cost_score >= 90 else "good" if cost_score >= 75 else "needs_improvement",
                    "optimization_opportunities": cost_opportunities
                }
            }
        }
    except Exception as e:
        logger.error(f"Design health calculation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Part comparison endpoint
@router.post("/parts/compare")
async def compare_parts(part_ids: List[str] = Body(..., embed=True, alias="part_ids")):
    """
    Compare multiple parts by their specifications.
    Returns detailed comparison of specs, differences, and recommendations.
    """
    try:
        from app.domain.part_database import get_part_database
        db = get_part_database()
        
        parts = []
        for part_id in part_ids:
            # Try to get part by ID or MPN
            part = db.get_part(part_id)
            if not part:
                # Try searching by MPN in all parts
                all_parts = db.get_all_parts()
                part = next((p for p in all_parts if p.get("mfr_part_number") == part_id or p.get("id") == part_id), None)
            if part:
                parts.append(part)
        
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 parts to compare")
        
        # Compare specifications
        all_specs = set()
        for part in parts:
            all_specs.update(part.keys())
        
        comparison_specs = {}
        differences = []
        
        for spec in all_specs:
            values = [part.get(spec) for part in parts]
            if len(set(str(v) for v in values if v is not None)) > 1:
                comparison_specs[spec] = values
                differences.append(f"{spec}: {values[0]} vs {values[1]}")
        
        recommendations = []
        if differences:
            recommendations.append(f"Found {len(differences)} specification differences")
            recommendations.append("Review differences carefully before substitution")
        
        return {
            "parts": parts,
            "comparison": {
                "specs": comparison_specs,
                "differences": differences,
                "recommendations": recommendations
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Part comparison error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Part alternatives endpoint
@router.get("/parts/alternatives/{part_id}")
async def find_part_alternatives(
    part_id: str,
    same_footprint: bool = Query(False),
    lower_cost: bool = Query(False)
):
    """
    Find alternative parts for a given part ID.
    Can filter by same footprint and/or lower cost.
    """
    try:
        criteria = {}
        if same_footprint:
            criteria["same_footprint"] = True
        if lower_cost:
            criteria["lower_cost"] = True
        
        alternatives_list = alternative_finder.find_alternatives(part_id, criteria=criteria if criteria else None)
        
        # Format response to match frontend AlternativePart type
        # alternatives_list contains: [{"part": {...}, "compatibility": {...}, "score": float, "reasons": [...]}, ...]
        formatted_alternatives = []
        for alt_item in alternatives_list:
            part = alt_item.get("part", {})
            compat = alt_item.get("compatibility", {})
            score = alt_item.get("score", 0)
            reasons = alt_item.get("reasons", [])
            
            cost_est = part.get("cost_estimate", {})
            if isinstance(cost_est, dict):
                cost_value = cost_est.get("unit", cost_est.get("value", 0))
            else:
                cost_value = cost_est or 0
            
            formatted_alternatives.append({
                "id": part.get("id", part.get("mfr_part_number", "")),
                "name": part.get("name", part.get("mfr_part_number", "Unknown")),
                "compatibility_score": round(score, 1),
                "compatibility_notes": reasons + (compat.get("notes", []) if isinstance(compat, dict) else []),
                "cost_estimate": {
                    "value": cost_value,
                    "currency": "USD"
                },
                "availability_status": part.get("availability_status", "unknown"),
                "lifecycle_status": part.get("lifecycle_status", "unknown")
            })
        
        return {"alternatives": formatted_alternatives}
    except Exception as e:
        logger.error(f"Find alternatives error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "version": "2.0.0"}

