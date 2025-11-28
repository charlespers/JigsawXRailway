"""
Query Router Agent
Classifies user queries and routes them to appropriate handlers
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from requests.exceptions import Timeout as RequestsTimeout

# Add development_demo/utils to path for config access
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from utils.config import load_config
except ImportError:
    load_config = None


class QueryRouterAgent:
    """Routes queries based on intent classification."""
    
    def __init__(self):
        """Initialize with LLM configuration."""
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
            self.temperature = config.get("temperature", 0.2)
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
                    self.temperature = config.get("temperature", 0.2)
                    self.provider = config.get("provider", "openai")
                except Exception:
                    provider = os.getenv("LLM_PROVIDER", "openai").lower()
                    if provider == "xai":
                        self.api_key = os.getenv("XAI_API_KEY")
                        self.endpoint = "https://api.x.ai/v1/chat/completions"
                        self.model = os.getenv("XAI_MODEL", "grok-3")
                        self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.2"))
                    else:
                        self.api_key = os.getenv("OPENAI_API_KEY")
                        self.endpoint = "https://api.openai.com/v1/chat/completions"
                        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
                    self.provider = provider
            else:
                provider = os.getenv("LLM_PROVIDER", "openai").lower()
                if provider == "xai":
                    self.api_key = os.getenv("XAI_API_KEY")
                    self.endpoint = "https://api.x.ai/v1/chat/completions"
                    self.model = os.getenv("XAI_MODEL", "grok-3")
                    self.temperature = float(os.getenv("XAI_TEMPERATURE", "0.2"))
                else:
                    self.api_key = os.getenv("OPENAI_API_KEY")
                    self.endpoint = "https://api.openai.com/v1/chat/completions"
                    self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                    self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
                self.provider = provider
            
            if not self.api_key:
                provider_name = "XAI" if self.provider == "xai" else "OpenAI"
                raise ValueError(f"{provider_name}_API_KEY not found.")
            
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self._initialized = True
    
    def classify_query(
        self,
        query: str,
        has_existing_design: bool = False,
        design_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify query intent and extract action details.
        
        Args:
            query: User query string
            has_existing_design: Whether there's an existing design
            design_context: Optional context about current design
        
        Returns:
            {
                "intent": "new_design" | "refinement" | "question" | "analysis_request" | "context_request",
                "confidence": float (0-1),
                "action_details": {
                    "parts_to_modify": List[str],
                    "parts_to_add": List[str],
                    "analysis_type": str,
                    "question_type": str,
                    "needed_info": List[str]
                },
                "reasoning": str
            }
        """
        # Rule-based quick classification first
        query_lower = query.lower().strip()
        
        # Check for question indicators
        question_indicators = ["what", "how", "why", "when", "where", "?", "explain", "tell me", "show me"]
        is_question = any(indicator in query_lower for indicator in question_indicators)
        
        # Check for refinement indicators
        refinement_indicators = ["change", "replace", "swap", "add", "remove", "update", "modify", "instead of"]
        is_refinement = any(indicator in query_lower for indicator in refinement_indicators)
        
        # Check for analysis request indicators
        analysis_indicators = ["analyze", "check", "validate", "review", "calculate", "estimate", "compare"]
        is_analysis = any(indicator in query_lower for indicator in analysis_indicators)
        
        # If no existing design and not a question, it's a new design
        if not has_existing_design and not is_question:
            return {
                "intent": "new_design",
                "confidence": 0.9,
                "action_details": {},
                "reasoning": "No existing design found, treating as new design request"
            }
        
        # If question and has design, route to question answering
        if is_question and has_existing_design:
            return {
                "intent": "question",
                "confidence": 0.85,
                "action_details": {
                    "question_type": self._extract_question_type(query_lower)
                },
                "reasoning": "Question detected about existing design"
            }
        
        # If refinement indicators and has design, route to refinement
        if is_refinement and has_existing_design:
            return {
                "intent": "refinement",
                "confidence": 0.8,
                "action_details": {
                    "parts_to_modify": self._extract_part_names(query),
                    "parts_to_add": self._extract_part_names(query, add_mode=True)
                },
                "reasoning": "Refinement request detected"
            }
        
        # If analysis indicators, route to analysis
        if is_analysis:
            return {
                "intent": "analysis_request",
                "confidence": 0.75,
                "action_details": {
                    "analysis_type": self._extract_analysis_type(query_lower)
                },
                "reasoning": "Analysis request detected"
            }
        
        # Default: use LLM for complex classification
        return self._llm_classify(query, has_existing_design, design_context)
    
    def _extract_question_type(self, query_lower: str) -> str:
        """Extract question type from query."""
        if any(word in query_lower for word in ["cost", "price", "expensive", "cheap"]):
            return "cost"
        elif any(word in query_lower for word in ["power", "current", "voltage", "watt"]):
            return "power"
        elif any(word in query_lower for word in ["compatible", "compatibility", "work with"]):
            return "compatibility"
        elif any(word in query_lower for word in ["thermal", "temperature", "heat"]):
            return "thermal"
        elif any(word in query_lower for word in ["available", "stock", "lead time"]):
            return "supply_chain"
        else:
            return "general"
    
    def _extract_analysis_type(self, query_lower: str) -> str:
        """Extract analysis type from query."""
        if "thermal" in query_lower or "temperature" in query_lower:
            return "thermal"
        elif "signal" in query_lower or "integrity" in query_lower:
            return "signal_integrity"
        elif "manufacturing" in query_lower or "dfm" in query_lower:
            return "manufacturing_readiness"
        elif "cost" in query_lower or "price" in query_lower:
            return "cost"
        elif "power" in query_lower:
            return "power"
        else:
            return "design_review"
    
    def _extract_part_names(self, query: str, add_mode: bool = False) -> list:
        """Extract part names/MPNs from query."""
        # Simple extraction - look for quoted strings or common part patterns
        import re
        # Look for quoted strings
        quoted = re.findall(r'"([^"]+)"', query)
        # Look for part numbers (alphanumeric with dashes, typically uppercase)
        part_numbers = re.findall(r'\b[A-Z0-9]+[-][A-Z0-9]+(?:\s|$)', query)
        return quoted + part_numbers
    
    def _llm_classify(
        self,
        query: str,
        has_existing_design: bool,
        design_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use LLM for complex query classification."""
        # Ensure agent is initialized before using LLM
        self._ensure_initialized()
        
        context_info = ""
        if design_context:
            part_count = len(design_context.get("selected_parts", {}))
            context_info = f"Current design has {part_count} parts selected."
        
        prompt = f"""
You are a query routing agent for a PCB design system. Classify the user's query and extract action details.

User Query: "{query}"
Has Existing Design: {has_existing_design}
{context_info}

Classify the query intent and return ONLY valid JSON:
{{
  "intent": "new_design" | "refinement" | "question" | "analysis_request" | "context_request",
  "confidence": 0.0-1.0,
  "action_details": {{
    "parts_to_modify": ["part_name_or_id"],
    "parts_to_add": ["part_name_or_id"],
    "analysis_type": "thermal" | "signal_integrity" | "manufacturing_readiness" | "cost" | "power" | "design_review",
    "question_type": "cost" | "power" | "compatibility" | "thermal" | "supply_chain" | "general",
    "needed_info": ["info_type"]
  }},
  "reasoning": "brief explanation"
}}

Intent meanings:
- "new_design": User wants to create a completely new design
- "refinement": User wants to modify existing design (change/add/remove parts)
- "question": User is asking about the current design
- "analysis_request": User wants to run a specific analysis
- "context_request": System needs more information from user

Return ONLY valid JSON, no additional text.
"""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert query routing agent. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": 500,
        }
        
        try:
            resp = requests.post(self.endpoint, headers=self.headers, json=payload, timeout=10)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            json_str = self._extract_json(content)
            return json.loads(json_str)
        except RequestsTimeout:
            # Fallback to rule-based classification
            return {
                "intent": "new_design" if not has_existing_design else "question",
                "confidence": 0.5,
                "action_details": {},
                "reasoning": "LLM timeout, using fallback classification"
            }
        except Exception as e:
            # Fallback to rule-based classification
            return {
                "intent": "new_design" if not has_existing_design else "question",
                "confidence": 0.5,
                "action_details": {},
                "reasoning": f"LLM error, using fallback: {str(e)}"
            }
    
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

