"""
Main FastAPI application entry point
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn

from app.api.routes import router, mcp_router
from app.core.config import settings
from app.core.logging import setup_logging

# Setup logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title="PCB Design BOM Generator",
    version="2.0.0",
    description="Enterprise PCB design system with agent-based component reasoning",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration - Use FastAPI's built-in middleware ONLY
# This handles OPTIONS automatically
try:
    cors_origins = settings.CORS_ORIGINS
    logger.info(f"CORS origins configured: {cors_origins}")
    
    if cors_origins == ["*"]:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
            max_age=3600,
        )
        logger.info("CORS configured with wildcard origin")
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
            max_age=3600,
        )
        logger.info(f"CORS configured with specific origins: {cors_origins}")
except Exception as e:
    logger.error(f"CORS configuration error: {e}", exc_info=True)
    # Fallback: allow all
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,
    )

# Include routes
app.include_router(router)
app.include_router(mcp_router)

# Health check - test if app responds
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "2.0.0"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "ok", "message": "PCB Design BOM Generator API", "version": "2.0.0"}

# Explicit OPTIONS handler for /mcp/component-analysis as backup
@app.options("/mcp/component-analysis")
async def options_mcp():
    """Explicit OPTIONS handler for MCP endpoint"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        }
    )

# Catch-all OPTIONS handler as final backup
@app.options("/{path:path}")
async def options_catchall(path: str):
    """Catch-all OPTIONS handler"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        }
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# Railway/Nixpacks entry point
def create_app():
    """Application factory for Railway"""
    return app
