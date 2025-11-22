"""
EDA Asset Agent
Generates and manages EDA (Electronic Design Automation) assets for parts:
- Footprints (.kicad_mod for KiCad)
- Symbols (.lib for KiCad)
- 3D Models (.step, .wrl)
- Support for multiple EDA tools (KiCad, Altium, Eagle)
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
from requests.exceptions import Timeout as RequestsTimeout

# Add development_demo/utils to path for config access
sys.path.insert(0, str(Path(__file__).parent.parent))


class EDAAssetAgent:
    """Agent that generates and manages EDA assets for PCB components."""
    
    def __init__(self):
        self.asset_cache_dir = Path(__file__).parent.parent / "data" / "eda_assets"
        self.asset_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # EDA tool support
        self.supported_tools = ["kicad", "altium", "eagle"]
        self.supported_formats = {
            "kicad": {
                "footprint": ".kicad_mod",
                "symbol": ".lib",
                "3d_model": ".step"
            },
            "altium": {
                "footprint": ".PcbLib",
                "symbol": ".SchLib",
                "3d_model": ".step"
            },
            "eagle": {
                "footprint": ".lbr",
                "symbol": ".lbr",
                "3d_model": ".step"
            }
        }
    
    def get_eda_assets(
        self,
        part: Dict[str, Any],
        tool: str = "kicad",
        asset_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get EDA assets for a part.
        
        Args:
            part: Part dictionary from database
            tool: EDA tool name ("kicad", "altium", "eagle")
            asset_types: List of asset types to generate ["footprint", "symbol", "3d_model"]
        
        Returns:
            Dictionary with asset URLs or generated content:
            {
                "footprint": {"url": "...", "content": "...", "format": ".kicad_mod"},
                "symbol": {"url": "...", "content": "...", "format": ".lib"},
                "3d_model": {"url": "...", "content": "...", "format": ".step"}
            }
        """
        if asset_types is None:
            asset_types = ["footprint", "symbol", "3d_model"]
        
        if tool not in self.supported_tools:
            tool = "kicad"  # Default to KiCad
        
        part_id = part.get("id", part.get("mpn", ""))
        assets = {}
        
        # Check if assets are already in part data
        eda_assets = part.get("eda_assets", {})
        if eda_assets and tool in eda_assets:
            tool_assets = eda_assets[tool]
            for asset_type in asset_types:
                if asset_type in tool_assets:
                    assets[asset_type] = tool_assets[asset_type]
                    continue
        
        # Generate missing assets
        for asset_type in asset_types:
            if asset_type not in assets:
                asset = self._generate_asset(part, tool, asset_type)
                if asset:
                    assets[asset_type] = asset
        
        return assets
    
    def _generate_asset(
        self,
        part: Dict[str, Any],
        tool: str,
        asset_type: str
    ) -> Optional[Dict[str, Any]]:
        """Generate an EDA asset for a part."""
        part_id = part.get("id", part.get("mpn", ""))
        package = part.get("package", "")
        footprint_name = part.get("footprint", "")
        
        # Check cache first
        cache_file = self.asset_cache_dir / tool / asset_type / f"{part_id}{self.supported_formats[tool][asset_type]}"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "url": None,
                "content": content,
                "format": self.supported_formats[tool][asset_type],
                "cached": True
            }
        
        # Generate based on asset type
        if asset_type == "footprint":
            return self._generate_footprint(part, tool)
        elif asset_type == "symbol":
            return self._generate_symbol(part, tool)
        elif asset_type == "3d_model":
            return self._generate_3d_model(part, tool)
        
        return None
    
    def _generate_footprint(
        self,
        part: Dict[str, Any],
        tool: str
    ) -> Optional[Dict[str, Any]]:
        """Generate footprint file for a part."""
        if tool == "kicad":
            return self._generate_kicad_footprint(part)
        # Add other tools as needed
        return None
    
    def _generate_kicad_footprint(
        self,
        part: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate KiCad footprint (.kicad_mod) file."""
        part_id = part.get("id", part.get("mpn", ""))
        package = part.get("package", "")
        footprint_name = part.get("footprint", "")
        
        # Extract package dimensions if available
        package_info = part.get("package_info", {})
        width = package_info.get("width", 0)
        height = package_info.get("height", 0)
        pitch = package_info.get("pitch", 0)
        pin_count = part.get("pin_count", 0)
        
        # Generate basic footprint based on package type
        if "QFN" in package.upper() or "DFN" in package.upper():
            return self._generate_qfn_footprint(part_id, footprint_name, width, height, pitch, pin_count)
        elif "SOIC" in package.upper() or "SOP" in package.upper():
            return self._generate_soic_footprint(part_id, footprint_name, width, height, pitch, pin_count)
        elif "QFP" in package.upper():
            return self._generate_qfp_footprint(part_id, footprint_name, width, height, pitch, pin_count)
        elif "0603" in package or "0805" in package or "1206" in package:
            return self._generate_passive_footprint(part_id, footprint_name, package)
        elif "USB" in package.upper() or "CONNECTOR" in part.get("category", "").upper():
            return self._generate_connector_footprint(part_id, footprint_name, package, pin_count)
        
        # Generic footprint template
        return {
            "url": None,
            "content": self._kicad_footprint_template(part_id, footprint_name or part_id, package),
            "format": ".kicad_mod",
            "cached": False
        }
    
    def _generate_symbol(
        self,
        part: Dict[str, Any],
        tool: str
    ) -> Optional[Dict[str, Any]]:
        """Generate symbol file for a part."""
        if tool == "kicad":
            return self._generate_kicad_symbol(part)
        return None
    
    def _generate_kicad_symbol(
        self,
        part: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate KiCad symbol (.lib) file."""
        part_id = part.get("id", part.get("mpn", ""))
        manufacturer = part.get("manufacturer", "")
        description = part.get("description", "")
        pin_count = part.get("pin_count", 0)
        pinout = part.get("pinout", {})
        
        # Generate symbol based on part type
        symbol_content = self._kicad_symbol_template(part_id, manufacturer, description, pin_count, pinout)
        
        return {
            "url": None,
            "content": symbol_content,
            "format": ".lib",
            "cached": False
        }
    
    def _generate_3d_model(
        self,
        part: Dict[str, Any],
        tool: str
    ) -> Optional[Dict[str, Any]]:
        """Generate or fetch 3D model for a part."""
        # Try to fetch from online sources (e.g., 3D ContentCentral, GrabCAD)
        part_id = part.get("id", part.get("mpn", ""))
        manufacturer = part.get("manufacturer", "")
        
        # For now, return a placeholder
        # In production, this would fetch from 3D model repositories
        return {
            "url": f"https://www.3dcontentcentral.com/Download/Model.aspx?ID={part_id}",
            "content": None,
            "format": ".step",
            "cached": False,
            "note": "3D model URL - download from manufacturer or 3D ContentCentral"
        }
    
    def _generate_qfn_footprint(
        self,
        part_id: str,
        footprint_name: str,
        width: float,
        height: float,
        pitch: float,
        pin_count: int
    ) -> Dict[str, Any]:
        """Generate QFN footprint."""
        # Simplified QFN footprint generation
        # In production, use proper IPC-7351 calculations
        content = f"""(footprint "{footprint_name or part_id}" (version 20211014) (generator pcbnew)
  (layer "F.Cu")
  (descr "QFN package generated for {part_id}")
  (tags "QFN")
  (attr smd)
  (fp_text reference "REF**" (at 0 -2.5) (layer "F.SilkS")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value "{part_id}" (at 0 2.5) (layer "F.Fab")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text user "${{{footprint_name or part_id}}}" (at 0 0) (layer "F.Fab")
    (effects (font (size 0.5 0.5) (thickness 0.1)) hide)
  )
  (pad "1" smd roundrect (at {-width/2 + pitch/2} {-height/2 + pitch/2}) (size {pitch*0.8} {pitch*0.8}) (layers "F.Cu" "F.Paste" "F.Mask")
    (roundrect_rratio 0.25))
  (pad "EP" smd roundrect (at 0 0) (size {width*0.8} {height*0.8}) (layers "F.Cu" "F.Paste" "F.Mask")
    (roundrect_rratio 0.25))
)
"""
        return {
            "url": None,
            "content": content,
            "format": ".kicad_mod",
            "cached": False
        }
    
    def _generate_soic_footprint(
        self,
        part_id: str,
        footprint_name: str,
        width: float,
        height: float,
        pitch: float,
        pin_count: int
    ) -> Dict[str, Any]:
        """Generate SOIC footprint."""
        # Simplified SOIC footprint
        body_width = width or 3.9
        body_length = height or (pin_count * pitch / 2 + 1.27)
        pad_width = 0.6
        pad_length = 1.0
        
        content = f"""(footprint "{footprint_name or part_id}" (version 20211014) (generator pcbnew)
  (layer "F.Cu")
  (descr "SOIC package generated for {part_id}")
  (tags "SOIC")
  (attr smd)
  (fp_text reference "REF**" (at 0 {-body_length/2 - 1}) (layer "F.SilkS")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value "{part_id}" (at 0 {body_length/2 + 1}) (layer "F.Fab")
    (effects (font (size 1 1) (thickness 0.15)))
  )
"""
        # Add pads
        for i in range(1, pin_count + 1):
            if i <= pin_count / 2:
                x = -body_width / 2 - pad_length / 2
                y = -body_length / 2 + (i - 0.5) * pitch
            else:
                x = body_width / 2 + pad_length / 2
                y = body_length / 2 - (i - pin_count / 2 - 0.5) * pitch
            
            content += f'  (pad "{i}" smd roundrect (at {x} {y}) (size {pad_length} {pad_width}) (layers "F.Cu" "F.Paste" "F.Mask")\n    (roundrect_rratio 0.25))\n'
        
        content += ")\n"
        
        return {
            "url": None,
            "content": content,
            "format": ".kicad_mod",
            "cached": False
        }
    
    def _generate_qfp_footprint(
        self,
        part_id: str,
        footprint_name: str,
        width: float,
        height: float,
        pitch: float,
        pin_count: int
    ) -> Dict[str, Any]:
        """Generate QFP footprint."""
        # Similar to QFN but with leads
        return self._generate_qfn_footprint(part_id, footprint_name, width, height, pitch, pin_count)
    
    def _generate_passive_footprint(
        self,
        part_id: str,
        footprint_name: str,
        package: str
    ) -> Dict[str, Any]:
        """Generate passive component footprint (resistor, capacitor)."""
        # Standard passive footprints
        package_sizes = {
            "0603": (1.6, 0.8),
            "0805": (2.0, 1.25),
            "1206": (3.2, 1.6),
            "1210": (3.2, 2.5),
            "1812": (4.5, 3.2)
        }
        
        size = package_sizes.get(package, (2.0, 1.25))
        width, height = size
        
        content = f"""(footprint "{footprint_name or package}" (version 20211014) (generator pcbnew)
  (layer "F.Cu")
  (descr "{package} package")
  (tags "{package}")
  (attr smd)
  (fp_text reference "REF**" (at 0 {-height/2 - 0.5}) (layer "F.SilkS")
    (effects (font (size 0.8 0.8) (thickness 0.1)))
  )
  (fp_text value "{part_id}" (at 0 {height/2 + 0.5}) (layer "F.Fab")
    (effects (font (size 0.8 0.8) (thickness 0.1)))
  )
  (pad "1" smd roundrect (at {-width/2 + 0.4} 0) (size 0.8 {height*0.9}) (layers "F.Cu" "F.Paste" "F.Mask")
    (roundrect_rratio 0.25))
  (pad "2" smd roundrect (at {width/2 - 0.4} 0) (size 0.8 {height*0.9}) (layers "F.Cu" "F.Paste" "F.Mask")
    (roundrect_rratio 0.25))
)
"""
        return {
            "url": None,
            "content": content,
            "format": ".kicad_mod",
            "cached": False
        }
    
    def _generate_connector_footprint(
        self,
        part_id: str,
        footprint_name: str,
        package: str,
        pin_count: int
    ) -> Dict[str, Any]:
        """Generate connector footprint."""
        # Generic connector template
        return {
            "url": None,
            "content": self._kicad_footprint_template(part_id, footprint_name or part_id, package),
            "format": ".kicad_mod",
            "cached": False
        }
    
    def _kicad_footprint_template(
        self,
        part_id: str,
        footprint_name: str,
        package: str
    ) -> str:
        """Generic KiCad footprint template."""
        return f"""(footprint "{footprint_name}" (version 20211014) (generator pcbnew)
  (layer "F.Cu")
  (descr "Footprint for {part_id}")
  (tags "{package}")
  (attr smd)
  (fp_text reference "REF**" (at 0 -2) (layer "F.SilkS")
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value "{part_id}" (at 0 2) (layer "F.Fab")
    (effects (font (size 1 1) (thickness 0.15)))
  )
)
"""
    
    def _kicad_symbol_template(
        self,
        part_id: str,
        manufacturer: str,
        description: str,
        pin_count: int,
        pinout: Dict[str, Any]
    ) -> str:
        """Generate KiCad symbol library entry."""
        # Simplified symbol generation
        # In production, use proper pin placement based on pinout
        symbol_lines = [
            f"DEF {part_id} U 0 40 Y Y 1 F N",
            f"F0 \"U\" 0 0 50 H V C CNN",
            f"F1 \"{part_id}\" 0 0 50 H V C CNN",
            f"F2 \"{manufacturer}\" 0 0 50 H I C CNN",
            f"F3 \"{description}\" 0 0 50 H I C CNN",
            "DRAW"
        ]
        
        # Add pins (simplified - in production, use actual pinout)
        pin_spacing = 100
        start_y = -(pin_count // 2) * pin_spacing
        
        for i in range(1, min(pin_count + 1, 20)):  # Limit to 20 pins for template
            pin_name = pinout.get(f"pin_{i}", str(i))
            y_pos = start_y + (i - 1) * pin_spacing
            symbol_lines.append(f"X {pin_name} {i} -200 {y_pos} 100 R 50 50 1 1 I")
        
        symbol_lines.extend([
            "S -150 -200 150 200 0 1 0 N",
            "ENDDRAW",
            "ENDDEF"
        ])
        
        return "\n".join(symbol_lines)
    
    def download_eda_assets(
        self,
        part: Dict[str, Any],
        tool: str = "kicad",
        output_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Download/generate EDA assets and save to files.
        
        Returns:
            Dictionary mapping asset types to file paths
        """
        if output_dir is None:
            output_dir = self.asset_cache_dir / tool
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        assets = self.get_eda_assets(part, tool)
        saved_files = {}
        
        part_id = part.get("id", part.get("mpn", ""))
        
        for asset_type, asset_data in assets.items():
            if asset_data.get("content"):
                file_ext = asset_data.get("format", "")
                filename = f"{part_id}_{asset_type}{file_ext}"
                file_path = output_dir / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(asset_data["content"])
                
                saved_files[asset_type] = file_path
        
        return saved_files

