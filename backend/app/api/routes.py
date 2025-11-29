"""
API routes
"""
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
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


@mcp_router.post("/mcp/component-analysis")
async def component_analysis_stream(request: Dict[str, Any]):
    """
    Streaming component analysis endpoint (compatible with frontend).
    
    Returns Server-Sent Events (SSE) stream of component reasoning and selections.
    """
    query = request.get("query", "")
    provider = request.get("provider", "xai")
    session_id = request.get("sessionId")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    async def generate_stream():
        try:
            # Send initial reasoning event
            yield f"data: {json.dumps({'type': 'reasoning', 'message': 'Analyzing requirements...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Generate design using orchestrator (takes string query)
            design = orchestrator.generate_design(query)
            
            # Stream component selections
            if design.selected_parts:
                for idx, (role, part) in enumerate(design.selected_parts.items()):
                    # Convert part dict to proper format
                    part_dict = part if isinstance(part, dict) else part.model_dump() if hasattr(part, 'model_dump') else {}
                    
                    # Build reasoning event
                    reasoning_data = {
                        'type': 'reasoning',
                        'componentId': role,
                        'componentName': part_dict.get('name', role),
                        'reasoning': f'Selected {part_dict.get("name", role)} for {role}',
                        'hierarchyLevel': 0
                    }
                    yield f"data: {json.dumps(reasoning_data)}\n\n"
                    await asyncio.sleep(0.1)
                    
                    # Extract cost
                    cost_est = part_dict.get('cost_estimate', {})
                    cost = cost_est.get('unit', 0) if isinstance(cost_est, dict) else (cost_est if cost_est else 0)
                    
                    # Build selection event
                    selection_data = {
                        'type': 'selection',
                        'componentId': role,
                        'componentName': part_dict.get('name', role),
                        'partData': {
                            'mpn': part_dict.get('mfr_part_number', ''),
                            'name': part_dict.get('name', ''),
                            'category': part_dict.get('category', ''),
                            'cost': cost
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
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": session_id or "new-session",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "version": "2.0.0"}

