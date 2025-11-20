"""
PCB Design Generator - Streamlit Page
Natural language input → Complete PCB design with BOM and connections
"""

import streamlit as st
import sys
import json
from pathlib import Path

# Add development_demo to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.design_orchestrator import DesignOrchestrator

st.set_page_config(
    page_title="PCB Design Generator | Development Demo",
    page_icon="🔌",
    layout="wide",
)

# Header with demo link
col_header1, col_header2 = st.columns([1, 4])
with col_header1:
    if st.button("🎯 Go to Demo", use_container_width=True, help="Open interactive visualization demo"):
        st.switch_page("pages/VisualDemo.py")
with col_header2:
    st.title("PCB Design Generator")
    st.caption("Describe your circuit in natural language and get a complete design with BOM and connections")

# Provider selection
import os
col1, col2 = st.columns([3, 1])
with col1:
    st.write("")  # Spacing
with col2:
    provider = st.selectbox(
        "LLM Provider",
        ["openai", "xai"],
        index=0 if os.getenv("LLM_PROVIDER", "openai").lower() == "openai" else 1,
        help="Choose between OpenAI or XAI (Grok) for LLM reasoning"
    )
    # Set environment variable for this session
    os.environ["LLM_PROVIDER"] = provider

# Example queries
EXAMPLE_QUERIES = [
    "temperature sensor with wifi and 5V-USBC",
    "ESP32 with temperature sensor and USB-C power",
    "WiFi enabled temperature monitoring board with 5V USB-C input"
]

st.sidebar.header("Example Queries")
for example in EXAMPLE_QUERIES:
    if st.sidebar.button(example, key=f"example_{example}", use_container_width=True):
        st.session_state.user_query = example

# Main input
user_query = st.text_area(
    "Describe your PCB design:",
    value=st.session_state.get("user_query", ""),
    placeholder="Example: temperature sensor with wifi and 5V-USBC",
    height=100
)

