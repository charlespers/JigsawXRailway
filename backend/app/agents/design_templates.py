"""
Design Templates Agent
Pre-built design patterns for common applications
"""
import logging
from typing import Dict, List, Any, Optional
from app.domain.part_database import get_part_database
from app.agents.intelligent_matcher import IntelligentMatcherAgent

logger = logging.getLogger(__name__)


class DesignTemplatesAgent:
    """
    Provides design templates for common PCB applications.
    
    Solves: "I need a battery-powered sensor node" → Gets complete design template
            with all parts pre-selected and validated
    """
    
    TEMPLATES = {
        "battery_sensor_node": {
            "name": "Battery-Powered Sensor Node",
            "description": "Complete design for IoT sensor node with WiFi, battery management",
            "requirements": {
                "functional_requirements": [
                    "Low-power MCU with WiFi",
                    "Sensor interface (I2C/SPI)",
                    "Battery management",
                    "Power regulation",
                    "Low power consumption"
                ],
                "technical_specs": {
                    "voltage_range": {"min": 2.7, "max": 4.2},  # Li-ion battery
                    "power_consumption": "low",
                    "interfaces": ["WiFi", "I2C", "SPI"],
                    "operating_temp": {"min": -20, "max": 60}
                },
                "constraints": {
                    "max_cost": 15.0,
                    "availability": "in_stock",
                    "lifecycle": "active"
                },
                "design_context": {
                    "application": "battery-powered",
                    "environment": "indoor/outdoor"
                }
            },
            "parts_needed": [
                {"role": "mcu", "query": "low-power MCU with WiFi, 3.3V, QFN package"},
                {"role": "power_regulator", "query": "3.3V LDO regulator, low quiescent current, <100uA"},
                {"role": "battery_charger", "query": "Li-ion battery charger IC, USB input"},
                {"role": "crystal", "query": "32.768kHz crystal for RTC"},
                {"role": "passives", "query": "decoupling capacitors, 10uF and 100nF"}
            ]
        },
        "industrial_controller": {
            "name": "Industrial Controller",
            "description": "Robust controller for industrial applications",
            "requirements": {
                "functional_requirements": [
                    "Industrial-grade MCU",
                    "Wide temperature range",
                    "Isolated interfaces",
                    "High reliability"
                ],
                "technical_specs": {
                    "voltage_range": {"min": 3.0, "max": 3.6},
                    "operating_temp": {"min": -40, "max": 85},
                    "interfaces": ["CAN", "RS485", "SPI"]
                },
                "constraints": {
                    "lifecycle": "active",
                    "reliability": "high"
                },
                "design_context": {
                    "application": "industrial",
                    "environment": "harsh",
                    "reliability_requirements": "high"
                }
            },
            "parts_needed": [
                {"role": "mcu", "query": "industrial MCU, -40 to 85°C, CAN interface"},
                {"role": "isolator", "query": "digital isolator, CAN/RS485"},
                {"role": "power", "query": "isolated power supply, 24V input"},
                {"role": "protection", "query": "TVS diodes, ESD protection"}
            ]
        },
        "usb_powered_device": {
            "name": "USB-Powered Device",
            "description": "Device powered from USB-C with data connectivity",
            "requirements": {
                "functional_requirements": [
                    "USB-C power and data",
                    "5V to 3.3V regulation",
                    "USB data interface"
                ],
                "technical_specs": {
                    "voltage_range": {"min": 4.5, "max": 5.5},  # USB voltage
                    "interfaces": ["USB-C", "I2C"]
                },
                "constraints": {
                    "max_cost": 10.0
                }
            },
            "parts_needed": [
                {"role": "connector", "query": "USB-C connector, through-hole or SMT"},
                {"role": "power_regulator", "query": "5V to 3.3V regulator, 500mA"},
                {"role": "usb_ic", "query": "USB interface IC or MCU with USB"}
            ]
        }
    }
    
    def __init__(self):
        self.db = get_part_database()
        self.matcher = IntelligentMatcherAgent()
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get design template"""
        return self.TEMPLATES.get(template_id)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates"""
        return [
            {
                "id": template_id,
                "name": template["name"],
                "description": template["description"]
            }
            for template_id, template in self.TEMPLATES.items()
        ]
    
    def generate_from_template(
        self,
        template_id: str,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete design from template.
        
        This is MAGICAL - takes a template and finds all parts automatically!
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        customizations = customizations or {}
        selected_parts = {}
        part_recommendations = {}
        
        # Merge customizations with template requirements
        requirements = template["requirements"].copy()
        if customizations:
            # Deep merge
            if "technical_specs" in customizations:
                requirements["technical_specs"].update(customizations["technical_specs"])
            if "constraints" in customizations:
                requirements["constraints"].update(customizations["constraints"])
        
        # Find parts for each role
        for part_spec in template["parts_needed"]:
            role = part_spec["role"]
            query = part_spec["query"]
            
            # Use intelligent matcher to find perfect parts
            results = self.matcher.find_perfect_parts(
                query=query,
                design_context=requirements.get("design_context"),
                existing_parts=selected_parts
            )
            
            if results["best_match"]:
                selected_parts[role] = results["best_match"]["part"]
                part_recommendations[role] = {
                    "selected": results["best_match"],
                    "alternatives": results["results"][:3]  # Top 3 alternatives
                }
            else:
                logger.warning(f"No match found for {role}: {query}")
        
        return {
            "template_id": template_id,
            "template_name": template["name"],
            "requirements": requirements,
            "selected_parts": selected_parts,
            "part_recommendations": part_recommendations,
            "design_complete": len(selected_parts) == len(template["parts_needed"])
        }

