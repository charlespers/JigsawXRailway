"""
Design-related schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from .common import BOMItem, Connection


class ComponentAnalysisRequest(BaseModel):
    """Request for component analysis (SSE endpoint)"""
    query: str = Field(..., min_length=1, description="Natural language design query")
    provider: str = Field(default="openai", pattern="^(openai|xai)$")
    sessionId: Optional[str] = None
    contextQueryId: Optional[str] = None
    context: Optional[str] = None


class ComponentAnalysisEvent(BaseModel):
    """SSE event structure"""
    type: str  # reasoning, selection, complete, error, heartbeat
    componentId: Optional[str] = None
    componentName: Optional[str] = None
    reasoning: Optional[str] = None
    hierarchyLevel: Optional[int] = None
    partData: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class DesignState(BaseModel):
    """Complete design state"""
    design_id: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    architecture: Optional[Dict[str, Any]] = None
    selected_parts: Dict[str, Any] = Field(default_factory=dict)
    external_components: List[Dict[str, Any]] = Field(default_factory=list)
    compatibility_results: Dict[str, Any] = Field(default_factory=dict)
    intermediaries: Dict[str, Any] = Field(default_factory=dict)
    connections: List[Connection] = Field(default_factory=list)
    bom: Dict[str, Any] = Field(default_factory=dict)
    design_analysis: Optional[Dict[str, Any]] = None
    updated_at: Optional[str] = None


class DesignReviewRequest(BaseModel):
    """Request for design review"""
    bom_items: List[BOMItem]
    connections: Optional[List[Connection]] = Field(default_factory=list)
    design_metadata: Optional[Dict[str, Any]] = None


class DesignReviewResponse(BaseModel):
    """Design review response"""
    design_health_score: float = Field(..., ge=0, le=100)
    health_level: str  # excellent, good, fair, poor
    health_breakdown: Dict[str, Any]
    recommendations: List[str]
    summary: Optional[str] = None


class DesignCompareRequest(BaseModel):
    """Request to compare designs"""
    designs: List[DesignState] = Field(..., min_items=2)
    baseline_index: int = Field(default=0, ge=0)


class DesignCompareResponse(BaseModel):
    """Design comparison response"""
    differences: Dict[str, Any]
    recommendations: List[str]
    cost_comparison: Optional[Dict[str, Any]] = None
    performance_comparison: Optional[Dict[str, Any]] = None

