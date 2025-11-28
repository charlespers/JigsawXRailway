"""
FastAPI Server for PCB Design API
Clean, modular architecture following industry best practices
"""

import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file if available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

# Create FastAPI app
app = FastAPI(
    title="PCB Design API",
    version="1.0.0",
    description="Multi-agent system for PCB design generation and analysis"
)

# Setup middleware
try:
    from api.middleware import setup_middleware
    setup_middleware(app)
    logger.info("[SERVER] Middleware configured successfully")
except Exception as e:
    logger.error(f"[SERVER] Failed to setup middleware: {e}", exc_info=True)

# Include API routes
try:
    from routes import api_router
    app.include_router(api_router)
    logger.info("[SERVER] API routes included successfully")
    
    # Include streaming routes at root level (not under /api/v1)
    try:
        from routes.streaming import router as streaming_router
        app.include_router(streaming_router)
        logger.info("[SERVER] Streaming routes included successfully")
    except Exception as e:
        logger.warning(f"[SERVER] Failed to include streaming routes: {e}")
    
    # Log route summary
    total_routes = len([r for r in app.routes if hasattr(r, 'path')])
    logger.info(f"[SERVER] Total routes registered: {total_routes}")
except Exception as e:
    logger.error(f"[SERVER] Failed to include API routes: {e}", exc_info=True)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    total_routes = len([r for r in app.routes if hasattr(r, 'path')])
    logger.info(f"[STARTUP] Application started. Total routes: {total_routes}")
    
    # Log route summary by category
    analysis_routes = [r for r in app.routes if hasattr(r, 'path') and '/analysis' in r.path]
    design_routes = [r for r in app.routes if hasattr(r, 'path') and '/design' in r.path]
    parts_routes = [r for r in app.routes if hasattr(r, 'path') and '/parts' in r.path]
    eda_routes = [r for r in app.routes if hasattr(r, 'path') and '/eda' in r.path]
    forecast_routes = [r for r in app.routes if hasattr(r, 'path') and '/forecast' in r.path]
    streaming_routes = [r for r in app.routes if hasattr(r, 'path') and '/mcp' in r.path]
    
    logger.info(f"[STARTUP] Route breakdown:")
    logger.info(f"[STARTUP]   - Analysis: {len(analysis_routes)} routes")
    logger.info(f"[STARTUP]   - Design: {len(design_routes)} routes")
    logger.info(f"[STARTUP]   - Parts: {len(parts_routes)} routes")
    logger.info(f"[STARTUP]   - EDA: {len(eda_routes)} routes")
    logger.info(f"[STARTUP]   - Forecast: {len(forecast_routes)} routes")
    logger.info(f"[STARTUP]   - Streaming: {len(streaming_routes)} routes")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("[SHUTDOWN] Application shutting down")


if __name__ == "__main__":
    # Read PORT from environment (Railway sets this automatically)
    port = int(os.environ.get("PORT", 3001))
    uvicorn.run(app, host="0.0.0.0", port=port)
