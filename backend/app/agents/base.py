"""
Base agent class with LLM integration
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
import requests
from requests import Response
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base agent with LLM integration"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = settings.XAI_API_KEY
        self.model = settings.XAI_MODEL
        self._initialized = False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        if self.provider == "xai":
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        return {}
    
    def _get_endpoint(self) -> str:
        """Get API endpoint"""
        if self.provider == "xai":
            base = settings.XAI_BASE_URL.rstrip("/")
            return f"{base}/chat/completions"
        raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Call LLM API"""
        endpoint = self._get_endpoint()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        headers = self._get_headers()
        
        try:
            logger.debug(f"Calling xAI endpoint: {endpoint}")
            logger.debug(f"Model: {self.model}, API key present: {bool(self.api_key)}")
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Log full response details for debugging
            logger.debug(f"xAI response status: {response.status_code}")
            logger.debug(f"xAI response headers: {dict(response.headers)}")
            
            if response.status_code == 404:
                error_text = response.text[:500] if response.text else "No response body"
                logger.error(
                    f"xAI 404 Not Found. Endpoint: {endpoint}\n"
                    f"Response: {error_text}\n"
                    f"Check: 1) API key is valid, 2) Model name '{self.model}' is correct, "
                    f"3) Base URL '{settings.XAI_BASE_URL}' is correct"
                )
            
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except requests.HTTPError as http_err:
            error_text = getattr(http_err.response, "text", "")[:500] if hasattr(http_err, 'response') else str(http_err)
            logger.error(
                f"LLM HTTP error (status {getattr(http_err.response, 'status_code', 'unknown')}) "
                f"from {endpoint}: {error_text}"
            )
            raise
        except Exception as e:
            logger.error(f"LLM API error calling {endpoint}: {e}", exc_info=True)
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            return json.loads(response.strip())
        except Exception as e:
            logger.error(f"JSON parsing error: {e}")
            raise

