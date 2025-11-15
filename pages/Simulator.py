"""
Demo 1 - Compatibility Simulator
Assign AI agents to KiCad components, toggle wires, and watch reasoning flow.
"""

from __future__ import annotations

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.component_agent import ComponentAgent
from components.component_registry import ComponentRegistry
from utils.visualizer import create_pcb_sim_visualization
from utils.config import load_config
from utils.kicad_parser import import_design_into_registry
from utils.scheduler import AgentScheduler

st.set_page_config(
    page_title="PCB Simulator | YC Demo",
    page_icon="🔌",
    layout="wide",
    initial_sidebar_state="expanded"
)

config = load_config()
if "registry" not in st.session_state:
    st.session_state.registry = ComponentRegistry()
if "agents" not in st.session_state:
    st.session_state.agents: Dict[str, ComponentAgent] = {}
if "simulation_log" not in st.session_state:
    st.session_state.simulation_log: List[Dict[str, Any]] = []
if "loaded_design_id" not in st.session_state:
    st.session_state.loaded_design_id = None

registry = st.session_state.registry
agents = st.session_state.agents
scheduler = AgentScheduler(registry)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def ensure_agent_exists(name: str, comp_data: Dict[str, Any]):
    if name not in agents:
        agents[name] = ComponentAgent(
            component_id=name,
            component_type=comp_data.get("type", "generic"),
            inputs=comp_data.get("inputs", []),
            outputs=comp_data.get("outputs", []),
            description=comp_data.get("description", "Manual component"),
        )


