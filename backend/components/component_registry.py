"""
Component Registry
Stores component states, inputs, outputs for agent context
"""

from typing import Dict, List, Any, Optional


class ComponentRegistry:
    """Registry for all components in the PCB design."""

    def __init__(self):
        self.components: Dict[str, Dict[str, Any]] = {}
        self.connections: List[Dict[str, Any]] = []
        self.state_history: List[Dict[str, Any]] = []

    def clear(self):
        """Reset registry to initial state."""
        self.components = {}
        self.connections = []
        self.state_history = []

    def add_component(self, comp_id: str, comp_data: Dict[str, Any]):
        """Add component to registry."""
        position = comp_data.get("position") or self._auto_position(len(self.components))
        self.components[comp_id] = {
            **comp_data,
            "current_inputs": {inp: None for inp in comp_data.get("inputs", [])},
            "current_outputs": {out: None for out in comp_data.get("outputs", [])},
            "position": position,
        }

    def remove_component(self, comp_id: str):
        if comp_id in self.components:
            del self.components[comp_id]
            self.connections = [
                conn for conn in self.connections if comp_id not in (conn["from"], conn["to"])
            ]

    def update_inputs(self, comp_id: str, inputs: Dict[str, Any]):
        if comp_id in self.components:
            self.components[comp_id]["current_inputs"].update(inputs)
            self._record_change("input", comp_id, inputs)

    def update_outputs(self, comp_id: str, outputs: Dict[str, Any]):
        if comp_id in self.components:
            self.components[comp_id]["current_outputs"].update(outputs)
            self._record_change("output", comp_id, outputs)

    def add_connection(self, from_comp: str, from_out: str, to_comp: str, to_in: str):
        self.connections.append(
            {
                "from": from_comp,
                "from_output": from_out,
                "to": to_comp,
                "to_input": to_in,
            }
        )

    def get_component_state(self, comp_id: str) -> Dict[str, Any]:
        comp = self.components.get(comp_id)
        if not comp:
            return {}
        return {
            "id": comp_id,
            "type": comp.get("type"),
            "inputs": comp.get("current_inputs"),
            "outputs": comp.get("current_outputs"),
            "description": comp.get("description"),
            "position": comp.get("position"),
        }

    def get_connections_for(self, comp_id: str) -> List[str]:
        connected = set()
        for conn in self.connections:
            if conn["from"] == comp_id:
                connected.add(conn["to"])
            if conn["to"] == comp_id:
                connected.add(conn["from"])
        return list(connected)

    def get_input_source(self, comp_id: str, input_name: str) -> Optional[str]:
        for conn in self.connections:
            if conn["to"] == comp_id and conn["to_input"] == input_name:
                return f"{conn['from']}.{conn['from_output']}"
        return None

    def get_output_destinations(self, comp_id: str, output_name: str) -> List[str]:
        dests = []
        for conn in self.connections:
            if conn["from"] == comp_id and conn["from_output"] == output_name:
                dests.append(f"{conn['to']}.{conn['to_input']}")
        return dests

    def get_connection_between(self, comp_a: str, comp_b: str):
        for conn in self.connections:
            if (conn['from'], conn['to']) == (comp_a, comp_b) or (conn['from'], conn['to']) == (comp_b, comp_a):
                return conn
        return None



    def get_all_components(self) -> Dict[str, Dict[str, Any]]:
        return self.components

    def count_connections(self) -> int:
        return len(self.connections)

    def get_recent_changes(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.state_history[-limit:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "components": self.components,
            "connections": self.connections,
            "state_history_count": len(self.state_history),
        }

    def _auto_position(self, index: int) -> Dict[str, float]:
        grid_cols = 3
        x = (index % grid_cols) * 40 + 20
        y = (index // grid_cols) * 30 + 20
        return {"x": x, "y": y}

    def _record_change(self, change_type: str, comp_id: str, data: Dict[str, Any]):
        self.state_history.append(
            {
                "type": change_type,
                "component": comp_id,
                "data": data,
                "timestamp": len(self.state_history),
            }
        )
