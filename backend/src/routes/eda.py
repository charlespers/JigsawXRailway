"""
EDA routes
Endpoints for EDA asset generation and download
"""

import logging
import tempfile
import zipfile
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.schemas.parts import (
    EDAAssetsRequest,
    EDAAssetsResponse,
    EDADownloadRequest,
    BOMEDAAssetsRequest,
    BOMEDAAssetsResponse
)
# Import agents - try new structure first, fall back to old
try:
    from agents.utilities.eda_asset_agent import EDAAssetAgent
except ImportError:
    # If new structure import fails, raise the error (no fallback)
    raise
from utils.part_database import get_part_by_id
from core.exceptions import AgentException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/eda", tags=["eda"])


@router.post("/assets", response_model=EDAAssetsResponse)
async def get_eda_assets(request: EDAAssetsRequest):
    """Get EDA assets (footprints, symbols, 3D models) for a part."""
    try:
        if not request.part and not request.bom_items:
            raise HTTPException(status_code=400, detail="Either 'part' or 'bom_items' must be provided")
        
        agent = EDAAssetAgent()
        
        if request.part:
            assets = agent.get_eda_assets(request.part, request.tool, request.asset_types)
            return EDAAssetsResponse(assets=assets, tool=request.tool, part_count=1)
        else:
            # Multiple parts from BOM
            all_assets = {}
            for item in request.bom_items:
                part_id = item.get("mpn") or item.get("id")
                if part_id:
                    part_data = get_part_by_id(part_id)
                    if part_data:
                        assets = agent.get_eda_assets(part_data, request.tool, request.asset_types)
                        all_assets[part_id] = assets
            return EDAAssetsResponse(assets=all_assets, tool=request.tool, part_count=len(all_assets))
    except HTTPException:
        raise
    except AgentException as e:
        logger.error(f"[EDA_ASSETS] Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"EDA asset agent error: {str(e)}")
    except ValueError as e:
        logger.error(f"[EDA_ASSETS] Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"[EDA_ASSETS] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in EDA assets: {str(e)}")


@router.post("/download")
async def download_eda_assets(request: EDADownloadRequest):
    """Download EDA assets for a part or BOM as files."""
    try:
        if not request.part and not request.bom_items:
            raise HTTPException(status_code=400, detail="Either 'part' or 'bom_items' must be provided")
        
        agent = EDAAssetAgent()
        
        # Create temporary directory for assets
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_dir = tmp_path / request.tool
            output_dir.mkdir(parents=True, exist_ok=True)
            
            saved_files = {}
            
            if request.part:
                # Single part
                saved_files = agent.download_eda_assets(request.part, request.tool, output_dir)
            elif request.bom_items:
                # Multiple parts from BOM
                for item in request.bom_items:
                    part_id = item.get("mpn") or item.get("id")
                    if part_id:
                        part_data = get_part_by_id(part_id)
                        if part_data:
                            part_files = agent.download_eda_assets(part_data, request.tool, output_dir)
                            saved_files.update(part_files)
            
            if not saved_files:
                raise HTTPException(status_code=404, detail="No EDA assets generated")
            
            # Create zip file
            zip_path = tmp_path / f"eda_assets_{request.tool}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for asset_type, file_path in saved_files.items():
                    zipf.write(file_path, file_path.name)
            
            # Return zip file
            return FileResponse(
                zip_path,
                media_type="application/zip",
                filename=f"eda_assets_{request.tool}.zip"
            )
    except HTTPException:
        raise
    except AgentException as e:
        logger.error(f"[EDA_DOWNLOAD] Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"EDA asset agent error: {str(e)}")
    except ValueError as e:
        logger.error(f"[EDA_DOWNLOAD] Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"[EDA_DOWNLOAD] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in EDA download: {str(e)}")


@router.post("/bom-assets", response_model=BOMEDAAssetsResponse)
async def get_bom_eda_assets(request: BOMEDAAssetsRequest):
    """Get EDA assets for all parts in a BOM."""
    try:
        agent = EDAAssetAgent()
        
        all_assets = {}
        
        for item in request.bom_items:
            part_id = item.get("mpn") or item.get("id")
            if part_id:
                part_data = get_part_by_id(part_id)
                if part_data:
                    assets = agent.get_eda_assets(part_data, request.tool, request.asset_types)
                    all_assets[part_id] = assets
        
        return BOMEDAAssetsResponse(
            assets=all_assets,
            tool=request.tool,
            part_count=len(all_assets)
        )
    except HTTPException:
        raise
    except AgentException as e:
        logger.error(f"[BOM_EDA_ASSETS] Agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"EDA asset agent error: {str(e)}")
    except ValueError as e:
        logger.error(f"[BOM_EDA_ASSETS] Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    except Exception as e:
        logger.error(f"[BOM_EDA_ASSETS] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error in BOM EDA assets: {str(e)}")

