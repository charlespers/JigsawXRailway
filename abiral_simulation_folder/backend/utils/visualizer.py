"""
PCB Visualization for Simulator
"""

import plotly.graph_objects as go
import numpy as np
from typing import Dict, List, Any


def create_pcb_sim_visualization(registry: Any) -> go.Figure:
    """
    Create PCB layout visualization showing components and connections.
    
    Args:
        registry: ComponentRegistry with all components
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    components = registry.get_all_components()
    connections = registry.connections
    
    if not components:
        # Empty board
        fig.add_annotation(
            text="No components to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color="#86868b")
        )
        fig.update_layout(
            xaxis=dict(range=[0, 100], visible=False),
            yaxis=dict(range=[0, 100], visible=False),
            plot_bgcolor="#000000",
            paper_bgcolor="#000000",
            width=800,
            height=600
        )
        return fig
    
    # Draw board outline
    fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=120, y1=100,
        line=dict(color="#424245", width=2),
        fillcolor="rgba(0, 0, 0, 0.1)",
        layer="below"
    )
    
    # Draw connections first (so they're behind components)
    for conn in connections:
        from_comp = components.get(conn['from'])
        to_comp = components.get(conn['to'])
        
        if from_comp and to_comp:
            x0, y0 = from_comp['position']['x'], from_comp['position']['y']
            x1, y1 = to_comp['position']['x'], to_comp['position']['y']
            
            # Draw trace as line
            fig.add_trace(go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(color="#007aff", width=2),
                showlegend=False,
                hovertemplate=f"{conn['from']}.{conn['from_output']} → {conn['to']}.{conn['to_input']}<extra></extra>"
            ))
    
    # Draw components
    for comp_id, comp in components.items():
        x, y = comp['position']['x'], comp['position']['y']
        comp_type = comp['type']
        
        # Component color based on type
        colors = {
            'mcu': '#ff3b30',
            'led': '#34c759',
            'resistor': '#ffa657',
            'sensor': '#af52de'
        }
        color = colors.get(comp_type, '#8e8e93')
        
        # Component size based on type
        sizes = {
            'mcu': 15,
            'led': 8,
            'resistor': 10,
            'sensor': 12
        }
        size = sizes.get(comp_type, 10)
        
        # Draw component as shape
        fig.add_shape(
            type="rect",
            x0=x-size/2, y0=y-size/2,
            x1=x+size/2, y1=y+size/2,
            fillcolor=color,
            line=dict(color="#ffffff", width=1),
            layer="above"
        )
        
        # Component label
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode="text",
            text=comp['name'],
            textfont=dict(size=8, color="#ffffff", family="monospace"),
            textposition="top center",
            showlegend=False,
            hovertemplate=f"<b>{comp['name']}</b><br>Type: {comp_type}<br>Inputs: {', '.join(comp['inputs'])}<br>Outputs: {', '.join(comp['outputs'])}<extra></extra>"
        ))
        
        # Draw I/O pins as small circles
        num_inputs = len(comp['inputs'])
        num_outputs = len(comp['outputs'])
        
        # Input pins (left side)
        for i in range(num_inputs):
            pin_y = y - (num_inputs-1)*2 + i*4
            fig.add_trace(go.Scatter(
                x=[x-size/2-2], y=[pin_y],
                mode="markers",
                marker=dict(size=4, color="#ff9500"),
                showlegend=False,
                hoverinfo="skip"
            ))
        
        # Output pins (right side)
        for i in range(num_outputs):
            pin_y = y - (num_outputs-1)*2 + i*4
            fig.add_trace(go.Scatter(
                x=[x+size/2+2], y=[pin_y],
                mode="markers",
                marker=dict(size=4, color="#00c7be"),
                showlegend=False,
                hoverinfo="skip"
            ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="PCB Layout Simulation",
            font=dict(size=20, color="#ffffff", family="-apple-system"),
            x=0.5,
            xanchor="center"
        ),
        xaxis=dict(
            range=[-10, 130],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        yaxis=dict(
            range=[-10, 110],
            showgrid=False,
            showticklabels=False,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1
        ),
        plot_bgcolor="#0a0a0a",
        paper_bgcolor="#000000",
        width=900,
        height=700,
        hovermode="closest",
        showlegend=False
    )
    
    return fig

