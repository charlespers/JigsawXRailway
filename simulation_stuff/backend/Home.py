"""
YC Demo - Landing Page
Production-ready AI PCB simulator with component-based reasoning agents
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.kicad_parser import parse_uploaded_design, get_design_summary

# Page config
st.set_page_config(
    page_title="AI PCB Simulator | YC Demo",
    page_icon="🔌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Session defaults
if "kicad_design" not in st.session_state:
    st.session_state.kicad_design = None
if "design_summary" not in st.session_state:
    st.session_state.design_summary = None

# Apple-style dark theme
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    .stApp {
        background: #000000;
        color: #ffffff;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main .block-container {
        padding-top: 0;
        padding-left: 0;
        padding-right: 0;
        max-width: 1200px;
    }
    
    .hero {
        min-height: 90vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 1.5rem;
        padding: 5rem 2rem 3rem;
    }
    
    .hero h1 {
        font-size: 4rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        margin: 0;
        background: linear-gradient(135deg, #ffffff 0%, #9ea0a6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .hero p {
        font-size: 1.5rem;
        color: #b3b3b8;
        max-width: 720px;
        line-height: 1.5;
    }
    
    .cta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
    }
    
    .cta-btn {
        background: #ffffff;
        color: #000000;
        padding: 0.9rem 2.5rem;
        border-radius: 999px;
        border: none;
        font-weight: 600;
        text-decoration: none;
        transition: all 0.3s ease;
    }
    .cta-btn:hover {
        background: #e5e5ea;
        transform: translateY(-2px);
    }
    .cta-secondary {
        background: transparent;
        color: #ffffff;
        border: 1px solid #4d4d50;
    }
    .cta-secondary:hover {
        border-color: #ffffff;
    }
    
    .stats-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        margin-bottom: 4rem;
    }
    .stat-card {
        background: #0d0d0f;
        border: 1px solid #1f1f24;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
    }
    .stat-card h3 {
        margin: 0;
        font-size: 2rem;
    }
    .stat-card p {
        margin: 0.5rem 0 0;
        font-size: 0.9rem;
        color: #a0a0a5;
    }
    
    .demo-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        margin-bottom: 4rem;
    }
    .demo-card {
        background: #111114;
        border: 1px solid #1d1d22;
        border-radius: 18px;
        padding: 2rem;
        min-height: 260px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: border 0.3s ease;
    }
    .demo-card:hover {
        border-color: #007aff;
    }
    .demo-card h3 {
        margin-top: 0;
        font-size: 1.4rem;
    }
    .demo-card p {
        color: #b3b3b8;
        line-height: 1.5;
    }
    
    .upload-wrapper {
        margin: 4rem 0;
        padding: 3rem 2rem;
        border-radius: 24px;
        border: 1px dashed #2b2b30;
        background: #060607;
        text-align: center;
    }
    
    [data-testid="stFileUploader"] {
        background: #141416 !important;
        border-radius: 16px !important;
        border: 1px dashed #2c2c31 !important;
        padding: 2rem !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #4c4cff !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Hero Section
st.markdown(
    """
<section class="hero">
    <h1>AI Reasoning for PCB Design</h1>
    <p>Upload a KiCad design, assign AI agents to each component, and watch them reason about compatibility, signal integrity, and hardware descriptions—no physics simulator required.</p>
    <div class="cta-row">
        <a class="cta-btn" href="/Simulator" target="_self">Launch Demo 1: Compatibility Simulator</a>
        <a class="cta-btn cta-secondary" href="/Optimizer" target="_self">Demo 2: NL → Optimization</a>
        <a class="cta-btn cta-secondary" href="/Describe" target="_self">Demo 3: Hardware Language</a>
    </div>
</section>
""",
    unsafe_allow_html=True,
)

# Stats Row
summary = st.session_state.design_summary
stat_columns = st.columns(3)
with stat_columns[0]:
    st.markdown('<div class="stat-card"><h3>{}</h3><p>Components Loaded</p></div>'.format(
        summary['components'] if summary else "--"
    ), unsafe_allow_html=True)
with stat_columns[1]:
    st.markdown('<div class="stat-card"><h3>{}</h3><p>Nets Detected</p></div>'.format(
        summary['nets'] if summary else "--"
    ), unsafe_allow_html=True)
with stat_columns[2]:
    st.markdown('<div class="stat-card"><h3>{}</h3><p>KiCad File</p></div>'.format(
        summary['filename'] if summary else "None"
    ), unsafe_allow_html=True)

# Demo Overview
st.markdown("### Choose a Demo")
st.markdown('<div class="demo-grid">', unsafe_allow_html=True)
st.markdown(
    """
