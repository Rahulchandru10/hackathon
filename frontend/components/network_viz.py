import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
import tempfile
import os

def render_network_graph(nodes: list, edges: list):
    """
    Renders an interactive corporate relationship graph using pyvis and st.components.v1.html
    """
    if not nodes:
        st.info("No network node relationships detected.")
        return

    # Create network graph
    net = Network(height="450px", width="100%", bgcolor="#000000", font_color="#CCC8B9")
    
    # Configure physics for smooth network organization
    net.force_atlas_2based()
    
    # Add Nodes
    for n in nodes:
        group = n.get("group", "Entity")
        
        # Color mapping based on node category
        color = "#CCC8B9" # primary warm gray
        if group == "Target":
            color = "#F5332C" # Red
            size = 25
        elif group == "Person":
            color = "#38bdf8" # Light Cyan/Blue
            size = 18
        elif group == "BeneficialOwner":
            color = "#c084fc" # Light Purple
            size = 20
        elif group == "Sanction":
            color = "#f87171" # Light Red
            size = 22
        elif group == "Article":
            color = "#facc15" # Light Yellow
            size = 15
        else:
            color = "#9ca3af" # Grey
            size = 15
            
        net.add_node(
            n["id"], 
            label=n["label"], 
            title=f"Category: {group}\nType: {n.get('type')}\nRisk: {n.get('risk_score', 0)}/100",
            color=color,
            size=size
        )
        
    # Add Edges
    for e in edges:
        net.add_edge(e["from"], e["to"], label=e.get("label", ""))

    # Save to temp HTML and display
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "network.html")
            net.write_html(path, open_browser=False, notebook=False)
            
            with open(path, "r", encoding="utf-8") as f:
                html_code = f.read()
                
            components.html(html_code, height=470)
    except Exception as e:
        st.error(f"Failed to render Neo4j relationship graph: {e}")
