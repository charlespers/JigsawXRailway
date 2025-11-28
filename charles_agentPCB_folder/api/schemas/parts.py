"""
Parts-related schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ComparePartsRequest(BaseModel):
    """Request to compare parts"""
    part_ids: List[str] = Field(..., min_items=2)


class ComparePartsResponse(BaseModel):
    """Parts comparison response"""
    parts: List[Dict[str, Any]]
    comparison: Dict[str, Any]


class AlternativesRequest(BaseModel):
    """Request for part alternatives"""
    part_id: str
    same_footprint: bool = False
    lower_cost: bool = False


class AlternativesResponse(BaseModel):
    """Part alternatives response"""
    alternatives: List[Dict[str, Any]]


class CompatibilityCheckRequest(BaseModel):
    """Compatibility check request"""
    part1: Dict[str, Any]
    part2: Dict[str, Any]


class CompatibilityCheckResponse(BaseModel):
    """Compatibility check response"""
    compatible: bool
    warnings: List[str]
    alternatives: Optional[List[Dict[str, Any]]] = None


class EDAAssetsRequest(BaseModel):
    """EDA assets request"""
    part: Optional[Dict[str, Any]] = None
    bom_items: Optional[List[Dict[str, Any]]] = None
    tool: str = Field(default="kicad", pattern="^(kicad|altium|eagle)$")
    asset_types: List[str] = Field(default_factory=lambda: ["footprint", "symbol"])


class EDAAssetsResponse(BaseModel):
    """EDA assets response"""
    assets: Optional[Dict[str, Any]] = None
    tool: str
    part_count: Optional[int] = None

