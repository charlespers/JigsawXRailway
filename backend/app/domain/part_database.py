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
        # Resolve path relative to app directory
        # __file__ is app/domain/part_database.py, so:
        # parent = app/domain
        # parent.parent = app/
        # parent.parent.parent = backend/
        app_dir = Path(__file__).parent.parent.parent
        db_path_str = settings.PARTS_DATABASE_PATH
        
        # Handle both relative and absolute paths
        if db_path_str.startswith("/"):
            # Absolute path
            self.db_path = Path(db_path_str)
        elif db_path_str.startswith("app/"):
            # Relative to backend root: app/data/parts
            self.db_path = app_dir / db_path_str.replace("app/", "")
        else:
            # Relative path, assume it's relative to backend root
            self.db_path = app_dir / db_path_str
        
        # Fallback: try multiple possible locations
        if not self.db_path.exists():
            # Try relative to backend root: app/data/parts
            fallback1 = app_dir / "app" / "data" / "parts"
            # Try absolute: /app/data/parts (Railway deployment)
            fallback2 = Path("/app/data/parts")
            # Try relative to current file: ../../data/parts
            fallback3 = Path(__file__).parent.parent.parent / "app" / "data" / "parts"
            
            for fallback in [fallback1, fallback2, fallback3]:
                if fallback.exists():
                    logger.info(f"Using fallback path: {fallback}")
                    self.db_path = fallback
                    break
            else:
                logger.warning(f"Parts database path not found. Tried: {self.db_path}, {fallback1}, {fallback2}, {fallback3}")
        
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

