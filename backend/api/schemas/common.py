"""
Common schemas used across all API endpoints
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "ok"
    version: Optional[str] = None
    timestamp: Optional[str] = None


class BOMItem(BaseModel):
    """BOM item structure"""
    part_data: Dict[str, Any]
    quantity: int = Field(default=1, ge=1)
    designator: Optional[str] = None
    reference: Optional[str] = None


class Connection(BaseModel):
    """Connection/net structure"""
    net_name: str
    components: List[str]
    pins: List[str]
    signal_type: Optional[str] = None


class PartObject(BaseModel):
    """Part object structure for frontend compatibility"""
    componentId: str
    mpn: str
    manufacturer: str
    description: str
    price: float
    currency: str = "USD"
    voltage: Optional[str] = None
    package: Optional[str] = None
    interfaces: Optional[List[str]] = None
    datasheet: Optional[str] = None
    quantity: int = 1
    # Extended fields
    tolerance: Optional[str] = None
    lifecycle_status: Optional[str] = None
    rohs_compliant: Optional[bool] = None
    lead_time_days: Optional[int] = None
    mounting_type: Optional[str] = None
    category: Optional[str] = None
    footprint: Optional[str] = None
    msl_level: Optional[str] = None
    assembly_side: Optional[str] = None
    alternate_part_numbers: Optional[List[str]] = None
    distributor_part_numbers: Optional[Dict[str, str]] = None
    temperature_rating: Optional[float] = None
    availability_status: Optional[str] = None
    test_point: Optional[bool] = None
    fiducial: Optional[bool] = None
    assembly_notes: Optional[str] = None

