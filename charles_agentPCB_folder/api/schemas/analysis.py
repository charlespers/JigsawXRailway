"""
Analysis-related schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from .common import BOMItem, Connection


class AnalysisRequest(BaseModel):
    """Base analysis request"""
    bom_items: List[BOMItem]
    connections: Optional[List[Connection]] = Field(default_factory=list)
    provider: Optional[str] = Field(default="openai", description="LLM provider: 'openai' or 'xai'")


class CostAnalysisRequest(AnalysisRequest):
    """Cost analysis request"""
    pass


class CostAnalysisResponse(BaseModel):
    """Cost analysis response"""
    total_cost: float
    cost_by_category: Dict[str, float]
    high_cost_items: List[Dict[str, Any]]
    optimization_opportunities: List[Dict[str, Any]]


class SupplyChainAnalysisRequest(AnalysisRequest):
    """Supply chain analysis request"""
    pass


class SupplyChainAnalysisResponse(BaseModel):
    """Supply chain analysis response"""
    risks: List[Dict[str, Any]]
    warnings: List[str]
    risk_score: float = Field(..., ge=0, le=100)
    recommendations: List[str]


class PowerAnalysisRequest(AnalysisRequest):
    """Power analysis request"""
    operating_modes: Optional[Dict[str, float]] = None
    battery_capacity_mah: Optional[float] = None
    battery_voltage: Optional[float] = Field(default=3.7)


class PowerAnalysisResponse(BaseModel):
    """Power analysis response"""
    total_power: float
    power_by_rail: Dict[str, float]
    power_by_component: List[Dict[str, Any]]
    battery_life: Optional[Dict[str, Any]] = None


class ThermalAnalysisRequest(AnalysisRequest):
    """Thermal analysis request"""
    ambient_temp: float = Field(default=25.0)
    pcb_area_cm2: Optional[float] = None


class ThermalAnalysisResponse(BaseModel):
    """Thermal analysis response"""
    component_thermal: Dict[str, Dict[str, Any]]
    thermal_issues: List[Dict[str, Any]]
    total_thermal_issues: int
    total_power_dissipation_w: float
    recommendations: List[str]


class SignalIntegrityAnalysisRequest(AnalysisRequest):
    """Signal integrity analysis request"""
    pcb_thickness_mm: float = Field(default=1.6)
    trace_width_mils: float = Field(default=5.0)


class SignalIntegrityAnalysisResponse(BaseModel):
    """Signal integrity analysis response"""
    high_speed_signals: List[Dict[str, Any]]
    impedance_recommendations: List[Dict[str, Any]]
    emi_emc_recommendations: List[str]
    routing_recommendations: List[str]
    decoupling_analysis: Dict[str, Any]


class ManufacturingReadinessRequest(AnalysisRequest):
    """Manufacturing readiness analysis request"""
    pass


class ManufacturingReadinessResponse(BaseModel):
    """Manufacturing readiness analysis response"""
    dfm_checks: Dict[str, Any]
    assembly_complexity: Dict[str, Any]
    test_point_coverage: Dict[str, Any]
    panelization_recommendations: List[str]
    overall_readiness: str  # ready, needs_review, not_ready
    recommendations: List[str]


class DesignValidationRequest(AnalysisRequest):
    """Design validation request"""
    pass


class DesignValidationResponse(BaseModel):
    """Design validation response"""
    valid: bool
    issues: List[Dict[str, Any]]
    warnings: List[Any]  # Can be string or object
    compliance: Dict[str, bool]
    summary: Optional[Dict[str, Any]] = None
    fix_suggestions: Optional[List[Dict[str, Any]]] = None


class BatchAnalysisRequest(AnalysisRequest):
    """Batch analysis request"""
    analysis_types: List[str] = Field(..., min_items=1)


class BatchAnalysisResponse(BaseModel):
    """Batch analysis response"""
    results: Dict[str, Any]
    completed: List[str]
    errors: Optional[Dict[str, str]] = None


class BOMInsightsRequest(AnalysisRequest):
    """BOM insights request"""
    pass


class BOMInsightsResponse(BaseModel):
    """BOM insights response"""
    total_parts: int
    total_cost: float
    categories: Dict[str, int]
    lifecycle_summary: Dict[str, int]
    availability_summary: Dict[str, int]
    recommendations: List[str]

