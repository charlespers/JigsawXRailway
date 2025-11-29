"""
Power analyzer agent
Analyzes power requirements and validates power budget - solves thermal and power management pain points
"""
import logging
from typing import Dict, List, Any, Optional
from app.core.exceptions import PCBDesignException

logger = logging.getLogger(__name__)


class PowerAnalyzerAgent:
    """
    Analyzes power requirements and validates power budgets.
    Solves: "Will my power supply handle all components? Are there thermal issues?"
    """
    
    def analyze_power_budget(
        self,
        selected_parts: Dict[str, Dict[str, Any]],
        power_supply: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze power budget for selected parts
        
        Args:
            selected_parts: Dictionary of selected parts
            power_supply: Optional power supply part specification
        
        Returns:
            Analysis with total power, current, warnings, and recommendations
        """
        total_power_watts = 0.0
        total_current_amps = 0.0
        power_by_rail = {}
        warnings = []
        recommendations = []
        
        # Analyze each part
        for part_name, part in selected_parts.items():
            part_power = self._calculate_part_power(part)
            part_current = self._extract_current(part)
            
            if part_power:
                total_power_watts += part_power
                warnings.append(f"{part_name}: {part_power:.2f}W")
            
            if part_current:
                total_current_amps += part_current
            
            # Track power by voltage rail
            voltage = self._extract_voltage(part)
            if voltage:
                rail_key = f"{voltage}V"
                if rail_key not in power_by_rail:
                    power_by_rail[rail_key] = {"power": 0, "current": 0, "parts": []}
                power_by_rail[rail_key]["power"] += part_power or 0
                power_by_rail[rail_key]["current"] += part_current or 0
                power_by_rail[rail_key]["parts"].append(part_name)
        
        # Validate against power supply if provided
        if power_supply:
            supply_power = self._extract_power_capacity(power_supply)
            supply_current = self._extract_current_capacity(power_supply)
            efficiency = power_supply.get("efficiency", 0.85)
            
            if supply_power:
                required_input_power = total_power_watts / efficiency
                if required_input_power > supply_power:
                    warnings.append(
                        f"CRITICAL: Required power ({required_input_power:.2f}W) exceeds "
                        f"supply capacity ({supply_power:.2f}W)"
                    )
                elif required_input_power > supply_power * 0.9:
                    warnings.append(
                        f"WARNING: Power usage ({required_input_power:.2f}W) is >90% of "
                        f"supply capacity ({supply_power:.2f}W)"
                    )
                    recommendations.append("Consider derating power supply to 70-80% capacity")
            
            if supply_current:
                if total_current_amps > supply_current:
                    warnings.append(
                        f"CRITICAL: Required current ({total_current_amps:.2f}A) exceeds "
                        f"supply capacity ({supply_current:.2f}A)"
                    )
        
        # Thermal analysis
        thermal_analysis = self._analyze_thermal(selected_parts, total_power_watts)
        
        return {
            "total_power_watts": round(total_power_watts, 2),
            "total_current_amps": round(total_current_amps, 2),
            "power_by_rail": {
                rail: {
                    "power_watts": round(data["power"], 2),
                    "current_amps": round(data["current"], 2),
                    "parts": data["parts"]
                }
                for rail, data in power_by_rail.items()
            },
            "warnings": warnings,
            "recommendations": recommendations,
            "thermal_analysis": thermal_analysis,
            "power_budget_status": "ok" if not any("CRITICAL" in w for w in warnings) else "critical"
        }
    
    def _calculate_part_power(self, part: Dict[str, Any]) -> Optional[float]:
        """Calculate power consumption for a part"""
        # Try direct power rating
        power_rating = part.get("power_rating")
        if power_rating:
            if isinstance(power_rating, dict):
                return power_rating.get("max") or power_rating.get("typical") or power_rating.get("value")
            return float(power_rating)
        
        # Calculate from voltage and current
        voltage = self._extract_voltage(part)
        current = self._extract_current(part)
        
        if voltage and current:
            return voltage * current
        
        return None
    
    def _extract_voltage(self, part: Dict[str, Any]) -> Optional[float]:
        """Extract nominal voltage"""
        supply = part.get("supply_voltage_range", {})
        if isinstance(supply, dict):
            return supply.get("nominal") or supply.get("max") or supply.get("min")
        return None
    
    def _extract_current(self, part: Dict[str, Any]) -> Optional[float]:
        """Extract maximum current"""
        current = part.get("current_max", {})
        if isinstance(current, dict):
            return current.get("max") or current.get("typical")
        elif isinstance(current, (int, float)):
            return float(current)
        return None
    
    def _extract_power_capacity(self, supply: Dict[str, Any]) -> Optional[float]:
        """Extract power supply capacity"""
        power = supply.get("power_rating", {})
        if isinstance(power, dict):
            return power.get("max") or power.get("value")
        elif isinstance(power, (int, float)):
            return float(power)
        return None
    
    def _extract_current_capacity(self, supply: Dict[str, Any]) -> Optional[float]:
        """Extract current supply capacity"""
        return self._extract_current(supply)
    
    def _analyze_thermal(
        self,
        parts: Dict[str, Dict[str, Any]],
        total_power: float
    ) -> Dict[str, Any]:
        """Analyze thermal characteristics"""
        thermal_warnings = []
        
        # Check for high-power components
        high_power_parts = []
        for name, part in parts.items():
            part_power = self._calculate_part_power(part)
            if part_power and part_power > 1.0:  # > 1W is significant
                high_power_parts.append({
                    "name": name,
                    "power_watts": part_power,
                    "thermal_resistance": part.get("thermal_resistance"),
                    "max_junction_temp": part.get("max_junction_temp")
                })
        
        if high_power_parts:
            thermal_warnings.append(
                f"Found {len(high_power_parts)} high-power component(s) requiring thermal consideration"
            )
        
        # Estimate junction temperature (simplified)
        # In production, use proper thermal modeling
        estimated_temp_rise = total_power * 50  # Rough estimate: 50°C/W for typical PCB
        
        return {
            "total_power_watts": round(total_power, 2),
            "high_power_components": high_power_parts,
            "estimated_temp_rise_c": round(estimated_temp_rise, 1),
            "warnings": thermal_warnings,
            "recommendations": [
                "Ensure adequate PCB copper pour for power distribution",
                "Consider thermal vias under high-power components",
                "Verify junction temperatures stay within limits"
            ] if high_power_parts else []
        }

