"""
Forecast routes
Endpoints for obsolescence and cost forecasting
"""

import logging
from fastapi import APIRouter, Request, HTTPException

from agents.obsolescence_forecast_agent import ObsolescenceForecastAgent
from agents.cost_forecast_agent import CostForecastAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.post("/obsolescence")
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
        logger.error(f"Error forecasting obsolescence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cost")
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
        logger.error(f"Error forecasting costs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

