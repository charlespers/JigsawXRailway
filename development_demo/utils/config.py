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
    Supports both OpenAI and XAI (Grok) APIs.
    
    Set LLM_PROVIDER to 'openai' or 'xai' to choose provider.
    """
    
    # Determine which provider to use
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider not in ["openai", "xai"]:
        raise ValueError(
            f"LLM_PROVIDER must be 'openai' or 'xai', got '{provider}'.\n"
            "Set it with: export LLM_PROVIDER='openai' or export LLM_PROVIDER='xai'"
        )
    
    config = {
        "provider": provider,
        "max_components": int(os.getenv("MAX_COMPONENTS", "10")),
        "simulation_timeout": int(os.getenv("SIMULATION_TIMEOUT", "30")),
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true"
    }
    
    if provider == "openai":
        # OpenAI configuration
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required when using OpenAI.\n"
                "Set it with: export OPENAI_API_KEY='your_key'"
            )
        
        config.update({
            "api_key": openai_api_key,
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
        })
    
    elif provider == "xai":
        # XAI (Grok) configuration
        xai_api_key = os.getenv("XAI_API_KEY")
        if not xai_api_key:
            raise ValueError(
                "XAI_API_KEY environment variable is required when using XAI.\n"
                "Set it with: export XAI_API_KEY='your_key'"
            )
        
        config.update({
            "api_key": xai_api_key,
            "endpoint": "https://api.x.ai/v1/chat/completions",
            "model": os.getenv("XAI_MODEL", "grok-3"),
            "temperature": float(os.getenv("XAI_TEMPERATURE", "0.3")),
        })
    
    return config

