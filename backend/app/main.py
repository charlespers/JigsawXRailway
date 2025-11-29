"""
Main FastAPI application entry point
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# CORS middleware - must be added before routes
# Handle both "*" and specific origins
try:
    cors_origins = settings.CORS_ORIGINS
    logger.info(f"CORS origins configured: {cors_origins}")
    
    if cors_origins == ["*"]:
        # When using "*", credentials must be False
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
            allow_headers=["*"],
            expose_headers=["*"],
        )
        logger.info("CORS configured with wildcard origin")
    else:
        # Specific origins can use credentials
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
            allow_headers=["*"],
            expose_headers=["*"],
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
    )

# Include routes
app.include_router(router)
app.include_router(mcp_router)  # MCP endpoints (no prefix)

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "ok", "version": "2.0.0"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "ok", "message": "PCB Design BOM Generator API", "version": "2.0.0"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# Railway/Nixpacks entry point
def create_app():
    """Application factory for Railway"""
    return app

