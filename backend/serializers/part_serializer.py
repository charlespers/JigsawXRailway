"""
Data Mapper
Converts our BOM/part format to React PartObject format
"""

from typing import Dict, Any, List, Optional


def format_voltage_range(voltage_range: Optional[Dict[str, Any]]) -> str:
    """Format voltage range to string."""
    if not voltage_range:
        return ""
    
    if isinstance(voltage_range, dict):
        min_v = voltage_range.get("min")
        max_v = voltage_range.get("max")
        nominal = voltage_range.get("nominal") or voltage_range.get("value")
        
        if min_v and max_v:
            return f"{min_v}V ~ {max_v}V"
        elif nominal:
            return f"{nominal}V"
    
    return str(voltage_range)


def get_datasheet_url(part_data: Dict[str, Any]) -> str:
    """Extract datasheet URL from part data."""
    return part_data.get("datasheet_url", "")


def bom_item_to_part_object(bom_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert BOM item to React PartObject format.
    
    Args:
        bom_item: BOM item from our system
    
    Returns:
        PartObject compatible dictionary
    """
    # Extract voltage from various sources
    voltage = ""
    if bom_item.get("value"):
        # Check if value contains voltage info
        value_str = str(bom_item["value"])
        if "V" in value_str:
            voltage = value_str
    
    # Try to get voltage from part data if available
    if not voltage:
        # This would need access to full part data, but for now use value
        pass
    
    # Extract interfaces
    interfaces = []
    if bom_item.get("category"):
        # Map category to interfaces if applicable
        category = bom_item["category"].lower()
        if "i2c" in category:
            interfaces.append("I2C")
        if "spi" in category:
            interfaces.append("SPI")
        if "uart" in category:
            interfaces.append("UART")
        if "wifi" in category or "wifi_module" in category:
            interfaces.append("WiFi")
        if "usb" in category:
            interfaces.append("USB")
    
    part_object = {
        "mpn": bom_item.get("mfr_part_number", bom_item.get("designator", "")),
        "manufacturer": bom_item.get("manufacturer", ""),
        "description": bom_item.get("description", ""),
        "price": bom_item.get("unit_cost", 0.0),
        "currency": "USD",
        "voltage": voltage or bom_item.get("value", ""),
        "package": bom_item.get("package", ""),
        "interfaces": interfaces,
        "datasheet": "",  # Will be filled from part data if available
        "quantity": bom_item.get("qty", 1),
        # Extended fields
        "tolerance": bom_item.get("tolerance", ""),
        "lifecycle_status": bom_item.get("lifecycle_status", ""),
        "rohs_compliant": bom_item.get("rohs_compliant", True),
        "lead_time_days": bom_item.get("lead_time_days"),
        "mounting_type": bom_item.get("mounting_type", ""),
        "category": bom_item.get("category", ""),
    }
    
    return part_object


def part_data_to_part_object(part_data: Dict[str, Any], quantity: int = 1, component_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert full part data to React PartObject format.
    
    Args:
        part_data: Full part data from our database
        quantity: Quantity for this part
        component_id: CRITICAL - The component/block identifier (maps to backend block_name)
    
    Returns:
        PartObject compatible dictionary with componentId preserved
    """
    # Extract interfaces
    interfaces = []
    interface_type = part_data.get("interface_type", [])
    if isinstance(interface_type, list):
        interfaces = interface_type
    elif isinstance(interface_type, str):
        interfaces = [interface_type]
    
    # Format voltage
    voltage = format_voltage_range(part_data.get("supply_voltage_range"))
    
    # Extract cost - safe extraction to handle nested dicts
    from utils.cost_utils import safe_extract_cost
    cost_estimate = part_data.get("cost_estimate", {})
    unit_cost = safe_extract_cost(cost_estimate, default=0.0)
    
    # Extract footprint (IPC-7351 compliant)
    footprint = part_data.get("footprint", "")
    if not footprint and part_data.get("package"):
        # Generate basic footprint name from package
        package = str(part_data.get("package", "")).upper()
        if "QFN" in package:
            footprint = f"{package}_IPC7351"
        elif "SOIC" in package:
            footprint = f"{package}_IPC7351"
        else:
            footprint = package
    
    # Extract MSL level
    msl_level = part_data.get("msl_level") or part_data.get("moisture_sensitivity_level")
    
    part_object = {
        # CRITICAL: Preserve componentId for frontend-backend mapping
        "componentId": component_id or part_data.get("componentId") or part_data.get("id", ""),
        "mpn": part_data.get("mfr_part_number", part_data.get("id", "")),
        "manufacturer": part_data.get("manufacturer", ""),
        "description": part_data.get("description", ""),
        "price": unit_cost,
        "currency": "USD",
        "voltage": voltage,
        "package": part_data.get("package", ""),
        "interfaces": interfaces,
        "datasheet": part_data.get("datasheet_url", ""),
        "quantity": quantity,
        # Extended fields
        "tolerance": part_data.get("tolerance", ""),
        "lifecycle_status": part_data.get("lifecycle_status", "active"),
        "rohs_compliant": part_data.get("rohs_compliant", True),
        "lead_time_days": part_data.get("lead_time_days"),
        "mounting_type": "SMT" if "SMT" in str(part_data.get("package", "")).upper() else "through_hole",
        "category": part_data.get("category", ""),
        # BOM fields
        "footprint": footprint,
        "msl_level": msl_level,
        "assembly_side": part_data.get("assembly_side", "top"),
        "alternate_part_numbers": part_data.get("alternate_part_numbers", []),
        "distributor_part_numbers": part_data.get("distributor_part_numbers", {}),
        "temperature_rating": part_data.get("operating_temp_range", {}).get("max") if isinstance(part_data.get("operating_temp_range"), dict) else None,
        "availability_status": part_data.get("availability_status", "unknown"),
        "test_point": part_data.get("test_point", False),
        "fiducial": part_data.get("fiducial", False),
        "assembly_notes": part_data.get("assembly_notes", ""),
    }
    
    return part_object

