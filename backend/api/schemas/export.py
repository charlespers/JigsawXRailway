"""
Export-related schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from .common import BOMItem, Connection


class ExportRequest(BaseModel):
    """Export request"""
    bom_items: List[BOMItem]
    connections: Optional[List[Connection]] = Field(default_factory=list)
    format: str = Field(..., pattern="^(excel|csv|altium|kicad|pdf|json|xml)$")
    options: Optional[Dict[str, Any]] = None


class ExportResponse(BaseModel):
    """Export response"""
    file_url: Optional[str] = None
    file_data: Optional[str] = None  # Base64 encoded for binary formats
    filename: str
    format: str
    size_bytes: Optional[int] = None

