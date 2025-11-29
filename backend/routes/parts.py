"""
Parts-related routes
"""

import logging
from fastapi import APIRouter, HTTPException

from api.schemas.parts import (
    ComparePartsRequest,
    ComparePartsResponse,
    AlternativesRequest,
    AlternativesResponse,
    CompatibilityCheckRequest,
    CompatibilityCheckResponse,
    EDAAssetsRequest,
    EDAAssetsResponse
)
from core.exceptions import AgentException, PartNotFoundException
from utils.part_comparison import compare_parts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parts", tags=["parts"])


@router.post("/compare", response_model=ComparePartsResponse)
async def compare_parts_endpoint(request: ComparePartsRequest):
    """Compare multiple parts side-by-side."""
    try:
        if len(request.part_ids) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 parts to compare")
        
        comparison = compare_parts(request.part_ids)
        return ComparePartsResponse(**comparison)
    except PartNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing parts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/alternatives/{part_id}", response_model=AlternativesResponse)
async def get_alternatives(
    part_id: str,
    same_footprint: bool = False,
    lower_cost: bool = False
):
    """Find alternative parts for a given part."""
    try:
        from agents.alternative_finder_agent import AlternativeFinderAgent
        
        finder = AlternativeFinderAgent()
        criteria = {
            "same_footprint": same_footprint,
            "lower_cost": lower_cost
        }
        alternatives = finder.find_alternatives(part_id, criteria)
        return AlternativesResponse(alternatives=alternatives)
    except PartNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AgentException as e:
        logger.error(f"Agent error finding alternatives: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error finding alternatives: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/compatibility", response_model=CompatibilityCheckResponse)
async def check_compatibility(request: CompatibilityCheckRequest):
    """Check compatibility between two parts."""
    try:
        from agents.compatibility_agent import CompatibilityAgent
        from agents.alternative_finder_agent import AlternativeFinderAgent
        
        if not request.part1 or not request.part2:
            raise HTTPException(status_code=400, detail="Both part1 and part2 must be provided")
        
        agent = CompatibilityAgent()
        result = agent.check_compatibility(request.part1, request.part2)
        
        # Get alternatives if incompatible
        alternatives = []
        if not result.get("compatible", True):
            alt_agent = AlternativeFinderAgent()
            alternatives = alt_agent.find_alternatives(
                request.part1.get("id", ""),
                limit=3
            )
        
        return CompatibilityCheckResponse(
            compatible=result.get("compatible", True),
            warnings=result.get("warnings", []),
            alternatives=alternatives if alternatives else None
        )
    except AgentException as e:
        logger.error(f"Agent error checking compatibility: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking compatibility: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/eda-assets", response_model=EDAAssetsResponse)
async def get_eda_assets(request: EDAAssetsRequest):
    """Get EDA assets (footprints, symbols, 3D models) for a part or BOM."""
    try:
        from agents.eda_asset_agent import EDAAssetAgent
        from utils.part_database import get_part_by_id
        
        if not request.part and not request.bom_items:
            raise HTTPException(status_code=400, detail="Either 'part' or 'bom_items' must be provided")
        
        agent = EDAAssetAgent()
        
        if request.part:
            # Single part
            assets = agent.get_eda_assets(request.part, request.tool, request.asset_types)
            return EDAAssetsResponse(assets=assets, tool=request.tool, part_count=1)
        else:
            # Multiple parts from BOM
            all_assets = {}
            for item in request.bom_items:
                part_id = item.get("mpn") or item.get("id")
                if part_id:
                    part_data = get_part_by_id(part_id)
                    if part_data:
                        assets = agent.get_eda_assets(part_data, request.tool, request.asset_types)
                        all_assets[part_id] = assets
            
            return EDAAssetsResponse(
                assets=all_assets,
                tool=request.tool,
                part_count=len(all_assets)
            )
    except AgentException as e:
        logger.error(f"Agent error getting EDA assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting EDA assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

