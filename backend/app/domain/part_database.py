"""
Part database interface
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from app.domain.models import Part, ComponentCategory
from app.core.config import settings

logger = logging.getLogger(__name__)


class PartDatabase:
    """Part database with caching and search"""
    
    def __init__(self):
        # Resolve path - handle both local dev and Railway deployment
        # In Railway: __file__ = /app/app/domain/part_database.py
        # In local: __file__ = backend/app/domain/part_database.py
        current_file = Path(__file__)
        app_dir = current_file.parent.parent.parent  # backend/ or /app
        
        db_path_str = settings.PARTS_DATABASE_PATH
        
        # Build list of paths to try (in order of preference)
        paths_to_try = []
        
        # 1. Absolute path (if provided)
        if db_path_str.startswith("/"):
            paths_to_try.append(Path(db_path_str))
        
        # 2. Relative to app directory: app/data/parts -> app_dir/app/data/parts
        if db_path_str.startswith("app/"):
            paths_to_try.append(app_dir / db_path_str)
            # Also try without "app/" prefix
            paths_to_try.append(app_dir / db_path_str.replace("app/", ""))
        
        # 3. Relative to current file location
        paths_to_try.append(current_file.parent.parent / "data" / "parts")
        
        # 4. Fallback locations (Railway-specific paths first)
        # In Railway, working dir is /app, so code is at /app/app/...
        paths_to_try.extend([
            Path("/app/app/data/parts"),  # Railway: code at /app/app, data at /app/app/data/parts
            current_file.parent.parent / "data" / "parts",  # Relative from part_database.py: app/data/parts
            app_dir / "app" / "data" / "parts",  # Local: backend/app/data/parts or Railway: /app/app/data/parts
            Path("/app/data/parts"),  # Railway alternative (if code structure differs)
            app_dir / "data" / "parts",  # backend/data/parts
            # Also try relative to where we are
            Path(__file__).parent.parent / "data" / "parts",  # app/data/parts from part_database.py
        ])
        
        # Try each path until we find one that exists
        self.db_path = None
        for path in paths_to_try:
            if path.exists() and path.is_dir():
                self.db_path = path
                logger.info(f"Found parts database at: {path}")
                break
        
        if not self.db_path:
            # Use first path as default (will log warning in _load_database)
            self.db_path = paths_to_try[0] if paths_to_try else Path(db_path_str)
            logger.warning(f"Parts database path not found. Will try: {self.db_path}")
        
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_database()
    
    def _load_database(self):
        """Load all part databases"""
        if not self.db_path.exists():
            logger.warning(f"Parts database path not found: {self.db_path}")
            return
        
        part_files = [
            "parts_base.json",
            "parts_mcu.json",
            "parts_sensors.json",
            "parts_power.json",
            "parts_connectors.json",
            "parts_passives.json",
            "parts_ics.json",
            "parts_intermediaries.json",
            "parts_mechanical.json",
            "parts_misc.json"
        ]
        
        for part_file in part_files:
            file_path = self.db_path / part_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for part in data:
                                if 'id' in part:
                                    self._cache[part['id']] = part
                        elif isinstance(data, dict) and 'parts' in data:
                            for part in data['parts']:
                                if 'id' in part:
                                    self._cache[part['id']] = part
                    logger.info(f"Loaded {len([p for p in self._cache.values() if part_file.replace('parts_', '').replace('.json', '') in str(p.get('category', ''))])} parts from {part_file}")
                except Exception as e:
                    logger.error(f"Error loading {part_file}: {e}")
        
        logger.info(f"Total parts loaded: {len(self._cache)}")
    
    def get_part(self, part_id: str) -> Optional[Dict[str, Any]]:
        """Get part by ID"""
        return self._cache.get(part_id)
    
    def search_parts(
        self,
        category: Optional[ComponentCategory] = None,
        interface: Optional[str] = None,
        voltage_range: Optional[tuple] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """Search parts by criteria"""
        results = []
        
        for part in self._cache.values():
            # Category filter
            if category and part.get('category') != category.value:
                continue
            
            # Interface filter
            if interface:
                part_interfaces = part.get('interface_type', [])
                if isinstance(part_interfaces, str):
                    part_interfaces = [part_interfaces]
                if interface.lower() not in [i.lower() for i in part_interfaces]:
                    continue
            
            # Voltage range filter
            if voltage_range:
                supply_range = part.get('supply_voltage_range', {})
                if isinstance(supply_range, dict):
                    min_v = supply_range.get('min', 0)
                    max_v = supply_range.get('max', float('inf'))
                    if not (voltage_range[0] <= max_v and voltage_range[1] >= min_v):
                        continue
            
            # Additional filters
            match = True
            for key, value in filters.items():
                if part.get(key) != value:
                    match = False
                    break
            
            if match:
                results.append(part)
        
        return results
    
    def get_all_parts(self) -> List[Dict[str, Any]]:
        """Get all parts"""
        return list(self._cache.values())


# Singleton instance
_part_database: Optional[PartDatabase] = None


def get_part_database() -> PartDatabase:
    """Get singleton part database instance"""
    global _part_database
    if _part_database is None:
        _part_database = PartDatabase()
    return _part_database

