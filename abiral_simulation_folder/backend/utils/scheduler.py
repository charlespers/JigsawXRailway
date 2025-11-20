"""
Event-driven scheduler for hierarchical agent activation.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Set, Any


class AgentScheduler:
    """Track dirty components and propagate reasoning wavefront-style."""

    def __init__(self, registry):
        self.registry = registry
        self.dirty_components: Set[str] = set()

    def mark_dirty(self, component_id: str):
        self.dirty_components.add(component_id)

    def run(self, agents: Dict[str, any], note: str = "") -> List[Dict[str, Any]]:
        processed = []
        queue = deque(self.dirty_components)
        self.dirty_components.clear()
        visited = set()

        while queue:
            comp_id = queue.popleft()
            if comp_id in visited:
                continue
            visited.add(comp_id)

            agent = agents.get(comp_id)
            if not agent:
                continue
            component_state = self.registry.get_component_state(comp_id)
            if not component_state:
                continue

            result = agent.reason_about_state(component_state, self.registry)
            processed.append({
                "component": comp_id,
                "result": result,
                "state": component_state,
                "note": note,
            })
            if result.get("output_changes"):
                self.registry.update_outputs(comp_id, result["output_changes"])
                for downstream in result.get("downstream_components", []):
                    queue.append(downstream)

        return processed
