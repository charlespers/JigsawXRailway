"""
Main FastAPI application entry point
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn

from app.api.routes import router, mcp_router
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

# CORS configuration: specific origins, credentials enabled
origins = [
    "https://jigsawxrailway-frontend.up.railway.app",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# Railway/Nixpacks entry point
def create_app():
    """Application factory for Railway"""
    return app
