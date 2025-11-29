"""
Forecast-related schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from .common import BOMItem


class ObsolescenceForecastRequest(BaseModel):
    """Obsolescence forecast request"""
    bom_items: List[BOMItem]
    forecast_years: int = Field(default=5, ge=1, le=10)


class ObsolescenceForecastResponse(BaseModel):
    """Obsolescence forecast response"""
    at_risk_parts: List[Dict[str, Any]]
    risk_summary: Dict[str, Any]
    recommendations: List[str]
    forecast_years: int


class CostForecastRequest(BaseModel):
    """Cost forecast request"""
    bom_items: List[BOMItem]
    forecast_months: int = Field(default=12, ge=1, le=60)
    production_volume: int = Field(default=1000, ge=1)


class CostForecastResponse(BaseModel):
    """Cost forecast response"""
    current_cost: float
    forecasted_costs: List[Dict[str, Any]]
    forecast_summary: Dict[str, Any]
    price_trends: Dict[str, Any]
    budget_recommendations: List[str]
    production_volume: int
    forecast_period_months: int