<div class="demo-card">
    <div>
        <h3>Demo 1 · Compatibility Simulator</h3>
        <p>Upload a KiCad design, auto-map components, and let AI agents reason about two-part interactions. Toggle wires, change inputs, and watch the graph update with no physics solver.</p>
    </div>
    <a class="cta-btn" href="/Simulator" target="_self">Open Simulator</a>
</div>
<div class="demo-card">
    <div>
        <h3>Demo 2 · Signal Integrity Optimizer</h3>
        <p>Describe constraints in natural language. The optimizer injects Dielectric-style geometry reasoning to suggest routing, impedance, and spacing fixes for your existing PCB.</p>
    </div>
    <a class="cta-btn cta-secondary" href="/Optimizer" target="_self">Launch Optimizer</a>
</div>
<div class="demo-card">
    <div>
        <h3>Demo 3 · Hardware DSL</h3>
        <p>Use a lightweight language to describe hardware from a software lens. Agents auto-generate component graphs and verify logic before you ever open a CAD tool.</p>
    </div>
    <a class="cta-btn cta-secondary" href="/Describe" target="_self">Open DSL Demo</a>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)

# Upload Section
st.markdown("### Upload a KiCad Design")
st.markdown(
    """
<div class="upload-wrapper">
    <p>Drop in a <strong>.kicad_pcb</strong> or JSON export. We parse components, nets, and pin mappings so each demo can reuse the same context.</p>
</div>
""",
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Drop your KiCad board or JSON design",
    type=["kicad_pcb", "json"],
    help="Supported formats: .kicad_pcb, .json"
)

if uploaded_file:
    try:
        design = parse_uploaded_design(uploaded_file)
        summary = get_design_summary(design)
        st.session_state.kicad_design = design
        st.session_state.design_summary = summary
        st.success(f"Imported {summary['components']} components and {summary['nets']} nets from {summary['filename']}")
        st.write("Component types:")
        st.json(summary['types'])
        st.markdown("[Go to Simulator →](/Simulator)")
    except ValueError as exc:
        st.error(str(exc))

# Current Design Context
if st.session_state.kicad_design:
    st.markdown("### Current Session Design")
    cols = st.columns(3)
    summary = st.session_state.design_summary
    cols[0].metric("Components", summary['components'])
    cols[1].metric("Nets", summary['nets'])
    cols[2].metric("Source", summary['filename'])

    st.markdown("#### Type Breakdown")
    st.json(summary['types'])
    st.info("This design is now available in all demos for richer reasoning context.")
else:
    st.warning("Upload a KiCad file to unlock full demo context.")

# Why AI Reasoning Section
st.markdown("### Why Reasoning Beats Traditional Simulation")
st.write(
    """
- Traditional SPICE/TDSpice simulators use heavy physics solvers. We use component-based agents powered by XAI.
- Agents know inputs, outputs, and interfaces. When you toggle a wire, they reason through the graph instantly.
- Works anywhere: deploy to Streamlit Cloud, Railway, Heroku, or Docker without GPU requirements.
    """
)

# Technology Stack
st.markdown("### Built on Dielectric + Jigsaw + XAI")
st.write(
    """
- **Dielectric**: computational geometry & optimization prompts
- **Jigsaw**: natural-language component selection
- **XAI (Grok)**: reasoning engine for component agents
- **KiCad / K-Layout Wrappers**: parse PCB + silicon layouts directly
- **HBM + Robotics Ready**: reason about interposers, breakout channels, and control loops without physics sim
    """
)

st.markdown("### Robotics Simulation Vision")
st.write(
    """
- Upload KiCad/K-Layout designs for your robot’s control stack.
- Agents understand every component, rail, and HBM bus—so “turn this wire off” becomes an instant simulation step.
- No Isaac Sim spin-up: agents reason about cause/effect at the robotics layer while logging every decision.
- Manufacturing teams get actionable routing + power guidance before a single board is ordered.
    """
)

st.markdown("---")
st.markdown("Need help deploying? Check `DEPLOYMENT.md` or run `./run.sh`. Ready when you are.")
