"""
Demo 3 - Hardware Description Language → Agents
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="Hardware DSL | YC Demo",
    page_icon="DSL",
    layout="wide",
)

st.title("Demo 3 · Software-Friendly Hardware Language")
st.caption("Describe a circuit in a tiny DSL and push it into the simulator.")

EXAMPLE = """component MCU as esp32
  power 3.3V
  connect gpio1 -> LED.ANODE
component LED as led_red
  resistor 330 between MCU.GPIO1 and LED.ANODE
"""

st.markdown("#### Example Syntax")
st.code(EXAMPLE, language="text")

user_dsl = st.text_area("Describe a small hardware idea", height=260)
parsed_design = None

if user_dsl.strip():
    try:
        parsed_design = None
        parsed_design = _parse_dsl(user_dsl)
        st.success(f"Parsed {len(parsed_design['components'])} components and {len(parsed_design['connections'])} connections")
        st.json(parsed_design)
    except ValueError as exc:
        st.error(str(exc))
else:
    st.warning("Enter a description to preview the DSL workflow.")

if parsed_design:
    if st.button("Send to Simulator", use_container_width=True):
        design_payload = _convert_to_design_payload(parsed_design)
        st.session_state.kicad_design = design_payload
        st.session_state.design_summary = {
            "filename": "DSL_MODEL",
            "components": len(parsed_design["components"]),
            "nets": len(design_payload.get("nets", [])),
            "types": _summarize_types(parsed_design["components"]),
        }
        st.session_state.loaded_design_id = None
        st.success("DSL design sent to simulator – open Demo 1 to run agents.")


def _parse_dsl(text: str) -> Dict[str, List]:
    components: List[Dict[str, str]] = []
    connections: List[Dict[str, str]] = []
    current_comp = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("component"):
            match = re.match(r"component\s+(\w+)\s+as\s+(\w+)", line, re.IGNORECASE)
            if not match:
                raise ValueError(f"Could not parse component declaration: {line}")
            name, comp_type = match.groups()
            current_comp = {"name": name, "type": comp_type, "description": comp_type}
            current_comp["inputs"], current_comp["outputs"] = [], []
            components.append(current_comp)
        elif line.lower().startswith("power") and current_comp:
            current_comp.setdefault("metadata", {})["power"] = line.split(" ", 1)[1]
        elif line.lower().startswith("connect"):
            try:
                left, right = line.split("->")
                src = left.replace("connect", "").strip()
                dst = right.strip()
            except ValueError:
                raise ValueError(f"Invalid connect syntax: {line}")
            connections.append({"from": src, "to": dst})
        elif line.lower().startswith("resistor"):
            match = re.match(r"resistor\s+(\S+)\s+between\s+(\S+)\s+and\s+(\S+)", line, re.IGNORECASE)
            if not match:
                raise ValueError(f"Invalid resistor syntax: {line}")
            value, a, b = match.groups()
            r_name = f"R_{len(components)+1}"
            components.append({
                "name": r_name,
                "type": "resistor",
                "description": f"{value} resistor",
                "inputs": ["IN"],
                "outputs": ["OUT"],
            })
            connections.append({"from": a, "to": f"{r_name}.IN"})
            connections.append({"from": f"{r_name}.OUT", "to": b})
        else:
            raise ValueError(f"Unsupported DSL line: {line}")

    if not components:
        raise ValueError("No components defined")
    return {"components": components, "connections": connections}


def _convert_to_design_payload(parsed: Dict[str, List]) -> Dict[str, Any]:
    nets = []
    for idx, conn in enumerate(parsed["connections"]):
        nets.append({
            "name": f"NET_{idx+1}",
            "connections": [
                _split_pin(conn["from"]),
                _split_pin(conn["to"]),
            ],
        })

    design = {
        "components": [
            {
                "name": comp["name"],
                "type": comp.get("type", "generic"),
                "description": comp.get("description", comp.get("type", "component")),
                "inputs": comp.get("inputs", ["IN"]),
                "outputs": comp.get("outputs", ["OUT"]),
            }
            for comp in parsed["components"]
        ],
        "nets": nets,
        "metadata": {"filename": "dsl_model"},
    }
    return design


def _split_pin(token: str) -> Dict[str, str]:
    if "." in token:
        comp, pin = token.split(".", 1)
    else:
        comp, pin = token, "OUT"
    return {"component": comp, "pin": pin}


def _summarize_types(components: List[Dict[str, Any]]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for comp in components:
        comp_type = comp.get("type", "unknown")
        summary[comp_type] = summary.get(comp_type, 0) + 1
    return summary
