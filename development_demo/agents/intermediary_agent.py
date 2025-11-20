"""
Intermediary Agent
Finds voltage conversion components to bridge voltage mismatches between parts
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.part_database import get_intermediary_candidates, search_voltage_converters


class IntermediaryAgent:
    """Agent that finds intermediary components to resolve voltage mismatches."""
    
    def __init__(self):
        pass
    
    def find_intermediary(
        self,
        source_part: Dict[str, Any],
        target_part: Dict[str, Any],
        connection_type: str,
        voltage_gap: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find intermediary components to bridge voltage gap between source and target.
        
        Args:
            source_part: Source component (provides voltage)
            target_part: Target component (requires voltage)
            connection_type: "power" or "signal"
            voltage_gap: Dictionary with source_voltage, target_min, target_max, target_nominal
        
        Returns:
            List of candidate intermediary parts, ranked by suitability
        """
        # Get candidates from database
        candidates = get_intermediary_candidates(voltage_gap, connection_type)
        
        # Estimate required current
        required_current = self._estimate_required_current(target_part)
        
        # Filter and rank candidates based on current requirements
        if required_current > 0:
            filtered_candidates = []
            for candidate in candidates:
                current_max = candidate.get("current_max", {})
                if isinstance(current_max, dict):
                    candidate_current = current_max.get("max") or current_max.get("typical", 0)
                else:
                    candidate_current = current_max or 0
                
                # Include if current capacity is sufficient (with 20% margin)
                if candidate_current >= required_current * 1.2 or candidate_current == 0:
                    filtered_candidates.append(candidate)
            
            candidates = filtered_candidates
        
        return candidates
    
    def _determine_intermediary_type(
        self,
        voltage_gap: Dict[str, Any],
        connection_type: str
    ) -> str:
        """
        Determine the type of intermediary component needed.
        
        Args:
            voltage_gap: Dictionary with source_voltage, target_min, target_max
            connection_type: "power" or "signal"
        
        Returns:
            Converter type string ("regulator_buck", "regulator_boost", "regulator_ldo", "level_shifter")
        """
        source_voltage = voltage_gap.get("source_voltage", 0)
        target_min = voltage_gap.get("target_min", 0)
        target_max = voltage_gap.get("target_max", 0)
        
        if not source_voltage or not target_min or not target_max:
            return "regulator_buck"  # Default
        
        target_voltage = (target_min + target_max) / 2
        voltage_diff = source_voltage - target_voltage
        
        if connection_type == "signal":
            return "level_shifter"
        elif abs(voltage_diff) < 1.0 and voltage_diff > 0:
            # Small drop, prefer LDO
            return "regulator_ldo"
        elif voltage_diff > 0:
            # Step down
            return "regulator_buck"
        else:
            # Step up
            return "regulator_boost"
    
    def _search_voltage_converters(
        self,
        input_voltage: float,
        output_voltage: float,
        min_current: float = 0.0,
        converter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search database for voltage converters matching criteria.
        
        Args:
            input_voltage: Input voltage in volts
            output_voltage: Output voltage in volts
            min_current: Minimum current capacity in amperes
            converter_type: Optional converter type filter
        
        Returns:
            List of matching converter parts
        """
        return search_voltage_converters(
            input_voltage, output_voltage, min_current, converter_type
        )
    
    def _estimate_required_current(self, target_part: Dict[str, Any]) -> float:
        """
        Estimate the current requirement of the target part.
        
        Args:
            target_part: Target component dictionary
        
        Returns:
            Estimated current requirement in amperes
        """
        current_max = target_part.get("current_max", {})
        if isinstance(current_max, dict):
            return current_max.get("max") or current_max.get("typical", 0.0)
        return float(current_max) if current_max else 0.0

