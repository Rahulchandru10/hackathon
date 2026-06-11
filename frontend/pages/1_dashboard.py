import streamlit as st
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from utils.api_client import api_client
from utils.styles import apply_custom_styles
from components.kpi_card import render_kpi_card

apply_custom_styles()

st.markdown('<div class="sentinel-title">🛡️ Compliance Dashboard</div>', unsafe_allow_html=True)
st.markdown("---")

async def load_dashboard_data():
    try:
        cases = await api_client.get_cases()
        alerts = await api_client.get_alerts()
        return cases, alerts
    except Exception as e:
        return [], []

cases, alerts = asyncio.run(load_dashboard_data())

# Read directly from protected namespace storage keys
med_high_boundary = st.session_state.get("saved_med_high", 50)

total_cases = len(cases)
high_risk_cases = len([c for c in cases if int(c.get("risk_score", 0)) >= med_high_boundary])
open_alerts = len([a for a in alerts if not a.get("is_read", False)])

col1, col2, col3 = st.columns(3)
with col1:
    render_kpi_card(str(total_cases), "Total Cases Managed", "📁")
with col2:
    render_kpi_card(str(high_risk_cases), "High/Critical Risk Cases", "⚠️")
with col3:
    render_kpi_card(str(open_alerts), "Active Compliance Alerts", "🔔")

st.markdown("### Case Intelligence Queue")

if not cases:
    st.info("No compliance cases have been registered yet. Navigate to the Screening page to initiate one.")
else:
    df_data = []
    for c in cases:
        entity = c.get("entity", {})
        df_data.append({
            "Case ID": c.get("id"),
            "Entity Name": entity.get("name"),
            "Entity Type": entity.get("entity_type"),
            "Risk Score": c.get("risk_score"),
            "Recommendation": c.get("recommendation"),
            "QA Status": c.get("regulator_qa_status"),
            "Created Date": c.get("created_at", "")[:10] if c.get("created_at") else "N/A"
        })
        
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)
    
    st.markdown("### Set Target Case for Investigation")
    selected_id = st.selectbox(
        "Select Case ID to analyze in Results, Network Graph, and Copilot tabs:",
        options=[c["id"] for c in cases],
        format_func=lambda x: f"{x} - {next((item['entity']['name'] for item in cases if item['id'] == x), 'Unknown')}"
    )
    
    if st.button("Activate Investigation Context"):
        st.session_state.selected_case_id = selected_id
        st.success(f"Context activated for Case: {selected_id}")
