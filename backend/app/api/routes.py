"""
API routes
"""
import logging
from fastapi import APIRouter, HTTPException
from app.api.schemas import DesignRequest, DesignResponse, BOMRequest, BOMResponse, ErrorResponse
from app.services.orchestrator import DesignOrchestrator
from app.agents.bom_generator import BOMGenerator
from app.domain.models import NetConnection
from app.core.exceptions import PCBDesignException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["pcb-design"])
orchestrator = DesignOrchestrator()
bom_generator = BOMGenerator()


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


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "version": "2.0.0"}

