"""
EDA routes
Endpoints for EDA asset generation and download
"""

import logging
import tempfile
import zipfile
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse

from agents.eda_asset_agent import EDAAssetAgent
from utils.part_database import get_part_by_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/eda", tags=["eda"])


@router.post("/assets")
async def get_eda_assets(request: Request):
    """Get EDA assets (footprints, symbols, 3D models) for a part."""
    try:
        data = await request.json()
        part = data.get("part", {})
        tool = data.get("tool", "kicad")  # kicad, altium, eagle
        asset_types = data.get("asset_types", ["footprint", "symbol", "3d_model"])
        
        if not part:
            raise HTTPException(status_code=400, detail="Part data is required")
        
        agent = EDAAssetAgent()
        assets = agent.get_eda_assets(part, tool, asset_types)
        return {"assets": assets, "tool": tool}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting EDA assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_eda_assets(request: Request):
    """Download EDA assets for a part or BOM as files."""
    try:
        data = await request.json()
        part = data.get("part")
        bom_items = data.get("bom_items", [])
        tool = data.get("tool", "kicad")
        asset_types = data.get("asset_types", ["footprint", "symbol"])
        
        agent = EDAAssetAgent()
        
        # Create temporary directory for assets
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_dir = tmp_path / tool
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if part:
                # Single part
                saved_files = agent.download_eda_assets(part, tool, output_dir)
            elif bom_items:
                # Multiple parts from BOM
                saved_files = {}
                
                for item in bom_items:
                    part_id = item.get("mpn") or item.get("id")
                    if part_id:
                        part_data = get_part_by_id(part_id)
                        if part_data:
                            part_files = agent.download_eda_assets(part_data, tool, output_dir)
                            saved_files.update(part_files)
            else:
                raise HTTPException(status_code=400, detail="Either 'part' or 'bom_items' must be provided")
            
            if not saved_files:
                raise HTTPException(status_code=404, detail="No EDA assets generated")
            
            # Create zip file
            zip_path = tmp_path / f"eda_assets_{tool}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for asset_type, file_path in saved_files.items():
                    zipf.write(file_path, file_path.name)
            
            # Return zip file
            return FileResponse(
                zip_path,
                media_type="application/zip",
                filename=f"eda_assets_{tool}.zip"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading EDA assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bom-assets")
async def get_bom_eda_assets(request: Request):
    """Get EDA assets for all parts in a BOM."""
    try:
        data = await request.json()
        bom_items = data.get("bom_items", [])
        tool = data.get("tool", "kicad")
        asset_types = data.get("asset_types", ["footprint", "symbol"])
        
        if not bom_items:
            raise HTTPException(status_code=400, detail="BOM items are required")
        
        agent = EDAAssetAgent()
        
        all_assets = {}
        
        for item in bom_items:
            part_id = item.get("mpn") or item.get("id")
            if part_id:
                part_data = get_part_by_id(part_id)
                if part_data:
                    assets = agent.get_eda_assets(part_data, tool, asset_types)
                    all_assets[part_id] = assets
        
        return {
            "assets": all_assets,
            "tool": tool,
            "part_count": len(all_assets)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting BOM EDA assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

