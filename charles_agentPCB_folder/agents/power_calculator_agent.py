"""
Power Calculator Agent
Calculates power consumption and estimates battery life
"""

from typing import List, Dict, Any, Optional


class PowerCalculatorAgent:
    """Calculates power consumption for BOM items."""
    
    def calculate_power_consumption(
        self,
        bom_items: List[Dict[str, Any]],
        operating_modes: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate power consumption for BOM items.
        
        Args:
            bom_items: List of BOM items with part data
            operating_modes: Optional dict mapping component IDs to duty cycles (0-1)
        
        Returns:
            Dictionary with power analysis:
            {
                "total_power": float,
                "power_by_rail": Dict,
                "power_by_component": List,
                "battery_life": Optional[float]
            }
        """
        power_by_rail = {}
        power_by_component = []
        total_power = 0.0
        
        operating_modes = operating_modes or {}
        
        for item in bom_items:
            part = item.get("part_data", {})
            part_id = part.get("id")
            quantity = item.get("quantity", 1)
            
            # Import safe_float_extract from design_analyzer
            from agents.design_analyzer import safe_float_extract
            
            # Get voltage rail - use safe extraction
            voltage_range = part.get("supply_voltage_range", {})
            voltage = safe_float_extract(
                voltage_range.get("nominal") or voltage_range.get("max") or voltage_range,
                context=f"voltage for {part_id}"
            )
            
            # Get current consumption - use safe extraction
            current_max = part.get("current_max", {})
            current = safe_float_extract(
                current_max.get("typical") or current_max.get("max") or current_max,
                context=f"current for {part_id}"
            )
            
            # Apply duty cycle if specified
            duty_cycle = operating_modes.get(part_id, 1.0)
            effective_current = current * duty_cycle
            
            if voltage > 0 and effective_current > 0:
                power = voltage * effective_current * quantity
                total_power += power
                
                rail_key = f"{voltage}V"
                if rail_key not in power_by_rail:
                    power_by_rail[rail_key] = 0.0
                power_by_rail[rail_key] += power
                
                power_by_component.append({
                    "part_id": part_id,
                    "name": part.get("name"),
                    "voltage": voltage,
                    "current": effective_current,
                    "power": power,
                    "quantity": quantity,
                    "duty_cycle": duty_cycle
                })
        
        # Estimate battery life (if battery capacity provided)
        battery_life = None
        
        return {
            "total_power": total_power,
            "power_by_rail": power_by_rail,
            "power_by_component": power_by_component,
            "battery_life": battery_life
        }
    
    def estimate_battery_life(
        self,
        total_power: float,
        battery_capacity_mah: float,
        battery_voltage: float = 3.7
    ) -> Dict[str, Any]:
        """
        Estimate battery life based on power consumption.
        
        Args:
            total_power: Total power consumption in watts
            battery_capacity_mah: Battery capacity in mAh
            battery_voltage: Battery voltage (default 3.7V for Li-ion)
        
        Returns:
            Dictionary with battery life estimates
        """
        battery_energy_wh = (battery_capacity_mah / 1000.0) * battery_voltage
        hours = battery_energy_wh / total_power if total_power > 0 else 0
        days = hours / 24.0
        
        return {
            "battery_capacity_mah": battery_capacity_mah,
            "battery_voltage": battery_voltage,
            "battery_energy_wh": battery_energy_wh,
            "total_power_w": total_power,
            "estimated_hours": hours,
            "estimated_days": days
        }

