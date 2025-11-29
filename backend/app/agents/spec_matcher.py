"""
Specification matcher agent
Matches parts based on exact specifications - solves the "find parts that meet my requirements" pain point
"""
import logging
from typing import Dict, List, Any, Optional
from app.domain.part_database import get_part_database
from app.domain.models import ComponentCategory

logger = logging.getLogger(__name__)


class SpecMatcherAgent:
    """
    Matches parts based on exact specifications.
    Solves: "I need a part with X voltage, Y current, Z interface"
    """
    
    def __init__(self):
        self.db = get_part_database()
    
    def find_matching_parts(
        self,
        specifications: Dict[str, Any],
        category: Optional[ComponentCategory] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find parts matching exact specifications
        
        Args:
            specifications: Dict with:
                - voltage_min, voltage_max: Voltage range
                - current_min, current_max: Current range
                - power_min, power_max: Power range
                - interfaces: List of required interfaces (e.g., ["I2C", "SPI"])
                - package: Package type (e.g., "QFN", "SOIC")
                - footprint: IPC-7351 footprint
                - temp_min, temp_max: Operating temperature range
                - rohs_compliant: Boolean
            category: Component category filter
            max_results: Maximum number of results
        
        Returns:
            List of matching parts with match scores
        """
        candidates = self.db.search_parts(category=category) if category else self.db.get_all_parts()
        scored_parts = []
        
        for part in candidates:
            score = self._calculate_match_score(part, specifications)
            if score > 0:
                scored_parts.append({
                    "part": part,
                    "match_score": score,
                    "match_details": self._get_match_details(part, specifications)
                })
        
        # Sort by match score (highest first)
        scored_parts.sort(key=lambda x: x["match_score"], reverse=True)
        
        return scored_parts[:max_results]
    
    def _calculate_match_score(self, part: Dict[str, Any], specs: Dict[str, Any]) -> float:
        """Calculate how well a part matches specifications (0-100)"""
        score = 100.0
        penalties = []
        
        # Voltage matching
        if "voltage_min" in specs or "voltage_max" in specs:
            part_voltage = self._extract_voltage_range(part)
            if part_voltage:
                spec_min = specs.get("voltage_min", 0)
                spec_max = specs.get("voltage_max", float('inf'))
                
                if part_voltage[1] < spec_min or part_voltage[0] > spec_max:
                    return 0  # No overlap, reject
                
                # Penalize if not optimal range
                if part_voltage[0] < spec_min * 0.9 or part_voltage[1] > spec_max * 1.1:
                    score -= 10
                    penalties.append("Voltage range wider than required")
            else:
                score -= 20
                penalties.append("No voltage specification")
        
        # Current matching
        if "current_min" in specs or "current_max" in specs:
            part_current = self._extract_current_range(part)
            if part_current:
                spec_min = specs.get("current_min", 0)
                spec_max = specs.get("current_max", float('inf'))
                
                if part_current[1] < spec_min:
                    return 0  # Insufficient current capacity
                
                if part_current[1] > spec_max * 1.5:
                    score -= 5
                    penalties.append("Current capacity exceeds requirement significantly")
            else:
                score -= 15
                penalties.append("No current specification")
        
        # Interface matching
        if "interfaces" in specs:
            part_interfaces = part.get("interface_type", [])
            if isinstance(part_interfaces, str):
                part_interfaces = [part_interfaces]
            
            required_interfaces = specs["interfaces"]
            matched = sum(1 for req in required_interfaces 
                         if any(req.lower() in iface.lower() for iface in part_interfaces))
            
            if matched == 0:
                return 0  # No matching interfaces
            
            if matched < len(required_interfaces):
                score -= (len(required_interfaces) - matched) * 15
                penalties.append(f"Missing {len(required_interfaces) - matched} interface(s)")
        
        # Package matching
        if "package" in specs:
            part_package = part.get("package", "").upper()
            spec_package = specs["package"].upper()
            if spec_package not in part_package:
                score -= 10
                penalties.append("Package mismatch")
        
        # Footprint matching
        if "footprint" in specs:
            part_footprint = part.get("footprint", "")
            if part_footprint != specs["footprint"]:
                score -= 5
                penalties.append("Footprint mismatch")
        
        # Temperature range matching
        if "temp_min" in specs or "temp_max" in specs:
            part_temp = self._extract_temp_range(part)
            if part_temp:
                spec_min = specs.get("temp_min", -40)
                spec_max = specs.get("temp_max", 85)
                
                if part_temp[1] < spec_min or part_temp[0] > spec_max:
                    return 0  # Temperature range doesn't overlap
                
                if part_temp[0] > spec_min or part_temp[1] < spec_max:
                    score -= 5
                    penalties.append("Temperature range may be limiting")
        
        # RoHS compliance
        if specs.get("rohs_compliant") is True:
            if not part.get("rohs_compliant", True):
                return 0  # Must be RoHS compliant
        
        # Availability bonus
        if part.get("availability_status") == "in_stock":
            score += 5
        elif part.get("availability_status") == "obsolete":
            score -= 30
        
        # Lifecycle status bonus
        if part.get("lifecycle_status") == "active":
            score += 5
        elif part.get("lifecycle_status") == "obsolete":
            score -= 25
        
        return max(0, score)
    
    def _extract_voltage_range(self, part: Dict[str, Any]) -> Optional[tuple]:
        """Extract voltage range as (min, max)"""
        supply = part.get("supply_voltage_range", {})
        if isinstance(supply, dict):
            min_v = supply.get("min")
            max_v = supply.get("max")
            if min_v is not None and max_v is not None:
                return (min_v, max_v)
        return None
    
    def _extract_current_range(self, part: Dict[str, Any]) -> Optional[tuple]:
        """Extract current range as (min, max)"""
        current = part.get("current_max", {})
        if isinstance(current, dict):
            min_c = current.get("min", 0)
            max_c = current.get("max") or current.get("typical", 0)
            if max_c:
                return (min_c, max_c)
        elif isinstance(current, (int, float)):
            return (0, float(current))
        return None
    
    def _extract_temp_range(self, part: Dict[str, Any]) -> Optional[tuple]:
        """Extract temperature range as (min, max)"""
        temp = part.get("operating_temp_range", {})
        if isinstance(temp, dict):
            min_t = temp.get("min")
            max_t = temp.get("max")
            if min_t is not None and max_t is not None:
                return (min_t, max_t)
        return None
    
    def _get_match_details(self, part: Dict[str, Any], specs: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed match information"""
        details = {
            "matches": [],
            "warnings": [],
            "missing": []
        }
        
        # Check what matches
        if "interfaces" in specs:
            part_interfaces = part.get("interface_type", [])
            if isinstance(part_interfaces, str):
                part_interfaces = [part_interfaces]
            matched = [iface for iface in specs["interfaces"] 
                      if any(iface.lower() in pif.lower() for pif in part_interfaces)]
            details["matches"].extend([f"Interface: {iface}" for iface in matched])
        
        # Check voltage
        part_voltage = self._extract_voltage_range(part)
        if part_voltage and ("voltage_min" in specs or "voltage_max" in specs):
            details["matches"].append(f"Voltage: {part_voltage[0]}V - {part_voltage[1]}V")
        
        # Check availability warnings
        if part.get("availability_status") != "in_stock":
            details["warnings"].append(f"Availability: {part.get('availability_status')}")
        
        if part.get("lifecycle_status") != "active":
            details["warnings"].append(f"Lifecycle: {part.get('lifecycle_status')}")
        
        return details

