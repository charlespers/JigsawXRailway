"""
Compatibility checking agent
Checks electrical and mechanical compatibility between parts
"""
import logging
from typing import Dict, Any, List
from app.core.exceptions import CompatibilityError

logger = logging.getLogger(__name__)


class CompatibilityAgent:
    """Checks part compatibility"""
    
    def check_compatibility(
        self,
        part1: Dict[str, Any],
        part2: Dict[str, Any],
        connection_type: str = "power"
    ) -> Dict[str, Any]:
        """Check compatibility between two parts"""
        issues = []
        warnings = []
        
        if connection_type == "power":
            # Check voltage compatibility
            v1 = self._extract_voltage_range(part1)
            v2 = self._extract_voltage_range(part2)
            
            if v1 and v2:
                if not self._voltage_overlap(v1, v2):
                    issues.append(f"Voltage mismatch: {v1} vs {v2}")
                elif abs(v1[1] - v2[1]) > 0.5:  # More than 0.5V difference
                    warnings.append(f"Voltage difference: {v1[1]}V vs {v2[1]}V")
        
        elif connection_type == "signal":
            # Check IO voltage levels
            io1 = part1.get("io_voltage_levels", [])
            io2 = part2.get("io_voltage_levels", [])
            
            if io1 and io2:
                if not self._io_compatible(io1, io2):
                    issues.append("IO voltage levels incompatible")
        
        return {
            "compatible": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    def _extract_voltage_range(self, part: Dict[str, Any]) -> Optional[tuple]:
        """Extract voltage range as (min, max)"""
        supply = part.get("supply_voltage_range", {})
        if isinstance(supply, dict):
            min_v = supply.get("min")
            max_v = supply.get("max")
            if min_v is not None and max_v is not None:
                return (min_v, max_v)
        return None
    
    def _voltage_overlap(self, range1: tuple, range2: tuple) -> bool:
        """Check if voltage ranges overlap"""
        return range1[0] <= range2[1] and range2[0] <= range1[1]
    
    def _io_compatible(self, io1: List[float], io2: List[float]) -> bool:
        """Check if IO voltage levels are compatible"""
        # Simplified: check if there's overlap
        if not io1 or not io2:
            return True
        return any(abs(v1 - v2) < 0.3 for v1 in io1 for v2 in io2)

