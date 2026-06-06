import streamlit as st
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import api_client
from utils.styles import apply_custom_styles
from components.network_viz import render_network_graph

apply_custom_styles()

st.markdown('<div class="sentinel-title">🕸️ Corporate Network Graph</div>', unsafe_allow_html=True)
st.markdown("---")

case_id = st.session_state.get("selected_case_id")

if not case_id:
    st.info("No active case context. Please select a case from the Dashboard or run a new Screening query.")
else:
    st.subheader(f"Neo4j Relationship Graph Context: {case_id}")
    st.markdown("Explore corporate network structures, ultimate beneficial owners (UBOs), related directors, and flagged sanctions links.")

    async def load_graph():
        net = await api_client.get_network(case_id)
        return net

    with st.spinner("Fetching Neo4j graph nodes..."):
        try:
            network_data = asyncio.run(load_graph())
            render_network_graph(network_data.get("nodes", []), network_data.get("edges", []))
        except Exception as e:
            st.error(f"Failed to fetch relationship graph: {e}")

    st.markdown("---")
    st.markdown("##### Node Category Legend")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("<span style='color:#F5332C; font-weight:700'>● Primary Target</span>", unsafe_allow_html=True)
    with col2:
        st.markdown("<span style='color:#38bdf8; font-weight:700'>● Directors / Persons</span>", unsafe_allow_html=True)
    with col3:
        st.markdown("<span style='color:#c084fc; font-weight:700'>● UBOs (Beneficial Owners)</span>", unsafe_allow_html=True)
    with col4:
        st.markdown("<span style='color:#f87171; font-weight:700'>● Sanctions / Watchlists</span>", unsafe_allow_html=True)
    with col5:
        st.markdown("<span style='color:#facc15; font-weight:700'>● Adverse Articles</span>", unsafe_allow_html=True)
