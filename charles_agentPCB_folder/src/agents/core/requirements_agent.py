"""
Requirements Agent
Converts natural language query → structured requirements
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List
import logging
import requests

# Add development_demo/utils to path for config access
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from utils.config import load_config
except ImportError:
    # Fallback: try to load from environment directly
    load_config = None


logger = logging.getLogger(__name__)


class RequirementsAgent:
    """Agent that extracts structured requirements from natural language queries."""
    
    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager
        # Don't initialize API keys here - do it lazily in extract_requirements
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
        
        # Always use XAI - OpenAI support removed
        self.provider = "xai"
        if load_config:
            try:
                config = load_config()
                # Only use config if it's for xAI
                if config.get("provider", "xai").lower() == "xai":
                    self.api_key = config.get("api_key") or os.getenv("XAI_API_KEY")
                    self.endpoint = config.get("endpoint") or "https://api.x.ai/v1/chat/completions"
                    self.model = config.get("model") or os.getenv("XAI_MODEL", "grok-3")
                    self.temperature = config.get("temperature") or float(os.getenv("XAI_TEMPERATURE", "0.3"))
                else:
                    # Force xAI
                    self.api_key = os.getenv("XAI_API_KEY")
                    self.endpoint = "https://api.x.ai/v1/chat/completions"
                    self.model = os.getenv("XAI_MODEL", "grok-3")
                    self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.3"))
            except Exception as e:
                # Fallback to environment - always xAI
                self.api_key = os.getenv("XAI_API_KEY")
                self.endpoint = "https://api.x.ai/v1/chat/completions"
                self.model = os.getenv("XAI_MODEL", "grok-3")
                self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.3"))
        else:
            # Read from environment - always xAI
            self.api_key = os.getenv("XAI_API_KEY")
            self.endpoint = "https://api.x.ai/v1/chat/completions"
            self.model = os.getenv("XAI_MODEL", "grok-3")
            self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.3"))
        
        if not self.api_key:
            env_provider = os.getenv("LLM_PROVIDER", "not_set")
            raise ValueError(
                f"XAI_API_KEY not found. Set environment variable to enable reasoning. "
                f"(LLM_PROVIDER env: {env_provider})"
            )
        
        # Validate API key format (basic check)
        if len(self.api_key) < 20:
            raise ValueError("XAI_API_KEY appears to be invalid (too short). Please check your Railway environment variables.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        self._initialized = True
    
    def extract_requirements(self, query: str) -> Dict[str, Any]:
        """Extract requirements from query - ensures provider is set before LLM calls."""
        # CRITICAL: Ensure initialized before any LLM usage
        self._ensure_initialized()
        """
        Extract structured requirements from a natural language query.
        
        Args:
            query: Natural language description (e.g., "temperature sensor with wifi and 5V-USBC")
        
        Returns:
            Dictionary with structured requirements:
            {
                "functional_blocks": [...],
                "constraints": {...},
                "preferences": {...}
            }
        """
        # Ensure API is initialized (reads provider from environment at runtime)
        self._ensure_initialized()
        
        # Check cache first
        if self.cache_manager:
            import hashlib
            cache_key = f"requirements:{hashlib.sha256(query.encode()).hexdigest()[:16]}"
            cached = self.cache_manager.get(cache_key)
            if cached is not None:
                return cached
        
        prompt = f"""
You are a PCB design requirements extraction agent. Analyze the following user query and extract structured technical requirements.

User Query: "{query}"

Extract and return ONLY a JSON object with the following structure:
{{
  "functional_blocks": [
    {{
      "type": "mcu_wifi" | "sensor_temperature" | "power_input" | "connector" | etc.,
      "description": "brief description",
      "required": true/false
    }}
  ],
  "constraints": {{
    "voltage": {{
      "input": "5V" | "3.3V" | etc.,
      "outputs": ["3.3V", ...],
      "unit": "V"
    }},
    "current": {{
      "max": <number>,
      "unit": "A"
    }},
    "interfaces": ["I2C", "SPI", "WiFi", "USB-C", ...],
    "temperature_range": {{
      "min": <number>,
      "max": <number>,
      "unit": "C"
    }},
    "accuracy": {{
      "value": <number>,
      "unit": "C" | "%" | etc.
    }}
  }},
  "preferences": {{
    "package_type": "SMT" | "through_hole" | "any",
    "cost_range": "low" | "medium" | "high" | "any",
    "availability": "in_stock" | "any"
  }}
}}

Focus on identifying:
- Main functional blocks (MCU, sensors, power, connectors)
- Electrical constraints (voltages, currents)
- Interface requirements (I2C, SPI, WiFi, USB, etc.)
- Environmental constraints (temperature, accuracy)
- User preferences (package, cost, availability)

