"""
Middleware module
Centralized middleware setup for the FastAPI application
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .error_handler import ErrorHandlerMiddleware
from .request_logging import LoggingMiddleware

logger = logging.getLogger(__name__)


def setup_middleware(app: FastAPI):
    """Configure all middleware for the FastAPI application."""
    
    # CORS middleware
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    if cors_origins == "*":
        allow_origins = ["*"]
    else:
        allow_origins = [origin.strip() for origin in cors_origins.split(",")]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"[MIDDLEWARE] CORS configured with origins: {allow_origins}")
    
    # Error handling middleware
    try:
        app.add_middleware(ErrorHandlerMiddleware)
        logger.info("[MIDDLEWARE] Error handler middleware added")
    except Exception as e:
        logger.warning(f"[MIDDLEWARE] Failed to add error handler middleware: {e}")
    
    # Logging middleware
    try:
        app.add_middleware(LoggingMiddleware)
        logger.info("[MIDDLEWARE] Logging middleware added")
    except Exception as e:
        logger.warning(f"[MIDDLEWARE] Failed to add logging middleware: {e}")
    
    # Metrics middleware (optional)
    try:
        from .metrics import MetricsMiddleware
        app.add_middleware(MetricsMiddleware)
        logger.info("[MIDDLEWARE] Metrics middleware added")
    except ImportError:
        logger.debug("[MIDDLEWARE] Metrics middleware not available, skipping")
    except Exception as e:
        logger.warning(f"[MIDDLEWARE] Failed to add metrics middleware: {e}")
