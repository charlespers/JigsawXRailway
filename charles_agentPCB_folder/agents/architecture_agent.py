"""
Architecture Agent
Builds functional hierarchy and selects anchor part
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

# Add development_demo/utils to path for config access
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from utils.config import load_config
except ImportError:
    # Fallback: try to load from environment directly
    load_config = None


class ArchitectureAgent:
    """Agent that builds block-level hierarchy and selects anchor part."""
    
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
            # Fallback to inline initialization
            if load_config:
                try:
                    config = load_config()
                    self.api_key = config.get("api_key")
                    self.endpoint = config.get("endpoint")
                    self.model = config.get("model")
                    self.temperature = config.get("temperature")
                    self.provider = config.get("provider", "openai")
                except Exception:
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
                raise ValueError(f"{provider_name}_API_KEY not found.")
            
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self._initialized = True
    
    def build_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build functional hierarchy from requirements.
        
        Returns:
            {
                "anchor_block": {...},
                "child_blocks": [...],
                "dependency_graph": {...},
                "constraints_per_block": {...}
            }
        """
        # Ensure API is initialized (reads provider from environment at runtime)
        self._ensure_initialized()
        
        prompt = f"""
You are a PCB architecture design agent. Given the following requirements, build a functional block hierarchy.

Requirements:
{json.dumps(requirements, indent=2)}

Identify:
1. The anchor part (most connected component, typically the main MCU or WiFi module)
2. Child blocks (power, sensors, connectors, etc.)
3. Dependency relationships (which blocks depend on which)
4. Constraints for each block (voltage rails, interfaces, etc.)

Return ONLY a JSON object:
{{
  "anchor_block": {{
    "type": "mcu_wifi" | "wifi_module" | etc.,
    "description": "description",
    "required_interfaces": ["I2C", "SPI", "WiFi", ...],
    "required_power_rails": ["3.3V", ...],
    "required_gpios": <number>
  }},
  "child_blocks": [
    {{
      "type": "power" | "sensor" | "connector" | "debug",
      "description": "description",
      "depends_on": ["anchor"] | [],
      "required_interfaces": [...],
      "required_power_rails": [...]
    }}
  ],
  "dependency_graph": {{
    "anchor": [],
    "power": ["anchor"],
    "sensor": ["anchor", "power"],
    ...
  }},
  "constraints_per_block": {{
    "anchor": {{
      "supply_voltage": "3.3V",
      "io_voltage": "3.3V",
      "interfaces": ["I2C", "WiFi"]
    }},
    "power": {{
      "input_voltage": "5V",
      "output_voltage": "3.3V",
      "output_current_min": <number>
    }},
    ...
  }}
}}

Return ONLY valid JSON, no additional text.
"""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert PCB architecture designer. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": 2000,
        }
        
        try:
            resp = requests.post(self.endpoint, headers=self.headers, json=payload, timeout=45)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            json_str = self._extract_json(content)
            return json.loads(json_str)
        except Exception as e:
            raise RuntimeError(f"Architecture building failed: {e}")
    
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

