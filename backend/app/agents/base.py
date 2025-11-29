"""
Base agent class with LLM integration
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional
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
                "Content-Type": "application/json"
            }
        return {}
    
    def _get_endpoint(self) -> str:
        """Get API endpoint"""
        if self.provider == "xai":
            return f"https://api.x.ai/v1/chat/completions"
        raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Call LLM API"""
        try:
            response = requests.post(
                self._get_endpoint(),
                headers=self._get_headers(),
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM API error: {e}")
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

