"""
Cost Utilities
Safe extraction of cost values from various data structures
"""

from typing import Any, Union


def safe_extract_cost(cost_data: Any, default: float = 0.0) -> float:
    """
    Safely extract a numeric cost value from various data structures.
    
    Handles:
    - Direct numeric values (int, float)
    - Dict with 'value', 'unit', 'cost' keys
    - Nested dicts
    - None or missing values
    
    Args:
        cost_data: Cost data in any format
        default: Default value if extraction fails
    
    Returns:
        Float cost value
    """
    if cost_data is None:
        return default
    
    # Direct numeric value
    if isinstance(cost_data, (int, float)):
        return float(cost_data)
    
    # Dict structure
    if isinstance(cost_data, dict):
        # Try common keys in order of preference
        for key in ["value", "unit", "cost", "price"]:
            if key in cost_data:
                value = cost_data[key]
                # If value is still a dict, recurse
                if isinstance(value, dict):
                    return safe_extract_cost(value, default)
                # If value is numeric, return it
                if isinstance(value, (int, float)):
                    return float(value)
                # If value is a string that looks like a number, try to parse
                if isinstance(value, str):
                    try:
                        # Remove currency symbols and whitespace
                        cleaned = value.replace("$", "").replace(",", "").strip()
                        return float(cleaned)
                    except (ValueError, AttributeError):
                        continue
        
        # If no valid key found, return default
        return default
    
    # String that might be a number
    if isinstance(cost_data, str):
        try:
            cleaned = cost_data.replace("$", "").replace(",", "").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return default
    
    # Unknown type, return default
    return default


def safe_extract_quantity(quantity_data: Any, default: int = 1) -> int:
    """
    Safely extract a numeric quantity value.
    
    Args:
        quantity_data: Quantity data in any format
        default: Default value if extraction fails
    
    Returns:
        Integer quantity value
    """
    if quantity_data is None:
        return default
    
    if isinstance(quantity_data, int):
        return max(1, quantity_data)  # Ensure at least 1
    
    if isinstance(quantity_data, float):
        return max(1, int(quantity_data))
    
    if isinstance(quantity_data, str):
        try:
            return max(1, int(float(quantity_data)))
        except (ValueError, TypeError):
            return default
    
    return default

