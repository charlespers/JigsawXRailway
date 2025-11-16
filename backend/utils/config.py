"""
Configuration for YC Demo
"""

import os
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """Load configuration from environment."""
    
    # Check for required env vars
    xai_api_key = os.getenv("XAI_API_KEY")
    if not xai_api_key:
        raise ValueError(
            "XAI_API_KEY environment variable is required.\n"
            "This simulator uses XAI for component reasoning.\n"
            "Set it with: export XAI_API_KEY='your_key'"
        )
    
    config = {
        "xai_api_key": xai_api_key,
        "xai_model": os.getenv("XAI_MODEL", "grok-beta"),
        "xai_temperature": float(os.getenv("XAI_TEMPERATURE", "0.3")),
        "max_components": int(os.getenv("MAX_COMPONENTS", "10")),
        "simulation_timeout": int(os.getenv("SIMULATION_TIMEOUT", "30")),
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true"
    }
    
    return config


def get_deployment_config() -> Dict[str, Any]:
    """Get deployment-specific configuration."""
    deployment_env = os.getenv("DEPLOYMENT_ENV", "local")
    
    configs = {
        "local": {
            "host": "localhost",
            "port": 8501,
            "workers": 1
        },
        "production": {
            "host": "0.0.0.0",
            "port": int(os.getenv("PORT", "8501")),
            "workers": int(os.getenv("WORKERS", "4"))
        },
        "staging": {
            "host": "0.0.0.0",
            "port": int(os.getenv("PORT", "8501")),
            "workers": 2
        }
    }
    
    return configs.get(deployment_env, configs["local"])