def _summarize_types(components: List[Dict[str, Any]]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for comp in components:
        comp_type = comp.get("type", "unknown")
        summary[comp_type] = summary.get(comp_type, 0) + 1
    return summary


def load_design_payload(design: Dict[str, Any], label: str):
    registry.clear()
    agents.clear()
    for comp in design.get("components", []):
        registry.add_component(comp["name"], comp)
        ensure_agent_exists(comp["name"], comp)
    for conn in design.get("connections", []):
        registry.add_connection(conn["from"], conn["from_output"], conn["to"], conn["to_input"])
    st.session_state.loaded_design_id = label
    st.session_state.design_summary = {
        "filename": label,
        "components": len(design.get("components", [])),
        "nets": len(design.get("connections", [])),
        "types": _summarize_types(design.get("components", [])),
    }
    st.session_state.simulation_log.append({
        "component": "system",
        "message": f"{label} loaded into simulator",
    })


def run_agent_reasoning(component_id: str, note: str = ""):
    scheduler.mark_dirty(component_id)
    entries = scheduler.run(agents, note)
    for entry in entries:
        st.session_state.simulation_log.append(
            {
                "component": entry["component"],
                "message": entry["result"].get("reasoning"),
                "note": entry.get("note", note),
                "outputs": entry["result"].get("output_changes"),
            }
        )


def run_global_simulation(note: str = "Global run"):
    for comp in registry.components.keys():
        scheduler.mark_dirty(comp)
    entries = scheduler.run(agents, note)
    for entry in entries:
        st.session_state.simulation_log.append(
            {
                "component": entry["component"],
                "message": entry["result"].get("reasoning"),
                "note": entry.get("note", note),
                "outputs": entry["result"].get("output_changes"),
            }
        )


HBM_SAMPLE = {
    "components": [
        {"name": "HBM_STACK", "type": "hbm", "description": "High-bandwidth memory", "inputs": ["VDD", "VSS", "REFCLK", "RESET#"], "outputs": ["DQ0", "DQ1", "DQ2", "DQ3"]},
        {"name": "INTERPOSER_SERDES", "type": "serdes", "description": "Interposer routing", "inputs": ["HBM_DQ0", "HBM_DQ1", "HBM_DQ2", "HBM_DQ3"], "outputs": ["GPU_RX0", "GPU_RX1", "GPU_RX2", "GPU_RX3"]},
        {"name": "GPU_CTRL", "type": "mcu", "description": "GPU controller", "inputs": ["3V3", "GND"], "outputs": ["HBM_RESET#", "HBM_CLK"]},
        {"name": "POWER_REG", "type": "regulator", "description": "3.3V rail", "inputs": ["VIN", "GND"], "outputs": ["3V3"]},
    ],
    "connections": [
        {"from": "POWER_REG", "from_output": "3V3", "to": "GPU_CTRL", "to_input": "3V3"},
        {"from": "POWER_REG", "from_output": "3V3", "to": "HBM_STACK", "to_input": "VDD"},
        {"from": "GPU_CTRL", "from_output": "HBM_RESET#", "to": "HBM_STACK", "to_input": "RESET#"},
        {"from": "GPU_CTRL", "from_output": "HBM_CLK", "to": "HBM_STACK", "to_input": "REFCLK"},
        {"from": "HBM_STACK", "from_output": "DQ0", "to": "INTERPOSER_SERDES", "to_input": "HBM_DQ0"},
        {"from": "HBM_STACK", "from_output": "DQ1", "to": "INTERPOSER_SERDES", "to_input": "HBM_DQ1"},
        {"from": "HBM_STACK", "from_output": "DQ2", "to": "INTERPOSER_SERDES", "to_input": "HBM_DQ2"},
        {"from": "HBM_STACK", "from_output": "DQ3", "to": "INTERPOSER_SERDES", "to_input": "HBM_DQ3"},
    ],
}

# ---------------------------------------------------------------------------
# Auto-import KiCad design from landing page upload
# ---------------------------------------------------------------------------
uploaded_design = st.session_state.get("kicad_design")
if uploaded_design:
    design_id = uploaded_design.get("metadata", {}).get("fingerprint")
    if design_id and design_id != st.session_state.loaded_design_id:
        import_design_into_registry(uploaded_design, registry)
        agents.clear()
        for comp_id, comp in registry.components.items():
            ensure_agent_exists(comp_id, comp)
        st.session_state.loaded_design_id = design_id
        st.session_state.simulation_log.append({
            "component": "system",
            "message": f"Design imported from {uploaded_design.get('metadata', {}).get('filename', 'KiCad file')}",
        })

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("Demo 1 · Compatibility Simulator")
st.caption("Component-based agents reason about PCB behavior with zero physics simulation.")

summary_block = st.session_state.get("design_summary")
if summary_block:
    cols = st.columns(3)
    cols[0].metric("Components", summary_block["components"])
    cols[1].metric("Nets", summary_block["nets"])
    cols[2].metric("Source", summary_block["filename"])
else:
    st.info("Upload a KiCad design on the landing page or add components manually below.")

st.divider()
st.info("Need a reference design? Load the built-in HBM/robotics sample from the sidebar to see how agents reason about memory breakout and interposer routing.")

sidebar = st.sidebar
sidebar.header("Component Library")
component_templates = {
    "Microcontroller": {"type": "mcu", "inputs": ["VCC", "GND", "RESET"], "outputs": ["GPIO1", "GPIO2", "TX", "RX"], "description": "Generic MCU"},
    "LED": {"type": "led", "inputs": ["ANODE", "CATHODE"], "outputs": [], "description": "Indicator LED"},
    "Resistor": {"type": "resistor", "inputs": ["IN"], "outputs": ["OUT"], "description": "Current-limiting resistor"},
    "Sensor": {"type": "sensor", "inputs": ["VCC", "GND"], "outputs": ["DATA"], "description": "Generic sensor"},
}
choice = sidebar.selectbox("Template", list(component_templates.keys()))
default_name = f"{choice}_{len(registry.components)+1}"
comp_name = sidebar.text_input("Component Name", default_name)
if sidebar.button("Add Component", use_container_width=True):
    payload = component_templates[choice].copy()
    payload["name"] = comp_name
    registry.add_component(comp_name, payload)
    ensure_agent_exists(comp_name, payload)
    st.experimental_rerun()

if sidebar.button("Load HBM Sample", use_container_width=True):
    load_design_payload(HBM_SAMPLE, "HBM_SAMPLE")
    st.experimental_rerun()

if sidebar.button("Clear All", use_container_width=True):
    registry.clear()
    agents.clear()
    st.session_state.loaded_design_id = None
    st.session_state.simulation_log = []
    st.experimental_rerun()

# Focus pair compatibility
comp_names = list(registry.components.keys())
if comp_names:
    st.subheader("Focus Pair")
    c1, c2 = st.columns(2)
    focus_a = c1.selectbox("Component A", comp_names)
    focus_b = c2.selectbox("Component B", comp_names)
    if focus_a and focus_b and focus_a != focus_b:
        agent_a = agents.get(focus_a)
        other_state = registry.get_component_state(focus_b)
        if agent_a and other_state:
            compat = agent_a.evaluate_compatibility(other_state, registry)
            st.metric("Compatible?", "Yes" if compat.get("compatible") else "Needs attention")
            st.write(compat.get("reasoning"))
            if compat.get("risks"):
                for risk in compat["risks"]:
                    st.warning(risk)

# Wire/input controls
if comp_names:
    st.subheader("Wire / Input Controls")
    with st.form("wire_controls"):
        ctl_component = st.selectbox("Component", comp_names, key="wire_component")
        inputs = registry.components[ctl_component]["inputs"] or ["IN"]
        ctl_input = st.selectbox("Input", inputs)
        new_state = st.selectbox("State", ["HIGH", "LOW", "FLOAT", "OFF"])
        note = st.text_input("Reason for change", "Manual toggle")
        submitted = st.form_submit_button("Apply + Reason", use_container_width=True)
    if submitted:
        registry.update_inputs(ctl_component, {ctl_input: new_state})
        run_agent_reasoning(ctl_component, note)

# Simulation controls
st.subheader("Simulation Control")
if st.button("Run Global Simulation", disabled=len(comp_names) < 2):
    run_global_simulation()
    st.success("Simulation complete")

st.metric("Active Components", len(comp_names))
st.metric("Active Agents", len(agents))
st.metric("Connections", registry.count_connections())

# Active component list
st.subheader("Active Components")
if not comp_names:
    st.info("No components yet. Upload a KiCad board or load the sample design.")
else:
    for comp_id, comp in registry.components.items():
        st.markdown(f"### {comp_id} · {comp.get('type', '').upper()}")
        cols = st.columns(2)
        cols[0].write(f"**Inputs:** {comp.get('inputs')}")
        cols[1].write(f"**Outputs:** {comp.get('outputs')}")
        with st.expander("Reasoning history"):
            agent = agents.get(comp_id)
            if agent and agent.reasoning_history:
                for entry in reversed(agent.reasoning_history[-3:]):
                    st.markdown(f"- {entry['reasoning']}")
            else:
                st.caption("No reasoning yet")

# Visualization
st.subheader("PCB Layout View")
if comp_names:
    fig = create_pcb_sim_visualization(registry)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Add components to see the layout")

# Reasoning log
st.subheader("Reasoning Log")
if st.session_state.simulation_log:
    for entry in reversed(st.session_state.simulation_log[-10:]):
        st.write(f"**{entry['component']}** · {entry.get('note', '')}")
        st.write(entry.get("message"))
else:
    st.caption("Run a simulation to populate the log")
