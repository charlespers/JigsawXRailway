"""
Requirements Agent
Converts natural language query → structured requirements
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import requests

# Add development_demo/utils to path for config access
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from utils.config import load_config
except ImportError:
    # Fallback: try to load from environment directly
    load_config = None


class RequirementsAgent:
    """Agent that extracts structured requirements from natural language queries."""
    
    def __init__(self):
        if load_config:
            try:
                config = load_config()
                self.api_key = config.get("api_key")
                self.endpoint = config.get("endpoint")
                self.model = config.get("model")
                self.temperature = config.get("temperature")
                self.provider = config.get("provider", "openai")
            except Exception as e:
                # Fallback if config not available
                provider = os.getenv("LLM_PROVIDER", "openai").lower()
                if provider == "xai":
                    self.api_key = os.getenv("XAI_API_KEY")
                    self.endpoint = "https://api.x.ai/v1/chat/completions"
                    self.model = os.getenv("XAI_MODEL", "grok-3")
                    self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.3"))
                else:
                    self.api_key = os.getenv("OPENAI_API_KEY")
                    self.endpoint = "https://api.openai.com/v1/chat/completions"
                    self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                    self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
                self.provider = provider
        else:
            # Fallback if config not available
            provider = os.getenv("LLM_PROVIDER", "openai").lower()
            if provider == "xai":
                self.api_key = os.getenv("XAI_API_KEY")
                self.endpoint = "https://api.x.ai/v1/chat/completions"
                self.model = os.getenv("XAI_MODEL", "grok-3")
                self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.3"))
            else:
                self.api_key = os.getenv("OPENAI_API_KEY")
                self.endpoint = "https://api.openai.com/v1/chat/completions"
                self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
            self.provider = provider
        
        if not self.api_key:
            provider_name = "XAI" if self.provider == "xai" else "OpenAI"
            raise ValueError(f"{provider_name}_API_KEY not found. Set environment variable to enable reasoning.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def extract_requirements(self, query: str) -> Dict[str, Any]:
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
            return json.loads(json_str)
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
            raise RuntimeError(f"Requirements extraction failed: {e}")
    
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

