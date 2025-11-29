"""
API request/response schemas
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.domain.models import Design, BOM, NetConnection


class DesignRequest(BaseModel):
    """Request to generate a design"""
    query: str = Field(..., description="Natural language description of the PCB design")
    provider: Optional[str] = Field(default="xai", description="LLM provider")


class DesignResponse(BaseModel):
    """Response with generated design"""
    design: Design
    success: bool = True
    message: Optional[str] = None


class BOMRequest(BaseModel):
    """Request to generate BOM"""
    selected_parts: Dict[str, Dict[str, Any]] = Field(..., description="Selected parts dictionary")
    connections: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Net connections")


class BOMResponse(BaseModel):
    """Response with BOM"""
    bom: BOM
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class SpecSearchRequest(BaseModel):
    """Request to search parts by specifications"""
    query: Optional[str] = Field(None, description="Natural language query")
    specifications: Optional[Dict[str, Any]] = Field(None, description="Exact specifications")
    category: Optional[str] = None
    max_results: int = Field(default=10, ge=1, le=50)


class PowerAnalysisRequest(BaseModel):
    """Request for power analysis"""
    selected_parts: Dict[str, Dict[str, Any]]
    power_supply: Optional[Dict[str, Any]] = None


class DFMCheckRequest(BaseModel):
    """Request for DFM check"""
    bom: BOM
    selected_parts: Dict[str, Dict[str, Any]]

