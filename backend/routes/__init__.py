"""
Routes Package
Backward compatibility re-exports for new src/ structure
"""

import sys
from pathlib import Path

# Add src to path if it exists
src_dir = Path(__file__).parent.parent / "src"
if src_dir.exists() and str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Try new structure first, fall back to old structure
try:
    from routes import api_router
except ImportError:
    # Fall back to importing directly from this directory
    from . import analysis, design, parts, export, eda, forecast, streaming
    from fastapi import APIRouter
    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(analysis.router, tags=["analysis"])
    api_router.include_router(design.router, tags=["design"])
    api_router.include_router(parts.router, tags=["parts"])
    api_router.include_router(export.router, tags=["export"])
    api_router.include_router(eda.router, tags=["eda"])
    api_router.include_router(forecast.router, tags=["forecast"])

__all__ = ["api_router"]
