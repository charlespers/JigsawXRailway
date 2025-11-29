"""
API routes
"""
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.api.schemas import DesignRequest, DesignResponse, BOMRequest, BOMResponse, ErrorResponse
from app.services.orchestrator import DesignOrchestrator
from app.agents.bom_generator import BOMGenerator
from app.agents.spec_matcher import SpecMatcherAgent
from app.agents.power_analyzer import PowerAnalyzerAgent
from app.agents.alternative_finder import AlternativeFinderAgent
from app.agents.dfm_checker import DFMCheckerAgent
from app.agents.query_parser import QueryParserAgent
from app.domain.models import NetConnection, ComponentCategory
from app.core.exceptions import PCBDesignException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["pcb-design"])
orchestrator = DesignOrchestrator()
bom_generator = BOMGenerator()
spec_matcher = SpecMatcherAgent()
power_analyzer = PowerAnalyzerAgent()
alternative_finder = AlternativeFinderAgent()
dfm_checker = DFMCheckerAgent()
query_parser = QueryParserAgent()


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


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "version": "2.0.0"}