if st.button("Generate Design", type="primary", use_container_width=True):
    if not user_query.strip():
        st.error("Please enter a design description.")
    else:
        with st.spinner("Generating design... This may take a minute."):
            try:
                orchestrator = DesignOrchestrator()
                design = orchestrator.generate_design(user_query)
                
                if "error" in design:
                    st.error(f"Design generation failed: {design['error']}")
                    if "design_state" in design:
                        st.json(design["design_state"])
                else:
                    st.session_state.design = design
                    st.success("Design generated successfully!")
                    st.rerun()
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# Display results
if "design" in st.session_state:
    design = st.session_state.design
    
    if "error" not in design:
        # Summary metrics
        st.divider()
        bom = design.get("bom", {})
        bom_items = bom.get("items", []) if isinstance(bom, dict) else bom
        bom_summary = bom.get("summary", {}) if isinstance(bom, dict) else {}
        
        cols = st.columns(5)
        cols[0].metric("Selected Parts", len(design.get("selected_parts", {})))
        cols[1].metric("External Components", len(design.get("external_components", [])))
        cols[2].metric("Nets", len(design.get("connections", [])))
        cols[3].metric("BOM Items", len(bom_items))
        if bom_summary.get("total_cost"):
            cols[4].metric("Total BOM Cost", f"${bom_summary['total_cost']:.2f}")
        
        # Architecture
        st.subheader("Architecture")
        architecture = design.get("architecture", {})
        if architecture:
            anchor = architecture.get("anchor_block", {})
            if anchor:
                st.write(f"**Anchor Part:** {anchor.get('type', 'N/A')} - {anchor.get('description', '')}")
            
            child_blocks = architecture.get("child_blocks", [])
            if child_blocks:
                st.write("**Child Blocks:**")
                for block in child_blocks:
                    st.write(f"- {block.get('type', 'N/A')}: {block.get('description', '')}")
        
        # Selected Parts
        st.subheader("Selected Parts")
        selected_parts = design.get("selected_parts", {})
        for block_name, part_data in selected_parts.items():
            with st.expander(f"{block_name}: {part_data.get('name', 'N/A')}"):
                cols = st.columns(2)
                cols[0].write(f"**Manufacturer:** {part_data.get('manufacturer', 'N/A')}")
                cols[0].write(f"**Part Number:** {part_data.get('mfr_part_number', 'N/A')}")
                cols[1].write(f"**Category:** {part_data.get('category', 'N/A')}")
                cols[1].write(f"**Package:** {part_data.get('package', 'N/A')}")
                
                if part_data.get('cost_estimate'):
                    cost = part_data['cost_estimate']
                    st.write(f"**Cost:** ${cost.get('value', 'N/A')} @ {cost.get('quantity', 'N/A')} qty")
                
                # Show compatibility results if available
                compat_results = design.get("compatibility_results", {})
                if block_name in compat_results:
                    compat = compat_results[block_name]
                    if compat.get("compatible"):
                        st.success("✓ Compatible")
                    else:
                        st.error("✗ Not Compatible")
                    if compat.get("warnings"):
                        for warning in compat["warnings"]:
                            st.warning(warning)
        
        # External Components
        st.subheader("External Components")
        ext_comps = design.get("external_components", [])
        if ext_comps:
            # Group by type
            grouped = {}
            for comp in ext_comps:
                comp_type = comp.get("type", "unknown")
                if comp_type not in grouped:
                    grouped[comp_type] = []
                grouped[comp_type].append(comp)
            
            for comp_type, comps in grouped.items():
                st.write(f"**{comp_type.upper()}:**")
                for comp in comps:
                    st.write(f"- {comp.get('value', 'N/A')} {comp_type} ({comp.get('package', 'N/A')}) - {comp.get('purpose', '')}")
        
        # Connections (Netlist)
        st.subheader("Connection List (Netlist)")
        connections = design.get("connections", [])
        if connections:
            for net in connections:
                net_name = net.get("net_name", "UNKNOWN")
                net_class = net.get("net_class", "signal")
                net_connections = net.get("connections", [])
                current = net.get("current_estimate_amps")
                trace_width = net.get("recommended_trace_width_mils")
                impedance = net.get("impedance_ohms")
                
                net_info = f"**{net_name}** ({net_class})"
                if current:
                    net_info += f" | Current: {current:.3f}A"
                if trace_width:
                    net_info += f" | Trace Width: {trace_width} mils"
                if impedance:
                    net_info += f" | Impedance: {impedance}Ω"
                
                st.write(net_info)
                for conn in net_connections:
                    if len(conn) >= 2:
                        st.write(f"  - {conn[0]}.{conn[1]}")
        else:
            st.info("No connections generated")
        
        # Design Analysis
        design_analysis = design.get("design_analysis", {})
        if design_analysis:
            st.subheader("Design Analysis")
            
            # Power Analysis
            power_analysis = design_analysis.get("power_analysis", {})
            if power_analysis:
                with st.expander("Power Analysis", expanded=True):
                    cols = st.columns(3)
                    cols[0].metric("Total Power", f"{power_analysis.get('total_power_watts', 0):.3f}W")
                    cols[1].metric("Power Rails", len(power_analysis.get("power_rails", {})))
                    
                    power_rails = power_analysis.get("power_rails", {})
                    if power_rails:
                        st.write("**Power Rails:**")
                        for rail_name, rail_info in power_rails.items():
                            st.write(f"- {rail_name}: {rail_info.get('current_amps', 0):.3f}A @ {rail_info.get('voltage', 0)}V = {rail_info.get('power_watts', 0):.3f}W")
                    
                    power_hungry = power_analysis.get("power_hungry_components", [])
                    if power_hungry:
                        st.write("**High Power Components:**")
                        for comp in power_hungry[:5]:  # Top 5
                            st.write(f"- {comp['part_id']}: {comp['power_watts']}W")
            
            # Thermal Analysis
            thermal_analysis = design_analysis.get("thermal_analysis", {})
            if thermal_analysis:
                with st.expander("Thermal Analysis"):
                    thermal_issues = thermal_analysis.get("thermal_issues", [])
                    if thermal_issues:
                        st.warning(f"Found {len(thermal_issues)} thermal issue(s)")
                        for issue in thermal_issues:
                            st.write(f"- **{issue['part_id']}**: {issue['issue']}")
                            if 'junction_temp_c' in issue:
                                st.write(f"  Junction Temp: {issue['junction_temp_c']}°C (Max: {issue.get('max_temp_c', 'N/A')}°C)")
                    else:
                        st.success("No thermal issues detected")
            
            # Design Rule Checks
            drc = design_analysis.get("design_rule_checks", {})
            if drc:
                with st.expander("Design Rule Checks"):
                    if drc.get("passed", False):
                        st.success("✓ All design rule checks passed")
                    else:
                        errors = drc.get("errors", [])
                        warnings = drc.get("warnings", [])
                        if errors:
                            st.error(f"Found {len(errors)} error(s):")
                            for error in errors:
                                st.write(f"- **{error.get('type', 'Unknown')}**: {error.get('message', '')}")
                        if warnings:
                            st.warning(f"Found {len(warnings)} warning(s):")
                            for warning in warnings[:10]:  # Show first 10
                                st.write(f"- **{warning.get('type', 'Unknown')}**: {warning.get('message', '')}")
            
            # Recommendations
            recommendations = design_analysis.get("recommendations", [])
            if recommendations:
                with st.expander("Design Recommendations"):
                    for rec in recommendations:
                        st.write(f"- {rec}")
        
        # BOM
        st.subheader("Bill of Materials (BOM)")
        bom = design.get("bom", {})
        bom_items = bom.get("items", []) if isinstance(bom, dict) else bom
        bom_summary = bom.get("summary", {}) if isinstance(bom, dict) else {}
        
        if bom_items:
            # Create DataFrame for better display
            import pandas as pd
            
            bom_data = []
            for item in bom_items:
                bom_data.append({
                    "Designator": item.get("designator", ""),
                    "Qty": item.get("qty", 1),
                    "Manufacturer": item.get("manufacturer", ""),
                    "Part Number": item.get("mfr_part_number", ""),
                    "Description": item.get("description", ""),
                    "Category": item.get("category", ""),
                    "Package": item.get("package", ""),
                    "Value": item.get("value", ""),
                    "Tolerance": item.get("tolerance", ""),
                    "Unit Cost": f"${item.get('unit_cost', 0):.4f}" if item.get("unit_cost") else "",
                    "Extended Cost": f"${item.get('extended_cost', 0):.4f}" if item.get("extended_cost") else "",
                    "Lifecycle": item.get("lifecycle_status", ""),
                    "RoHS": "Yes" if item.get("rohs_compliant", True) else "No",
                    "Notes": item.get("notes", "")
                })
            
            df = pd.DataFrame(bom_data)
            st.dataframe(df, use_container_width=True)
            
            # BOM Summary
            if bom_summary:
                st.write("**BOM Summary:**")
                cols = st.columns(4)
                cols[0].metric("Total Parts", bom_summary.get("total_parts", 0))
                cols[1].metric("Total Qty", bom_summary.get("total_qty", 0))
                cols[2].metric("Total Cost", f"${bom_summary.get('total_cost', 0):.2f}")
            
            # Download options
            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download BOM as CSV",
                    csv,
                    "bom.csv",
                    "text/csv",
                    key="download_csv"
                )
            with col2:
                json_str = json.dumps(design, indent=2)
                st.download_button(
                    "Download Full Design as JSON",
                    json_str,
                    "design.json",
                    "application/json",
                    key="download_json"
                )
        else:
            st.info("No BOM generated")
        
        # Raw JSON view
        with st.expander("View Raw Design JSON"):
            st.json(design)