Return ONLY valid JSON, no additional text.
"""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert PCB design requirements extraction agent. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": 1500,
        }
        
        resp = None
        try:
            resp = requests.post(self.endpoint, headers=self.headers, json=payload, timeout=45)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            
            # Extract JSON from response
            json_str = self._extract_json(content)
            result = self._safe_load_requirements(json_str, query)
            
            # Cache result
            if self.cache_manager:
                import hashlib
                cache_key = f"requirements:{hashlib.sha256(query.encode()).hexdigest()[:16]}"
                self.cache_manager.set(cache_key, result, ttl=3600)  # Cache for 1 hour
            
            return result
        except requests.exceptions.HTTPError as e:
            error_detail = str(e)
            status_code = "Unknown"
            error_message = ""
            if resp is not None:
                status_code = resp.status_code
                try:
                    error_data = resp.json()
                    error_message = error_data.get("error", {})
                    if isinstance(error_message, dict):
                        error_detail = error_message.get("message", str(e))
                    else:
                        error_detail = str(error_message) if error_message else str(e)
                except:
                    error_detail = resp.text[:500] if hasattr(resp, 'text') else str(e)
            
            # Log the request for debugging
            debug_info = f"Endpoint: {self.endpoint}, Model: {self.model}, Provider: {getattr(self, 'provider', 'unknown')}"
            raise RuntimeError(f"Requirements extraction failed: HTTP {status_code} - {error_detail}\nDebug: {debug_info}")
        except Exception as e:
            logger.warning("Requirements extraction failed, using fallback structure: %s", e)
            return self._build_fallback_requirements(query)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from LLM response."""
        # Remove markdown code blocks if present
        if "```" in text:
            start = text.find("```")
            end = text.find("```", start + 3)
            if end > start:
                text = text[start + 3:end]
                # Remove language identifier
                if text.startswith("json"):
                    text = text[4:]
        
        # Find first { and last }
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx >= 0 and end_idx > start_idx:
            return text[start_idx:end_idx + 1]
        
        return text

    def _safe_load_requirements(self, json_str: str, query: str) -> Dict[str, Any]:
        """Safely load requirements JSON and apply fallback defaults."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.warning("Invalid JSON from requirements agent: %s\nPayload:%s", exc, json_str[:500])
            return self._build_fallback_requirements(query)
        
        # Ensure required keys exist
        if not isinstance(data.get("functional_blocks"), list) or not data["functional_blocks"]:
            data["functional_blocks"] = self._build_fallback_requirements(query)["functional_blocks"]
        if "constraints" not in data or not isinstance(data["constraints"], dict):
            data["constraints"] = {}
        if "preferences" not in data or not isinstance(data["preferences"], dict):
            data["preferences"] = {}
        return data

    def _build_fallback_requirements(self, query: str) -> Dict[str, Any]:
        """Build heuristic-based requirements when the agent output is unusable."""
        query_lower = query.lower()
        blocks = [
            {
                "type": "mcu",
                "description": "Primary controller / anchor component",
                "required": True
            }
        ]
        if "wifi" in query_lower or "esp" in query_lower:
            blocks.append({
                "type": "wifi_module",
                "description": "Wireless connectivity block",
                "required": True
            })
        if "sensor" in query_lower:
            blocks.append({
                "type": "sensor",
                "description": "Sensor interface block",
                "required": True
            })
        if "power" in query_lower or "battery" in query_lower:
            blocks.append({
                "type": "power",
                "description": "Power regulation block",
                "required": True
            })
        if "usb" in query_lower:
            blocks.append({
                "type": "connector",
                "description": "USB/IO connector block",
                "required": False
            })
        # Ensure at least MCU + Power
        if not any(b["type"] == "power" for b in blocks):
            blocks.append({
                "type": "power",
                "description": "Power regulation block",
                "required": True
            })
        
        voltage_matches = re.findall(r"(\d+(\.\d+)?)\s*v", query_lower)
        voltage_values = sorted({float(match[0]) for match in voltage_matches}, reverse=True)
        voltage_constraint = {}
        if voltage_values:
            voltage_constraint = {
                "input": f"{voltage_values[0]}V",
                "outputs": [f"{v}V" for v in voltage_values[1:]] or ["3.3V"],
                "unit": "V"
            }
        else:
            voltage_constraint = {"input": "5V", "outputs": ["3.3V"], "unit": "V"}
        
        constraints = {
            "voltage": voltage_constraint,
            "interfaces": []
        }
        if "i2c" in query_lower:
            constraints["interfaces"].append("I2C")
        if "spi" in query_lower:
            constraints["interfaces"].append("SPI")
        if "uart" in query_lower:
            constraints["interfaces"].append("UART")
        if "wifi" in query_lower:
            constraints["interfaces"].append("WiFi")
        if not constraints["interfaces"]:
            constraints["interfaces"] = ["GPIO"]
        
        preferences = {
            "package_type": "SMT" if "smt" in query_lower or "compact" in query_lower else "any",
            "cost_range": "low" if "low cost" in query_lower else "any",
            "availability": "in_stock"
        }
        
        return {
            "functional_blocks": blocks,
            "constraints": constraints,
            "preferences": preferences
        }

