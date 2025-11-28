"""
API Routes
Modular route definitions for the PCB Design API
"""

from fastapi import APIRouter

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Import all route modules
from . import design, analysis, parts, export

# Include routers
api_router.include_router(design.router, tags=["design"])
api_router.include_router(analysis.router, tags=["analysis"])
api_router.include_router(parts.router, tags=["parts"])
api_router.include_router(export.router, tags=["export"])

