"""
Agent Helper Functions
Shared utilities for agent initialization
"""

import os
from typing import Dict, Any, Optional

try:
    from utils.config import load_config
except ImportError:
    load_config = None


def initialize_llm_config() -> Dict[str, Any]:
    """
    Initialize LLM configuration from config file or environment variables.
    This function reads the provider from the environment at runtime,
    allowing the provider to be set dynamically.
    
    Returns:
        Dictionary with api_key, endpoint, model, temperature, provider, headers
    """
    if load_config:
        try:
            config = load_config()
            api_key = config.get("api_key")
            endpoint = config.get("endpoint")
            model = config.get("model")
            temperature = config.get("temperature")
            provider = config.get("provider", "openai")
        except Exception:
            # Fallback to environment
            provider = os.getenv("LLM_PROVIDER", "openai").lower()
            if provider == "xai":
                api_key = os.getenv("XAI_API_KEY")
                endpoint = "https://api.x.ai/v1/chat/completions"
                model = os.getenv("XAI_MODEL", "grok-3")
                temperature = float(os.getenv("XAI_TEMPERATURE", "0.3"))
            else:
                api_key = os.getenv("OPENAI_API_KEY")
                endpoint = "https://api.openai.com/v1/chat/completions"
                model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    else:
        # Read from environment
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        if provider == "xai":
            api_key = os.getenv("XAI_API_KEY")
            endpoint = "https://api.x.ai/v1/chat/completions"
            model = os.getenv("XAI_MODEL", "grok-3")
            temperature = float(os.getenv("XAI_TEMPERATURE", "0.3"))
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            endpoint = "https://api.openai.com/v1/chat/completions"
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    
    if not api_key:
        provider_name = "XAI" if provider == "xai" else "OpenAI"
        env_provider = os.getenv("LLM_PROVIDER", "not_set")
        error_msg = (
            f"{provider_name}_API_KEY not found. "
            f"Provider requested: '{provider}', LLM_PROVIDER env: '{env_provider}'. "
            f"Please set {provider_name}_API_KEY environment variable on Railway."
        )
        # Log for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[PROVIDER ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    # Validate API key format (basic check)
    if provider == "xai" and len(api_key) < 20:
        raise ValueError("XAI_API_KEY appears to be invalid (too short). Please check your .env file.")
    if provider == "openai" and not api_key.startswith("sk-"):
        raise ValueError("OPENAI_API_KEY appears to be invalid (should start with 'sk-'). Please check your .env file.")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    return {
        "api_key": api_key,
        "endpoint": endpoint,
        "model": model,
        "temperature": temperature,
        "provider": provider,
        "headers": headers,
    }

