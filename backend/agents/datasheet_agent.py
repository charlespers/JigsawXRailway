"""
Datasheet Parsing & Enrichment Agent
Mock PDF parsing - extracts missing attributes from datasheet cache
"""

from typing import Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.part_database import get_datasheet_data, get_part_by_id


class DatasheetAgent:
    """Agent that enriches part data from datasheet cache (mock PDF parsing)."""
    
    def enrich_part(self, part_id: str) -> Dict[str, Any]:
        """
        Enrich a part with data from datasheet cache.
        
        Args:
            part_id: ID of the part to enrich
        
        Returns:
            Dictionary with enriched attributes
        """
        part = get_part_by_id(part_id)
        if not part:
            return {}
        
        # Get datasheet data (mock PDF parsing result)
        datasheet_data = get_datasheet_data(part_id)
        
        enriched = part.copy()
        
        if datasheet_data:
            # Merge datasheet data into part
            # Pin descriptions
            if "pin_descriptions" in datasheet_data:
                if "pinout" not in enriched or not enriched["pinout"]:
                    enriched["pinout"] = datasheet_data["pin_descriptions"]
                else:
                    # Merge pin descriptions
                    for pin, desc in datasheet_data["pin_descriptions"].items():
                        if pin in enriched["pinout"]:
                            if isinstance(enriched["pinout"][pin], str):
                                enriched["pinout"][pin] = {
                                    "description": enriched["pinout"][pin],
                                    "datasheet_note": desc
                                }
            
            # Electrical characteristics
            if "electrical_characteristics" in datasheet_data:
                elec = datasheet_data["electrical_characteristics"]
                for key, value in elec.items():
                    if key not in enriched or not enriched[key]:
                        enriched[key] = value
            
            # Application circuit
            if "application_circuit" in datasheet_data:
                enriched["datasheet_application_circuit"] = datasheet_data["application_circuit"]
        
        return enriched
    
    def get_missing_fields(self, part_id: str, required_fields: list) -> Dict[str, Any]:
        """
        Check which required fields are missing and try to fill them from datasheet.
        
        Args:
            part_id: ID of the part
            required_fields: List of field names that are required
        
        Returns:
            Dictionary with missing fields filled (if available in datasheet)
        """
        part = get_part_by_id(part_id)
        if not part:
            return {}
        
        missing = {}
        datasheet_data = get_datasheet_data(part_id)
        
        for field in required_fields:
            if field not in part or not part[field]:
                # Try to find in datasheet data
                if datasheet_data:
                    # Map common field names
                    field_map = {
                        "supply_voltage_range": "electrical_characteristics.supply_voltage",
                        "io_voltage_levels": "electrical_characteristics.i2c_input_high_voltage",
                        "pinout": "pin_descriptions"
                    }
                    
                    if field in field_map:
                        mapped_path = field_map[field]
                        # Simple path traversal
                        if "." in mapped_path:
                            section, subfield = mapped_path.split(".", 1)
                            if section in datasheet_data:
                                section_data = datasheet_data[section]
                                if subfield in section_data:
                                    missing[field] = section_data[subfield]
        
        return missing

