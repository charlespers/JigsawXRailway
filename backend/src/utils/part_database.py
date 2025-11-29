"""
Part Database Utilities
Load and query the part database with validation and caching
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Required fields for a valid part
REQUIRED_PART_FIELDS = ["id", "mpn", "manufacturer", "category"]
OPTIONAL_PART_FIELDS = [
    "description", "supply_voltage_range", "interface_type", "operating_temp_range",
    "cost_estimate", "availability_status", "lifecycle_status", "datasheet_url",
    "package_type", "pin_count", "recommended_external_components"
]


def get_database_path() -> Path:
    """Get the path to the part database directory."""
    current_file = Path(__file__)
    return current_file.parent.parent / "data" / "part_database"


def validate_part(part: Dict[str, Any], category: str) -> tuple[bool, Optional[str]]:
    """
    Validate a part dictionary has required fields and valid types.
    
    Returns:
        (is_valid, error_message)
    """
    # Check required fields
    for field in REQUIRED_PART_FIELDS:
        if field not in part:
            return False, f"Missing required field: {field}"
    
    # Validate field types
    if not isinstance(part["id"], str) or not part["id"]:
        return False, "Field 'id' must be a non-empty string"
    if not isinstance(part["mpn"], str) or not part["mpn"]:
        return False, "Field 'mpn' must be a non-empty string"
    if not isinstance(part["manufacturer"], str) or not part["manufacturer"]:
        return False, "Field 'manufacturer' must be a non-empty string"
    if not isinstance(part["category"], str):
        return False, "Field 'category' must be a string"
    
    # Validate numeric fields if present
    if "cost_estimate" in part and part["cost_estimate"] is not None:
        try:
            float(part["cost_estimate"])
        except (ValueError, TypeError):
            return False, "Field 'cost_estimate' must be a number"
    
    # Validate voltage range if present
    if "supply_voltage_range" in part and part["supply_voltage_range"] is not None:
        vr = part["supply_voltage_range"]
        if isinstance(vr, dict):
            if "min" in vr and not isinstance(vr["min"], (int, float)):
                return False, "supply_voltage_range.min must be a number"
            if "max" in vr and not isinstance(vr["max"], (int, float)):
                return False, "supply_voltage_range.max must be a number"
    
    return True, None


@lru_cache(maxsize=1)
def load_part_database() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load all part files from the database with validation.
    Results are cached to improve performance.
    Returns a dictionary mapping category names to lists of parts.
    """
    db_path = get_database_path()
    database = {}
    validation_errors = []
    
    # Load each category file
    category_files = {
        "mcu": "parts_mcu.json",
        "sensors": "parts_sensors.json",
        "power": "parts_power.json",
        "passives": "parts_passives.json",
        "connectors": "parts_connectors.json",
        "ics": "parts_ics.json",
        "mechanical": "parts_mechanical.json",
        "misc": "parts_misc.json",
        "intermediaries": "parts_intermediaries.json",
    }
    
    for category, filename in category_files.items():
        file_path = db_path / filename
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    parts = data.get("parts", [])
                    
                    # Validate each part
                    valid_parts = []
                    for i, part in enumerate(parts):
                        is_valid, error = validate_part(part, category)
                        if is_valid:
                            valid_parts.append(part)
                        else:
                            validation_errors.append(f"{filename}[{i}]: {error}")
                            logger.warning(f"[DB_VALIDATION] Invalid part in {filename}[{i}]: {error}")
                    
                    database[category] = valid_parts
                    logger.info(f"[DB] Loaded {len(valid_parts)} valid parts from {filename} (skipped {len(parts) - len(valid_parts)} invalid)")
            except json.JSONDecodeError as e:
                logger.error(f"[DB] Invalid JSON in {filename}: {e}")
                database[category] = []
            except Exception as e:
                logger.error(f"[DB] Error loading {filename}: {e}", exc_info=True)
                database[category] = []
        else:
            logger.warning(f"[DB] File not found: {filename}")
            database[category] = []
    
    if validation_errors:
        logger.warning(f"[DB_VALIDATION] Found {len(validation_errors)} validation errors (see logs above)")
    
    return database


# Cache for all parts to improve performance
_all_parts_cache: Optional[List[Dict[str, Any]]] = None
_parts_index_cache: Optional[Dict[str, Dict[str, Any]]] = None  # Index by part ID
_category_index_cache: Optional[Dict[str, List[Dict[str, Any]]]] = None  # Index by category

