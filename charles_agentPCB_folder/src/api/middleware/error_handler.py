"""
Error Handler Middleware
Standardized error handling and responses with correlation IDs
"""

import logging
import uuid
import time
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any
from core.exceptions import (
    PCBDesignException,
    AgentException,
    ValidationException,
    PartNotFoundException,
    CompatibilityException,
)

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Handle exceptions and return standardized error responses with correlation IDs."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Add correlation ID to response headers
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        except PartNotFoundException as e:
            logger.error(f"[ERROR] Part not found: {e.part_id}")
            return JSONResponse(
                status_code=404,
                content={
                    "error": str(e),
                    "code": "PART_NOT_FOUND",
                    "part_id": e.part_id,
                }
            )
        except CompatibilityException as e:
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            logger.error(f"[ERROR] [{correlation_id}] Compatibility issue: {e}")
            return JSONResponse(
                status_code=400,
                headers={"X-Correlation-ID": correlation_id},
                content={
                    "error": str(e),
                    "code": "COMPATIBILITY_ERROR",
                    "part1": e.part1,
                    "part2": e.part2,
                    "issues": e.issues,
                    "correlation_id": correlation_id,
                    "timestamp": time.time()
                }
            )
        except ValidationException as e:
            logger.error(f"[ERROR] Validation error: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": str(e),
                    "code": "VALIDATION_ERROR",
                    "field": e.field,
                    "errors": e.errors,
                }
            )
        except AgentException as e:
            logger.error(f"[ERROR] Agent error: {e.agent_name} - {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(e),
                    "code": "AGENT_ERROR",
                    "agent_name": e.agent_name,
                    "details": e.details,
                }
            )
        except PCBDesignException as e:
            logger.error(f"[ERROR] PCB Design error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(e),
                    "code": "DESIGN_ERROR",
                }
            )
        except HTTPException:
            # Re-raise HTTP exceptions (they're already properly formatted)
            raise
        except Exception as e:
            logger.error(f"[ERROR] Unexpected error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR",
                }
            )

