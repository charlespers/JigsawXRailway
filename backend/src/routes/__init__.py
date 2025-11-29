"""
API Routes
Modular route definitions for the PCB Design API
"""

import logging
import sys
from pathlib import Path
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Ensure routes directory is in path
routes_dir = Path(__file__).parent
if str(routes_dir) not in sys.path:
    sys.path.insert(0, str(routes_dir))

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Import all route modules with error handling
_imported_routers = []

# 1. Analysis routes (most critical)
try:
    from routes.analysis import router as analysis_router
    api_router.include_router(analysis_router, tags=["analysis"])
    _imported_routers.append("analysis")
    logger.info("[ROUTES] ✓ Analysis router included successfully")
except Exception as e:
    logger.error(f"[ROUTES] ✗ Failed to import/include analysis router: {e}", exc_info=True)

# 2. Design routes
try:
    from routes.design import router as design_router
    api_router.include_router(design_router, tags=["design"])
    _imported_routers.append("design")
    logger.info("[ROUTES] ✓ Design router included successfully")
except Exception as e:
    logger.warning(f"[ROUTES] Failed to import/include design router: {e}")

# 3. Parts routes
try:
    from routes.parts import router as parts_router
    api_router.include_router(parts_router, tags=["parts"])
    _imported_routers.append("parts")
    logger.info("[ROUTES] ✓ Parts router included successfully")
except Exception as e:
    logger.warning(f"[ROUTES] Failed to import/include parts router: {e}")

# 4. Export routes
try:
    from routes.export import router as export_router
    api_router.include_router(export_router, tags=["export"])
    _imported_routers.append("export")
    logger.info("[ROUTES] ✓ Export router included successfully")
except Exception as e:
    logger.warning(f"[ROUTES] Failed to import/include export router: {e}")

# 5. EDA routes
try:
    from routes.eda import router as eda_router
    api_router.include_router(eda_router, tags=["eda"])
    _imported_routers.append("eda")
    logger.info("[ROUTES] ✓ EDA router included successfully")
except Exception as e:
    logger.warning(f"[ROUTES] Failed to import/include EDA router: {e}")

# 6. Forecast routes
try:
    from routes.forecast import router as forecast_router
    api_router.include_router(forecast_router, tags=["forecast"])
    _imported_routers.append("forecast")
    logger.info("[ROUTES] ✓ Forecast router included successfully")
except Exception as e:
    logger.warning(f"[ROUTES] Failed to import/include forecast router: {e}")

# Log final route count
total_routes = len([r for r in api_router.routes if hasattr(r, 'path')])
logger.info(f"[ROUTES] Summary: {len(_imported_routers)} routers imported, {total_routes} total routes")

__all__ = ["api_router"]
