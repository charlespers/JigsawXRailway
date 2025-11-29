"""
Main FastAPI application entry point
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
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

# Add CORS headers to ALL responses (bulletproof approach)
class CORSHeaderMiddleware(BaseHTTPMiddleware):
    """Add CORS headers to all responses - ensures headers are always present"""
    async def dispatch(self, request: Request, call_next):
        # Get origin from request
        origin = request.headers.get("Origin", "*")
        
        # Handle OPTIONS requests immediately - don't even call the app
        if request.method == "OPTIONS":
            # Use specific origin if configured, otherwise *
            cors_origin = origin if origin and origin in settings.CORS_ORIGINS else "*"
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": cors_origin if cors_origin != "*" else "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Credentials": "true" if cors_origin != "*" else "false",
                    "Access-Control-Max-Age": "3600",
                }
            )
        
        # For all other requests, add CORS headers to response
        response = await call_next(request)
        cors_origin = origin if origin and origin in settings.CORS_ORIGINS else "*"
        response.headers["Access-Control-Allow-Origin"] = cors_origin if cors_origin != "*" else "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true" if cors_origin != "*" else "false"
        response.headers["Access-Control-Max-Age"] = "3600"
        return response

# Add CORS header middleware FIRST (before CORS middleware)
app.add_middleware(CORSHeaderMiddleware)

# CORS middleware - must be added before routes
# Handle both "*" and specific origins
try:
    cors_origins = settings.CORS_ORIGINS
    logger.info(f"CORS origins configured: {cors_origins}")
    
    # Always allow OPTIONS explicitly
    if cors_origins == ["*"]:
        # When using "*", credentials must be False
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
            allow_headers=["*"],
            expose_headers=["*"],
            max_age=3600,  # Cache preflight for 1 hour
        )
        logger.info("CORS configured with wildcard origin")
    else:
        # Specific origins can use credentials
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
            allow_headers=["*"],
            expose_headers=["*"],
            max_age=3600,  # Cache preflight for 1 hour
        )
        logger.info(f"CORS configured with specific origins: {cors_origins}")
except Exception as e:
    logger.error(f"CORS configuration error: {e}", exc_info=True)
    # Fallback: allow all with explicit OPTIONS
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
app.include_router(mcp_router)  # MCP endpoints (no prefix)

# Catch-all OPTIONS handler for CORS preflight (must be after routes)
# This MUST be simple and never crash - Railway edge proxy depends on it
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Catch-all OPTIONS handler for CORS preflight requests - MUST NOT CRASH"""
    from fastapi.responses import Response
    try:
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "false",
                "Access-Control-Max-Age": "3600",
            }
        )
    except Exception as e:
        # Even if there's an error, return something
        logger.error(f"OPTIONS handler error: {e}", exc_info=True)
        return Response(status_code=200, headers={"Access-Control-Allow-Origin": "*"})

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

