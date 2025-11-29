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
    
    def _build_xai_url(self, path: str) -> str:
        base = settings.XAI_BASE_URL.rstrip("/")
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base}{path}"

    def _get_xai_endpoints(self) -> List[str]:
        """Return ordered list of xAI endpoints to try (chat first, then messages)."""
        endpoints = [self._build_xai_url(settings.XAI_CHAT_COMPLETIONS_PATH)]
        messages_url = self._build_xai_url(settings.XAI_MESSAGES_PATH)
        if messages_url not in endpoints:
            endpoints.append(messages_url)
        return endpoints

    def _get_endpoints(self) -> List[str]:
        if self.provider == "xai":
            return self._get_xai_endpoints()
        raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Call LLM API"""
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
        endpoints = self._get_endpoints()
        last_error: Optional[Exception] = None

        for idx, endpoint in enumerate(endpoints):
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                if response.status_code == 404 and idx + 1 < len(endpoints):
                    logger.warning(
                        "xAI endpoint %s returned 404. Attempting fallback endpoint.",
                        endpoint
                    )
                    continue

                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except requests.HTTPError as http_err:
                error_text = getattr(http_err.response, "text", "")
                logger.error(
                    "LLM HTTP error (status %s) from %s: %s",
                    getattr(http_err.response, "status_code", "unknown"),
                    endpoint,
                    error_text
                )
                last_error = http_err
            except Exception as exc:
                logger.error("LLM API error calling %s: %s", endpoint, exc)
                last_error = exc
                break

        if last_error:
            raise last_error
        raise RuntimeError("LLM call failed with no response")
    
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

