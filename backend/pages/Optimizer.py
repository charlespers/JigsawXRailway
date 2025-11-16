"""
Demo 2 - Natural Language Signal Integrity Optimizer
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import load_config

st.set_page_config(
    page_title="Signal Integrity Optimizer | YC Demo",
    page_icon="SIG",
    layout="wide",
)

load_config()  # ensures API key is present
API_ENDPOINT = "https://api.x.ai/v1/chat/completions"
API_KEY = os.getenv("XAI_API_KEY")

st.title("Demo 2 · Natural Language Signal Integrity Optimizer")
st.caption("Describe constraints in plain English and let agents suggest routing fixes.")

summary = st.session_state.get("design_summary")
if summary:
    cols = st.columns(3)
    cols[0].metric("Components", summary["components"])
    cols[1].metric("Nets", summary["nets"])
    cols[2].metric("Source", summary["filename"])
else:
    st.info("Upload a KiCad design on the landing page to provide richer context.")

st.divider()

with st.form("optimizer_form"):
    user_goal = st.text_area(
        "What should we optimize?",
        placeholder="Example: Match the HBM DQ lanes within ±5ps and improve SPI bus crosstalk",
        height=160,
    )
    critical_nets: List[str] = []
    if summary and st.session_state.get("kicad_design"):
        nets = [net.get("name") for net in st.session_state["kicad_design"].get("nets", [])]
        critical_nets = st.multiselect("Optional: highlight key nets", nets[:80])
    submitted = st.form_submit_button("Run Optimizer", use_container_width=True)

if submitted:
    if not user_goal.strip():
        st.error("Please describe a goal or constraint.")
    elif not API_KEY:
        st.error("XAI_API_KEY not configured.")
    else:
        context = {
            "design_summary": summary or {},
            "critical_nets": critical_nets,
            "goal": user_goal.strip(),
        }
        prompt = f"""
You are a signal-integrity optimization agent for robotics/PCB systems.
Design context: {json.dumps(context, indent=2)}
Suggest actionable routing/stackup changes without running physics simulations.
Return ONLY JSON with keys summary (string), recommendations ([string]), constraints ([{{"target": str, "rule": str, "rationale": str}}]), follow_up_questions ([string]).
"""
        payload = {
            "model": "grok-beta",
            "messages": [
                {"role": "system", "content": "You are a PCB signal-integrity expert. Return only JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": float(os.getenv("XAI_TEMPERATURE", "0.2")),
            "max_tokens": 1200,
        }
        try:
            with st.spinner("Reasoning about signal integrity..."):
                resp = requests.post(
                    API_ENDPOINT,
                    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=45,
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                result = json.loads(content[content.find("{") : content.rfind("}") + 1])
        except Exception as exc:
            st.error(f"Optimizer failed: {exc}")
        else:
            st.success("Optimization complete")
            st.subheader("Summary")
            st.write(result.get("summary", "No summary available"))

            if result.get("recommendations"):
                st.subheader("Recommendations")
                for rec in result["recommendations"]:
                    st.markdown(f"- {rec}")

            if result.get("constraints"):
                st.subheader("Constraints to Apply")
                for constraint in result["constraints"]:
                    st.markdown(
                        f"**{constraint.get('target', 'Net')}**: {constraint.get('rule')}  "
                        f"_Reason_: {constraint.get('rationale')}"
                    )

            if result.get("follow_up_questions"):
                st.subheader("Follow-up Questions")
                st.write("; ".join(result["follow_up_questions"]))
else:
    st.markdown("#### How it works")
    st.write(
        """
1. Describe what needs improvement (e.g., "Route HBM data lanes with matched length").
2. Select critical nets from the uploaded KiCad design (optional).
3. We feed the goal + design context into Grok and return structured actions.
4. Perfect for early-stage robotics boards where physics solvers are too heavy.
        """
    )
