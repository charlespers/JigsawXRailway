"""
Export-related routes
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import tempfile
import zipfile
from pathlib import Path

from api.schemas.export import ExportRequest, ExportResponse
from core.exceptions import AgentException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/", response_model=ExportResponse)
async def export_design(request: ExportRequest):
    """Export design in various formats."""
    try:
        from utils.bom_exporter import export_bom
        
        # Convert BOM items format
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        
        # Export based on format
        if request.format == "excel":
            file_path = export_bom(bom_items, format="xlsx", **request.options or {})
        elif request.format == "csv":
            file_path = export_bom(bom_items, format="csv", **request.options or {})
        elif request.format == "json":
            import json
            file_path = Path(tempfile.gettempdir()) / f"design_export_{hash(str(bom_items))}.json"
            with open(file_path, "w") as f:
                json.dump({"bom_items": bom_items, "connections": request.connections}, f, indent=2)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        # For now, return file info (in production, upload to storage and return URL)
        return ExportResponse(
            file_url=None,  # Would be set in production
            filename=file_path.name,
            format=request.format,
            size_bytes=file_path.stat().st_size if file_path.exists() else None
        )
    except AgentException as e:
        logger.error(f"Agent error in export: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in export: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/download")
async def download_export(request: ExportRequest):
    """Download exported design as file."""
    try:
        from utils.bom_exporter import export_bom
        
        # Convert BOM items format
        bom_items = [
            {"part_data": item.part_data, "quantity": item.quantity}
            for item in request.bom_items
        ]
        
        # Export based on format
        if request.format in ["excel", "csv"]:
            file_path = export_bom(bom_items, format=request.format, **request.options or {})
            return FileResponse(
                file_path,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if request.format == "excel" else "text/csv",
                filename=file_path.name
            )
        elif request.format == "json":
            import json
            file_path = Path(tempfile.gettempdir()) / f"design_export_{hash(str(bom_items))}.json"
            with open(file_path, "w") as f:
                json.dump({"bom_items": bom_items, "connections": request.connections}, f, indent=2)
            return FileResponse(
                file_path,
                media_type="application/json",
                filename=file_path.name
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
    except AgentException as e:
        logger.error(f"Agent error in export download: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in export download: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

