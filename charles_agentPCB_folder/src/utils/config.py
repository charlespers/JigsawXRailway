"""
Configuration for Development Demo
Supports both OpenAI and XAI (Grok) APIs
"""

import os
from typing import Dict, Any, Literal

# Try to load from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment.
    Only supports XAI (Grok) API - OpenAI support removed.
    
    Set LLM_PROVIDER to 'xai' (default).
    """
    
    # Always use xai - OpenAI support removed
    provider = os.getenv("LLM_PROVIDER", "xai").lower()
    
    if provider != "xai":
        # Force xai if something else is set
        provider = "xai"
    
    config = {
        "provider": provider,
        "max_components": int(os.getenv("MAX_COMPONENTS", "10")),
        "simulation_timeout": int(os.getenv("SIMULATION_TIMEOUT", "30")),
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true"
    }
    
    # XAI (Grok) configuration - only provider supported
    xai_api_key = os.getenv("XAI_API_KEY")
    if not xai_api_key:
        raise ValueError(
            "XAI_API_KEY environment variable is required.\n"
            "Set it with: export XAI_API_KEY='your_key' or set it on Railway."
        )
    
    config.update({
        "api_key": xai_api_key,
        "endpoint": "https://api.x.ai/v1/chat/completions",
        "model": os.getenv("XAI_MODEL", "grok-3"),
        "temperature": float(os.getenv("XAI_TEMPERATURE", "0.3")),
    })
    
    return config

