"""
API Routes
Modular route definitions for the PCB Design API
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Import all route modules with error handling
try:
    from . import analysis
    api_router.include_router(analysis.router, tags=["analysis"])
    logger.info("[ROUTES] Successfully included analysis router")
except Exception as e:
    logger.error(f"[ROUTES] Failed to import/include analysis router: {e}", exc_info=True)

try:
    from . import design
    api_router.include_router(design.router, tags=["design"])
    logger.info("[ROUTES] Successfully included design router")
except Exception as e:
    logger.error(f"[ROUTES] Failed to import/include design router: {e}", exc_info=True)

try:
    from . import parts
    api_router.include_router(parts.router, tags=["parts"])
    logger.info("[ROUTES] Successfully included parts router")
except Exception as e:
    logger.error(f"[ROUTES] Failed to import/include parts router: {e}", exc_info=True)

try:
    from . import export
    api_router.include_router(export.router, tags=["export"])
    logger.info("[ROUTES] Successfully included export router")
except Exception as e:
    logger.error(f"[ROUTES] Failed to import/include export router: {e}", exc_info=True)

# Log final route count
analysis_routes = [r for r in api_router.routes if hasattr(r, 'path') and '/analysis' in r.path]
logger.info(f"[ROUTES] Total analysis routes in api_router: {len(analysis_routes)}")

