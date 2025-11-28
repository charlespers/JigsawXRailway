"""
Design-related routes
"""

import logging
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

from api.schemas.design import (
    DesignReviewRequest,
    DesignReviewResponse,
    DesignCompareRequest,
    DesignCompareResponse
)
from api.schemas.common import ErrorResponse
from agents.design_review_agent import DesignReviewAgent
from agents.design_comparison_agent import DesignComparisonAgent
from core.exceptions import AgentException, OrchestrationException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/design", tags=["design"])


@router.post("/review", response_model=DesignReviewResponse)
async def review_design(request: DesignReviewRequest):
    """Get comprehensive design review with health score."""
    try:
        agent = DesignReviewAgent()
        
        # Convert BOM items format
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        
        # Convert connections format
        connections = [
            {
                "net_name": conn.net_name,
                "components": conn.components,
                "pins": conn.pins,
                "signal_type": conn.signal_type
            }
            for conn in request.connections
        ]
        
        review = agent.review_design(
            bom_items,
            connections,
            request.design_metadata
        )
        
        return DesignReviewResponse(**review)
    
    except AgentException as e:
        logger.error(f"Agent error in design review: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in design review: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/compare", response_model=DesignCompareResponse)
async def compare_designs(request: DesignCompareRequest):
    """Compare multiple design versions."""
    try:
        agent = DesignComparisonAgent()
        
        # Convert design states to dict format
        designs = [design.dict() for design in request.designs]
        
        comparison = agent.compare_designs(designs, request.baseline_index)
        
        return DesignCompareResponse(**comparison)
    
    except AgentException as e:
        logger.error(f"Agent error in design comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in design comparison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

