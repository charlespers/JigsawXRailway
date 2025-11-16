"""
Component-Based AI Agent
Each component has an agent that reasons about its behavior using XAI.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)


class ComponentAgent:
    """AI agent representing a PCB component."""

    def __init__(
        self,
        component_id: str,
        component_type: str,
        inputs: List[str],
        outputs: List[str],
        description: str,
    ) -> None:
        self.component_id = component_id
        self.component_type = component_type
        self.inputs = inputs
        self.outputs = outputs
        self.description = description

        # Backend / XAI configuration (connects to Grok endpoint)
        self.api_key = os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "XAI_API_KEY not found. Set `export XAI_API_KEY='your_key'` to enable reasoning."
            )

        self.endpoint = "https://api.x.ai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Local state for UI + downstream reasoning
        self.current_inputs = {inp: None for inp in inputs}
        self.current_outputs = {out: None for out in outputs}
        self.reasoning_history: List[Dict[str, Any]] = []
        self.communication_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Core Reasoning
    # ------------------------------------------------------------------
    def reason_about_state(self, component_state: Dict[str, Any], registry: Any) -> Dict[str, Any]:
        """Call backend to reason about this component given current state."""
        context = self._build_component_context(component_state, registry)
        prompt = f"""
You are an AI agent for component {self.component_id} ({self.component_type}).
Inputs: {', '.join(self.inputs)}
Outputs: {', '.join(self.outputs)}
Description: {self.description}

Current State:
{json.dumps(component_state, indent=2)}

Circuit Context:
{context}

Analyze how this component should behave. Determine output changes, downstream impact, and whether other agents need to be notified. Return ONLY JSON with:
{{
  "reasoning": str,
  "input_status": {{"pin": "ok|invalid|missing"}},
  "output_changes": {{"pin": value}},
  "downstream_components": ["id"],
  "should_notify_agents": bool,
  "warnings": ["..."]
}}
"""
        response = self._call_xai(prompt)
        result = self._extract_json(response)
        self._log_reasoning(result, component_state)
        return result

    def evaluate_compatibility(self, other_state: Dict[str, Any], registry: Any) -> Dict[str, Any]:
        """Reason if this component can safely connect to another."""
        connection = registry.get_connection_between(self.component_id, other_state.get("id"))
        prompt = f"""
Component A (driver): {json.dumps(self.to_dict(), indent=2)}
Component B (receiver): {json.dumps(other_state, indent=2)}
Connection: {json.dumps(connection, indent=2)}

Determine if outputs from Component A can safely drive inputs of Component B. Consider voltage/current limits, interface type, required buffers, and if a resistor/level shifter is needed.
Return ONLY JSON:
{{
  "compatible": true/false,
  "reasoning": str,
  "risks": ["..."],
  "recommended_buffers": ["..."]
}}
"""
        response = self._call_xai(prompt)
        return self._extract_json(response)

    def communicate_with_agent(
        self,
        other_agent: "ComponentAgent",
        message: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = f"""
Agent {self.component_id} reports: "{message}"
Context: {json.dumps(context, indent=2)}
How should component {other_agent.component_id} respond? Return JSON with keys understood, reasoning, my_outputs_change, new_outputs.
"""
        response = self._call_xai(prompt)
        content = self._extract_json(response)
        self.communication_log.append({
            "to": other_agent.component_id,
            "message": message,
            "context": context,
            "response": content,
        })
        return content

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _call_xai(self, prompt: str) -> Dict[str, Any]:
        payload = {
            "model": "grok-beta",
            "messages": [
                {"role": "system", "content": "You are an expert PCB agent. Return only JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": float(os.getenv("XAI_TEMPERATURE", "0.3")),
            "max_tokens": 1500,
        }
        resp = requests.post(self.endpoint, headers=self.headers, json=payload, timeout=45)
        if resp.status_code != 200:
            raise RuntimeError(f"XAI error {resp.status_code}: {resp.text[:200]}")
        return resp.json()["choices"][0]["message"]["content"]

    def _extract_json(self, text: str) -> Dict[str, Any]:
        if "```" in text:
            start = text.find("```")
            end = text.find("```", start + 3)
            text = text[start + 3 : end]
        text = text[text.find("{") : text.rfind("}") + 1]
        return json.loads(text)

    def _build_component_context(self, component_state: Dict[str, Any], registry: Any) -> str:
        parts = [f"Total components: {len(registry.get_all_components())}"]
        neighbors = registry.get_connections_for(self.component_id)
        if neighbors:
            parts.append(f"Connected to: {', '.join(neighbors)}")
        for inp in self.inputs:
            src = registry.get_input_source(self.component_id, inp)
            if src:
                parts.append(f"Input {inp} driven by {src}")
        for out in self.outputs:
            dests = registry.get_output_destinations(self.component_id, out)
            if dests:
                parts.append(f"Output {out} drives {', '.join(dests)}")
        return "\n".join(parts)

    def _log_reasoning(self, result: Dict[str, Any], component_state: Dict[str, Any]) -> None:
        self.reasoning_history.append(
            {
                "reasoning": result.get("reasoning"),
                "state": component_state,
                "output_changes": result.get("output_changes"),
                "warnings": result.get("warnings", []),
            }
        )

    def get_current_reasoning(self) -> str:
        if not self.reasoning_history:
            return "No reasoning yet."
        return self.reasoning_history[-1].get("reasoning", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "current_inputs": self.current_inputs,
            "current_outputs": self.current_outputs,
        }
