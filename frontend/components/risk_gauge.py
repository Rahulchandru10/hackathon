import plotly.graph_objects as go
import streamlit as st

def render_risk_gauge(score: int, title: str = "Overall Risk Score"):
    """
    Renders a clean speed-gauge chart showing target risk levels using Plotly
    """
    color = "#4ade80" # Green
    if score > 75:
        color = "#F5332C" # Vibrant Red
    elif score > 50:
        color = "#facc15" # Yellow/Orange
    elif score > 20:
        color = "#facc15" # Yellow

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 20, 'family': 'Outfit', 'color': '#CCC8B9'}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#CCC8B9"},
            'bar': {'color': color},
            'bgcolor': "rgba(204, 200, 185, 0.05)",
            'borderwidth': 2,
            'bordercolor': "rgba(204, 200, 185, 0.2)",
            'steps': [
                {'range': [0, 20], 'color': 'rgba(74, 222, 128, 0.15)'},
                {'range': [20, 50], 'color': 'rgba(250, 204, 21, 0.15)'},
                {'range': [50, 75], 'color': 'rgba(245, 51, 44, 0.15)'},
                {'range': [75, 100], 'color': 'rgba(245, 51, 44, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "#F5332C", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#CCC8B9", 'family': "Outfit"},
        margin=dict(l=20, r=20, t=50, b=20),
        height=220
    )

    st.plotly_chart(fig, use_container_width=True)