def get_all_parts() -> List[Dict[str, Any]]:
    """Get all parts from the database as a flat list (cached)."""
    global _all_parts_cache
    if _all_parts_cache is None:
        database = load_part_database()
        all_parts = []
        for parts_list in database.values():
            all_parts.extend(parts_list)
        _all_parts_cache = all_parts
        logger.info(f"[DB_CACHE] Loaded {len(all_parts)} parts into cache")
    return _all_parts_cache

def _build_indexes():
    """Build search indexes for faster lookups."""
    global _parts_index_cache, _category_index_cache
    if _parts_index_cache is None or _category_index_cache is None:
        all_parts = get_all_parts()
        _parts_index_cache = {}
        _category_index_cache = {}
        for part in all_parts:
            part_id = part.get("id", "")
            if part_id:
                _parts_index_cache[part_id] = part
            category = part.get("category", "")
            if category:
                if category not in _category_index_cache:
                    _category_index_cache[category] = []
                _category_index_cache[category].append(part)
        logger.info(f"[DB_INDEX] Built indexes: {len(_parts_index_cache)} parts, {len(_category_index_cache)} categories")


def get_part_by_id(part_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific part by its ID (indexed lookup)."""
    _build_indexes()
    return _parts_index_cache.get(part_id) if _parts_index_cache else None


# Search result cache with TTL
from functools import lru_cache
import hashlib
import json as json_module

def _cache_key(category: Optional[str], constraints: Optional[Dict[str, Any]]) -> str:
    """Generate cache key for search query."""
    key_data = {"category": category, "constraints": constraints}
    key_str = json_module.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()

_search_cache: Dict[str, tuple[List[Dict[str, Any]], float]] = {}
_cache_ttl = 300.0  # 5 minutes

def search_parts(
    category: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search for parts matching the given criteria (with caching and indexing).
    
    Args:
        category: Part category to filter by (e.g., "mcu_wifi", "sensor_temperature")
        constraints: Dictionary of constraints to match:
            - supply_voltage_range: dict with min/max/nominal
            - interface_type: list of interfaces (e.g., ["I2C", "WiFi"])
            - operating_temp_range: dict with min/max
            - availability_status: "in_stock", etc.
            - lifecycle_status: "active", etc.
    
    Returns:
        List of matching parts
    """
    # Check cache first
    cache_key = _cache_key(category, constraints)
    if cache_key in _search_cache:
        results, timestamp = _search_cache[cache_key]
        if time.time() - timestamp < _cache_ttl:
            logger.debug(f"[DB_CACHE] Cache hit for search: {cache_key[:8]}")
            return results
    
    # Use indexed lookup if category is specified
    if category and _category_index_cache:
        _build_indexes()
        parts_to_search = _category_index_cache.get(category, [])
        if not parts_to_search:
            # Try partial match
            parts_to_search = [p for cat, parts in _category_index_cache.items() if category in cat for p in parts]
    else:
        parts_to_search = get_all_parts()
    
    matches = []
    
    for part in parts_to_search:
        # Category filter
        if category:
            part_category = part.get("category", "")
            if category not in part_category and part_category != category:
                continue
        
        # Constraint filters
        if constraints:
            matches_constraints = True
            
            # Supply voltage range check
            if "supply_voltage_range" in constraints:
                req_range = constraints["supply_voltage_range"]
                part_range = part.get("supply_voltage_range")
                if part_range:
                    req_min = req_range.get("min")
                    req_max = req_range.get("max")
                    req_nominal = req_range.get("nominal")
                    
                    part_min = part_range.get("min")
                    part_max = part_range.get("max")
                    part_nominal = part_range.get("nominal")
                    
                    # Check if ranges overlap
                    if req_nominal:
                        if part_min and req_nominal < part_min:
                            matches_constraints = False
                        if part_max and req_nominal > part_max:
                            matches_constraints = False
                    elif req_min and req_max:
                        # Check range overlap
                        if part_max and req_min > part_max:
                            matches_constraints = False
                        if part_min and req_max < part_min:
                            matches_constraints = False
            
            # Interface type check
            if "interface_type" in constraints:
                req_interfaces = constraints["interface_type"]
                if isinstance(req_interfaces, str):
                    req_interfaces = [req_interfaces]
                part_interfaces = part.get("interface_type", [])
                if not isinstance(part_interfaces, list):
                    part_interfaces = [part_interfaces]
                
                # Check if any required interface is present
                if not any(iface in part_interfaces for iface in req_interfaces):
                    matches_constraints = False
            
            # Operating temperature range check
            if "operating_temp_range" in constraints:
                req_temp = constraints["operating_temp_range"]
                part_temp = part.get("operating_temp_range")
                if part_temp:
                    req_min = req_temp.get("min")
                    req_max = req_temp.get("max")
                    part_min = part_temp.get("min")
                    part_max = part_temp.get("max")
                    
                    # Check if ranges overlap
                    if req_min is not None and part_max is not None and req_min > part_max:
                        matches_constraints = False
                    if req_max is not None and part_min is not None and req_max < part_min:
                        matches_constraints = False
            
            # Availability status check
            if "availability_status" in constraints:
                req_status = constraints["availability_status"]
                part_status = part.get("availability_status")
                if part_status != req_status:
                    matches_constraints = False
            
            # Lifecycle status check
            if "lifecycle_status" in constraints:
                req_status = constraints["lifecycle_status"]
                part_status = part.get("lifecycle_status")
                if part_status != req_status:
                    matches_constraints = False
            
            if not matches_constraints:
                continue
        
        matches.append(part)
    
    return matches


def get_application_template(part_id: str) -> Optional[Dict[str, Any]]:
    """Get the recommended application circuit template for a part."""
    part = get_part_by_id(part_id)
    if part:
        return part.get("typical_circuit")
    return None


def get_recommended_external_components(part_id: str) -> List[Dict[str, Any]]:
    """Get the list of recommended external components for a part."""
    part = get_part_by_id(part_id)
    if part:
        return part.get("recommended_external_components", [])
    return []


def load_datasheet_cache() -> Dict[str, Any]:
    """Load the datasheet cache (mock extracted PDF data)."""
    db_path = get_database_path()
    cache_path = db_path / "datasheet_cache.json"
    
    if cache_path.exists():
        with open(cache_path, 'r') as f:
            data = json.load(f)
            return data.get("extracted_data", {})
    return {}


def get_datasheet_data(part_id: str) -> Optional[Dict[str, Any]]:
    """Get extracted datasheet data for a part (mock PDF parsing result)."""
    cache = load_datasheet_cache()
    return cache.get(part_id)


# Voltage converter cache (in-memory)
_voltage_converter_cache: Dict[str, List[Dict[str, Any]]] = {}


def search_voltage_converters(
    input_voltage: float,
    output_voltage: float,
    min_current: float = 0.0,
    converter_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for voltage conversion components (buck, boost, LDO, level shifter).
    
    Args:
        input_voltage: Input voltage in volts
        output_voltage: Desired output voltage in volts
        min_current: Minimum current capacity in amperes
        converter_type: Optional filter for converter type ("regulator_buck", "regulator_boost", 
                        "regulator_ldo", "level_shifter")
    
    Returns:
        List of matching voltage converter parts
    """
    # Check cache first
    cache_key = f"{input_voltage}_{output_voltage}_{min_current}_{converter_type or 'any'}"
    if cache_key in _voltage_converter_cache:
        return _voltage_converter_cache[cache_key]
    
    all_parts = get_all_parts()
    candidates = []
    
    # Categories that contain voltage converters
    converter_categories = [
        "regulator_buck",
        "regulator_boost",
        "regulator_ldo",
        "level_shifter"
    ]
    
    for part in all_parts:
        category = part.get("category", "")
        
        # Filter by converter type if specified
        if converter_type and converter_type not in category:
            continue
        
        # Only consider voltage converter categories
        if not any(cat in category for cat in converter_categories):
            continue
        
        # Check input voltage range
        input_range = part.get("input_voltage_range") or part.get("supply_voltage_range")
        if input_range:
            input_min = input_range.get("min")
            input_max = input_range.get("max")
            if input_min and input_max:
                if not (input_min <= input_voltage <= input_max):
                    continue
        
        # Check output voltage
        output_voltage_spec = part.get("output_voltage")
        if output_voltage_spec:
            if isinstance(output_voltage_spec, dict):
                part_output = output_voltage_spec.get("nominal") or output_voltage_spec.get("value")
            else:
                part_output = output_voltage_spec
            
            # Allow small tolerance (±0.1V)
            if part_output and abs(part_output - output_voltage) > 0.1:
                # Check if adjustable
                if not part.get("adjustable", False):
                    continue
        
        # Check current capacity
        current_max = part.get("current_max", {})
        if isinstance(current_max, dict):
            part_current = current_max.get("max") or current_max.get("typical", 0)
        else:
            part_current = current_max or 0
        
        if min_current > 0 and part_current > 0 and part_current < min_current:
            continue
        
        candidates.append(part)
    
    # Cache results
    _voltage_converter_cache[cache_key] = candidates
    return candidates


def get_intermediary_candidates(
    voltage_gap: Dict[str, Any],
    connection_type: str = "power"
) -> List[Dict[str, Any]]:
    """
    Get intermediary component candidates for a voltage gap.
    
    Args:
        voltage_gap: Dictionary with source_voltage, target_min, target_max, target_nominal
        connection_type: "power" or "signal"
    
    Returns:
        Ranked list of intermediary candidates
    """
    source_voltage = voltage_gap.get("source_voltage")
    target_min = voltage_gap.get("target_min")
    target_max = voltage_gap.get("target_max")
    target_nominal = voltage_gap.get("target_nominal")
    
    if not source_voltage or not target_min or not target_max:
        return []
    
    # Use nominal if available, otherwise midpoint
    if target_nominal:
        output_voltage = target_nominal
    else:
        output_voltage = (target_min + target_max) / 2
    
    # Determine converter type based on voltage relationship
    voltage_diff = source_voltage - output_voltage
    
    if connection_type == "signal":
        # For signals, use level shifter
        candidates = search_voltage_converters(
            source_voltage, output_voltage, 0.0, "level_shifter"
        )
    elif abs(voltage_diff) < 1.0 and voltage_diff > 0:
        # Small drop (<1V), prefer LDO
        candidates = search_voltage_converters(
            source_voltage, output_voltage, 0.0, "regulator_ldo"
        )
        # Also check buck converters
        candidates.extend(search_voltage_converters(
            source_voltage, output_voltage, 0.0, "regulator_buck"
        ))
    elif voltage_diff > 0:
        # Step down, prefer buck converter
        candidates = search_voltage_converters(
            source_voltage, output_voltage, 0.0, "regulator_buck"
        )
        # Also check LDO for small drops
        if voltage_diff < 1.5:
            candidates.extend(search_voltage_converters(
                source_voltage, output_voltage, 0.0, "regulator_ldo"
            ))
    else:
        # Step up, use boost converter
        candidates = search_voltage_converters(
            source_voltage, output_voltage, 0.0, "regulator_boost"
        )
    
    # Remove duplicates (by part ID)
    seen_ids = set()
    unique_candidates = []
    for candidate in candidates:
        part_id = candidate.get("id")
        if part_id and part_id not in seen_ids:
            seen_ids.add(part_id)
            unique_candidates.append(candidate)
    
    # Rank by preference: efficiency, current capacity, cost
    def rank_score(part: Dict[str, Any]) -> float:
        score = 0.0
        
        # Prefer higher efficiency - use safe_float_extract for consistency
        from agents.design_analyzer import safe_float_extract
        efficiency_val = part.get("efficiency", 0)
        efficiency = safe_float_extract(
            efficiency_val,
            default=0.0,
            context=f"efficiency for {part.get('id', 'unknown')}"
        )
        
        if efficiency > 0:
            score += efficiency * 0.4
        
        # Prefer higher current capacity
        current_max = part.get("current_max", {})
        if isinstance(current_max, dict):
            current = current_max.get("max", 0)
        else:
            current = current_max or 0
        if current > 0:
            score += min(current * 10, 0.3)  # Cap at 0.3
        
        # Prefer lower cost
        cost = part.get("cost", {})
        if isinstance(cost, dict):
            unit_cost = cost.get("unit", 0)
        else:
            unit_cost = cost or 0
        if unit_cost > 0:
            score += max(0, 0.3 - (unit_cost / 10))  # Lower cost = higher score
        
        return score
    
    # Sort by score (descending)
    unique_candidates.sort(key=rank_score, reverse=True)
    
    return unique_candidates

