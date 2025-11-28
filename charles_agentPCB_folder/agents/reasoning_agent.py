"""
Reasoning Agent
Evaluates feasibility of using an intermediary component to bridge two parts
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import requests

# Add development_demo/utils to path for config access
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from utils.config import load_config
except ImportError:
    load_config = None


class ReasoningAgent:
    """Agent that evaluates intermediary feasibility using rule-based and LLM reasoning."""
    
    def __init__(self):
        # Don't initialize API keys here - do it lazily
        # This allows the provider to be set in the environment before use
        self._initialized = False
        self.api_key = None
        self.endpoint = None
        self.model = None
        self.temperature = None
        self.provider = None
        self.headers = None
    
    def _ensure_initialized(self):
        """Lazily initialize API configuration based on current environment."""
        if self._initialized:
            return
        
        try:
            from agents._agent_helpers import initialize_llm_config
            config = initialize_llm_config()
            self.api_key = config["api_key"]
            self.endpoint = config["endpoint"]
            self.model = config["model"]
            self.temperature = config["temperature"]
            self.provider = config["provider"]
            self.headers = config["headers"]
            self._initialized = True
        except ImportError:
            # Fallback to inline initialization - always xAI
            self.provider = "xai"
            if load_config:
                try:
                    config = load_config()
                    # Only use config if it's for xAI
                    if config.get("provider", "xai").lower() == "xai":
                        self.api_key = config.get("api_key") or os.getenv("XAI_API_KEY")
                        self.endpoint = config.get("endpoint") or "https://api.x.ai/v1/chat/completions"
                        self.model = config.get("model") or os.getenv("XAI_MODEL", "grok-3")
                        self.temperature = config.get("temperature") or float(os.getenv("XAI_TEMPERATURE", "0.2"))
                    else:
                        # Force xAI
                        self.api_key = os.getenv("XAI_API_KEY")
                        self.endpoint = "https://api.x.ai/v1/chat/completions"
                        self.model = os.getenv("XAI_MODEL", "grok-3")
                        self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.2"))
                except Exception:
                    # Fallback to environment - always xAI
                    self.api_key = os.getenv("XAI_API_KEY")
                    self.endpoint = "https://api.x.ai/v1/chat/completions"
                    self.model = os.getenv("XAI_MODEL", "grok-3")
                    self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.2"))
            else:
                # Read from environment - always xAI
                self.api_key = os.getenv("XAI_API_KEY")
                self.endpoint = "https://api.x.ai/v1/chat/completions"
                self.model = os.getenv("XAI_MODEL", "grok-3")
                self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.2"))
            
            if not self.api_key:
                env_provider = os.getenv("LLM_PROVIDER", "not_set")
                raise ValueError(
                    f"XAI_API_KEY not found. Set environment variable to enable reasoning. "
                    f"(LLM_PROVIDER env: {env_provider})"
                )
            
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self._initialized = True
    
    def evaluate_intermediary_feasibility(
        self,
        source_part: Dict[str, Any],
        intermediary_part: Dict[str, Any],
        target_part: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate if an intermediary can successfully bridge source and target.
        
        Args:
            source_part: Source component
            intermediary_part: Proposed intermediary component
            target_part: Target component
        
        Returns:
            {
                "feasible": bool,
                "feasibility_score": float (0-1),
                "reasoning": str,
                "risks": List[str],
                "warnings": List[str],
                "power_dissipation": float (watts),
                "thermal_ok": bool
            }
        """
        # Rule-based checks first
        rule_result = self._rule_based_evaluation(
            source_part, intermediary_part, target_part
        )
        
        # If rule-based check is conclusive, return it
        if rule_result["feasible"] is not None:
            return rule_result
        
        # Ensure API is initialized (reads provider from environment at runtime)
        self._ensure_initialized()
        
        # Otherwise use LLM for complex reasoning
        return self._llm_based_evaluation(
            source_part, intermediary_part, target_part
        )
    
    def _rule_based_evaluation(
        self,
        source_part: Dict[str, Any],
        intermediary_part: Dict[str, Any],
        target_part: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rule-based feasibility evaluation."""
        risks = []
        warnings = []
        feasibility_score = 1.0
        
        # Check voltage compatibility: Source → Intermediary
        source_voltage = self._get_output_voltage(source_part)
        intermediary_input_range = intermediary_part.get("input_voltage_range") or intermediary_part.get("supply_voltage_range")
        
        if source_voltage and intermediary_input_range:
            input_min = intermediary_input_range.get("min")
            input_max = intermediary_input_range.get("max")
            if input_min and input_max:
                if not (input_min <= source_voltage <= input_max):
                    return {
                        "feasible": False,
                        "feasibility_score": 0.0,
                        "reasoning": f"Source voltage {source_voltage}V not in intermediary input range {input_min}-{input_max}V",
                        "risks": ["Voltage incompatibility"],
                        "warnings": [],
                        "power_dissipation": 0.0,
                        "thermal_ok": False
                    }
        
        # Check voltage compatibility: Intermediary → Target
        intermediary_output = intermediary_part.get("output_voltage")
        if intermediary_output:
            if isinstance(intermediary_output, dict):
                intermediary_output_voltage = intermediary_output.get("nominal") or intermediary_output.get("value")
            else:
                intermediary_output_voltage = intermediary_output
        else:
            intermediary_output_voltage = None
        
        target_input_range = target_part.get("supply_voltage_range")
        if intermediary_output_voltage and target_input_range:
            target_min = target_input_range.get("min")
            target_max = target_input_range.get("max")
            if target_min and target_max:
                if not (target_min <= intermediary_output_voltage <= target_max):
                    return {
                        "feasible": False,
                        "feasibility_score": 0.0,
                        "reasoning": f"Intermediary output {intermediary_output_voltage}V not in target range {target_min}-{target_max}V",
                        "risks": ["Voltage incompatibility"],
                        "warnings": [],
                        "power_dissipation": 0.0,
                        "thermal_ok": False
                    }
        
        # Check current capacity
        target_current = self._get_current_requirement(target_part)
        intermediary_current = self._get_current_capacity(intermediary_part)
        
        if target_current > 0 and intermediary_current > 0:
            if intermediary_current < target_current:
                return {
                    "feasible": False,
                    "feasibility_score": 0.0,
                    "reasoning": f"Intermediary current capacity ({intermediary_current}A) insufficient for target ({target_current}A)",
                    "risks": ["Current capacity insufficient"],
                    "warnings": [],
                    "power_dissipation": 0.0,
                    "thermal_ok": False
                }
            elif intermediary_current < target_current * 1.2:
                warnings.append(f"Intermediary current capacity ({intermediary_current}A) has limited margin for target ({target_current}A)")
                feasibility_score *= 0.8
        
        # Calculate power dissipation (especially important for LDOs)
        power_dissipation = self._calculate_power_dissipation(
            source_voltage, intermediary_output_voltage, target_current
        )
        
        # Check thermal limits
        thermal_ok = self._check_thermal_limits(intermediary_part, power_dissipation)
        if not thermal_ok:
            risks.append(f"Power dissipation ({power_dissipation:.2f}W) may exceed thermal limits")
            feasibility_score *= 0.5
        
        # Adjust score based on efficiency (for switching regulators)
        efficiency = intermediary_part.get("efficiency", 0)
        if efficiency > 0:
            if efficiency < 0.7:
                warnings.append(f"Low efficiency ({efficiency*100:.1f}%)")
                feasibility_score *= 0.9
        
        return {
            "feasible": True,
            "feasibility_score": feasibility_score,
            "reasoning": "Rule-based checks passed",
            "risks": risks,
            "warnings": warnings,
            "power_dissipation": power_dissipation,
            "thermal_ok": thermal_ok
        }
    
    def _llm_based_evaluation(
        self,
        source_part: Dict[str, Any],
        intermediary_part: Dict[str, Any],
        target_part: Dict[str, Any]
    ) -> Dict[str, Any]:
        """LLM-based feasibility evaluation for complex cases."""
        # Ensure API is initialized (reads provider from environment at runtime)
        self._ensure_initialized()
        
        prompt = f"""
You are a PCB design reasoning agent. Evaluate if an intermediary component can successfully bridge two parts.

Source Part:
{json.dumps(source_part, indent=2)}

Intermediary Part:
{json.dumps(intermediary_part, indent=2)}

Target Part:
{json.dumps(target_part, indent=2)}

Analyze:
1. Voltage compatibility (source → intermediary → target)
2. Current capacity (can intermediary supply target's needs)
3. Power dissipation and thermal considerations
4. Efficiency and design complexity trade-offs
5. Overall feasibility

Return ONLY JSON:
{{
  "feasible": true/false,
  "feasibility_score": 0.0-1.0,
  "reasoning": "detailed explanation",
  "risks": ["risk1", "risk2"],
  "warnings": ["warning1", "warning2"],
  "power_dissipation": <watts>,
  "thermal_ok": true/false
}}

Return ONLY valid JSON, no additional text.
"""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert PCB design reasoning agent. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": 1500,
        }
        
        try:
            # Reduced timeout to prevent blocking (15 seconds instead of 45)
            resp = requests.post(self.endpoint, headers=self.headers, json=payload, timeout=15)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            json_str = self._extract_json(content)
            result = json.loads(json_str)
            
            # Ensure required fields
            if "power_dissipation" not in result:
                result["power_dissipation"] = self._calculate_power_dissipation(
                    self._get_output_voltage(source_part),
                    self._get_output_voltage(intermediary_part),
                    self._get_current_requirement(target_part)
                )
            if "thermal_ok" not in result:
                result["thermal_ok"] = self._check_thermal_limits(
                    intermediary_part, result.get("power_dissipation", 0)
                )
            
            return result
        except RequestsTimeout:
            # Timeout - fallback to rule-based result
            return self._rule_based_evaluation(source_part, intermediary_part, target_part)
        except Exception as e:
            # Fallback to rule-based result
            return self._rule_based_evaluation(source_part, intermediary_part, target_part)
    
    def _calculate_power_dissipation(
        self,
        input_voltage: Optional[float],
        output_voltage: Optional[float],
        current: float
    ) -> float:
        """
        Calculate power dissipation in intermediary (especially for LDOs).
        
        Args:
            input_voltage: Input voltage in volts
            output_voltage: Output voltage in volts
            current: Load current in amperes
        
        Returns:
            Power dissipation in watts
        """
        if not input_voltage or not output_voltage or current <= 0:
            return 0.0
        
        # Power dissipation = (Vin - Vout) * Iout
        return (input_voltage - output_voltage) * current
    
    def _check_thermal_limits(
        self,
        intermediary_part: Dict[str, Any],
        power_dissipation: float
    ) -> bool:
        """
        Check if power dissipation is within thermal limits.
        
        Args:
            intermediary_part: Intermediary component dictionary
            power_dissipation: Calculated power dissipation in watts
        
        Returns:
            True if thermal limits are OK
        """
        if power_dissipation <= 0:
            return True
        
        # Get thermal resistance (if available)
        thermal_resistance = intermediary_part.get("thermal_resistance", {})
        if isinstance(thermal_resistance, dict):
            theta_ja = thermal_resistance.get("theta_ja") or thermal_resistance.get("junction_to_ambient")
        else:
            theta_ja = thermal_resistance
        
        # Get max junction temperature
        max_temp = intermediary_part.get("max_junction_temp") or intermediary_part.get("max_operating_temp")
        if isinstance(max_temp, dict):
            max_temp_value = max_temp.get("max") or max_temp.get("value")
        else:
            max_temp_value = max_temp
        
        # If we have thermal data, check
        if theta_ja and max_temp_value:
            # Assume ambient temp of 25°C
            ambient_temp = 25.0
            junction_temp = ambient_temp + (power_dissipation * theta_ja)
            return junction_temp < max_temp_value
        
        # Heuristic: For LDOs, warn if dissipation > 1W
        category = intermediary_part.get("category", "")
        if "ldo" in category.lower():
            return power_dissipation <= 1.0
        
        # For switching regulators, typically OK up to 2-3W
        if "buck" in category.lower() or "boost" in category.lower():
            return power_dissipation <= 3.0
        
        # Default: assume OK if no data
        return True
    
    def _get_output_voltage(self, part: Dict[str, Any]) -> Optional[float]:
        """Extract output voltage from part."""
        output_voltage = part.get("output_voltage")
        if output_voltage:
            if isinstance(output_voltage, dict):
                return output_voltage.get("nominal") or output_voltage.get("value")
            return float(output_voltage)
        
        # Try supply voltage range
        supply_range = part.get("supply_voltage_range")
        if supply_range:
            return supply_range.get("nominal") or supply_range.get("value")
        
        return None
    
    def _get_current_requirement(self, part: Dict[str, Any]) -> float:
        """Extract current requirement from part."""
        current_max = part.get("current_max", {})
        if isinstance(current_max, dict):
            return current_max.get("max") or current_max.get("typical", 0.0)
        return float(current_max) if current_max else 0.0
    
    def _get_current_capacity(self, part: Dict[str, Any]) -> float:
        """Extract current capacity from part."""
        return self._get_current_requirement(part)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from LLM response."""
        if "```" in text:
            start = text.find("```")
            end = text.find("```", start + 3)
            if end > start:
                text = text[start + 3:end]
                if text.startswith("json"):
                    text = text[4:]
        
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx >= 0 and end_idx > start_idx:
            return text[start_idx:end_idx + 1]
        return text

