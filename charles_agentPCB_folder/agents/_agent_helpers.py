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
    Defaults to XAI - OpenAI support removed.
    
    Returns:
        Dictionary with api_key, endpoint, model, temperature, provider, headers
    """
    # Default to xAI - no OpenAI support
    provider = os.getenv("LLM_PROVIDER", "xai").lower()
    
    if load_config:
        try:
            config = load_config()
            # Only use config if provider is xai
            if config.get("provider", "xai").lower() == "xai":
                api_key = config.get("api_key") or os.getenv("XAI_API_KEY")
                endpoint = config.get("endpoint") or "https://api.x.ai/v1/chat/completions"
                model = config.get("model") or os.getenv("XAI_MODEL", "grok-3")
                temperature = config.get("temperature") or float(os.getenv("XAI_TEMPERATURE", "0.3"))
                provider = "xai"
            else:
                # Force xAI even if config says otherwise
                api_key = os.getenv("XAI_API_KEY")
                endpoint = "https://api.x.ai/v1/chat/completions"
                model = os.getenv("XAI_MODEL", "grok-3")
                temperature = float(os.getenv("XAI_TEMPERATURE", "0.3"))
                provider = "xai"
        except Exception:
            # Fallback to environment - always xAI
            provider = "xai"
            api_key = os.getenv("XAI_API_KEY")
            endpoint = "https://api.x.ai/v1/chat/completions"
            model = os.getenv("XAI_MODEL", "grok-3")
            temperature = float(os.getenv("XAI_TEMPERATURE", "0.3"))
    else:
        # Read from environment - always xAI
        provider = "xai"
        api_key = os.getenv("XAI_API_KEY")
        endpoint = "https://api.x.ai/v1/chat/completions"
        model = os.getenv("XAI_MODEL", "grok-3")
        temperature = float(os.getenv("XAI_TEMPERATURE", "0.3"))
    
    if not api_key:
        env_provider = os.getenv("LLM_PROVIDER", "not_set")
        error_msg = (
            f"XAI_API_KEY not found. "
            f"LLM_PROVIDER env: '{env_provider}'. "
            f"Please set XAI_API_KEY environment variable on Railway."
        )
        # Log for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[PROVIDER ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    # Validate API key format (basic check)
    if len(api_key) < 20:
        raise ValueError("XAI_API_KEY appears to be invalid (too short). Please check your Railway environment variables.")
    
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

