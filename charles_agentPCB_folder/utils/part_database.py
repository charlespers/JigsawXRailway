"""
Part Database Utilities
Load and query the part database
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


def get_database_path() -> Path:
    """Get the path to the part database directory."""
    current_file = Path(__file__)
    return current_file.parent.parent / "data" / "part_database"


def load_part_database() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load all part files from the database.
    Returns a dictionary mapping category names to lists of parts.
    """
    db_path = get_database_path()
    database = {}
    
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
    }
    
    for category, filename in category_files.items():
        file_path = db_path / filename
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
                database[category] = data.get("parts", [])
        else:
            database[category] = []
    
    return database


def get_all_parts() -> List[Dict[str, Any]]:
    """Get all parts from the database as a flat list."""
    database = load_part_database()
    all_parts = []
    for parts_list in database.values():
        all_parts.extend(parts_list)
    return all_parts


def get_part_by_id(part_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific part by its ID."""
    all_parts = get_all_parts()
    for part in all_parts:
        if part.get("id") == part_id:
            return part
    return None


def search_parts(
    category: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search for parts matching the given criteria.
    
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
    all_parts = get_all_parts()
    matches = []
    
    for part in all_parts:
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
        
        # Prefer higher efficiency
        efficiency = part.get("efficiency", 0)
        if efficiency:
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

