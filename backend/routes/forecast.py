"""
Forecast routes
Endpoints for obsolescence and cost forecasting
"""

import logging
import os
from fastapi import APIRouter, HTTPException

from api.schemas.forecast import (
    ObsolescenceForecastRequest,
    ObsolescenceForecastResponse,
    CostForecastRequest,
    CostForecastResponse
)
from agents.obsolescence_forecast_agent import ObsolescenceForecastAgent
from agents.cost_forecast_agent import CostForecastAgent
from core.exceptions import AgentException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.post("/obsolescence", response_model=ObsolescenceForecastResponse)
async def forecast_obsolescence(request: ObsolescenceForecastRequest):
    """Forecast component obsolescence risks."""
    # Set provider before creating agents
    provider = "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        agent = ObsolescenceForecastAgent()
        
        # Convert BOM items format
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        
        forecast = agent.forecast_obsolescence(bom_items, request.forecast_years)
        return ObsolescenceForecastResponse(**forecast)
    except AgentException as e:
        logger.error(f"[OBSOLESCENCE_FORECAST] Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Obsolescence forecast agent error: {str(e)}")
    except ValueError as e:
        logger.error(f"[OBSOLESCENCE_FORECAST] Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"[OBSOLESCENCE_FORECAST] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in obsolescence forecast: {str(e)}")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider


@router.post("/cost", response_model=CostForecastResponse)
async def forecast_costs(request: CostForecastRequest):
    """Forecast BOM costs over time."""
    # Set provider before creating agents
    provider = "xai"  # Default to xai - OpenAI support removed
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    os.environ["LLM_PROVIDER"] = provider
    
    try:
        agent = CostForecastAgent()
        
        # Convert BOM items format
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        
        forecast = agent.forecast_costs(bom_items, request.forecast_months, request.production_volume)
        return CostForecastResponse(**forecast)
    except AgentException as e:
        logger.error(f"[COST_FORECAST] Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cost forecast agent error: {str(e)}")
    except ValueError as e:
        logger.error(f"[COST_FORECAST] Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"[COST_FORECAST] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in cost forecast: {str(e)}")
    finally:
        # Restore original provider
        os.environ["LLM_PROVIDER"] = original_provider

