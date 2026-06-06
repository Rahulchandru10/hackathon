import streamlit as st
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import api_client
from utils.styles import apply_custom_styles

apply_custom_styles()

st.markdown('<div class="sentinel-title">🔔 Continuous Monitoring & Alerts Feed</div>', unsafe_allow_html=True)
st.markdown("---")

async def load_monitoring_details():
    subs = await api_client.get_subscriptions()
    alerts = await api_client.get_alerts()
    return subs, alerts

try:
    subs, alerts = asyncio.run(load_monitoring_details())
except Exception as e:
    st.error(f"Failed to load monitoring dashboard: {e}")
    st.stop()

col_feed, col_sub = st.columns([2, 1])

with col_feed:
    st.markdown("### Active Compliance Alerts Feed")
    if not alerts:
        st.info("No active alerts logged by the background monitoring scheduler.")
    else:
        for al in alerts:
            severity = al.get("severity", "LOW")
            sev_color = "#F5332C" if severity in ("HIGH", "CRITICAL") else "#facc15"
            
            st.markdown(f"""
                <div style="
                    background: rgba(18, 18, 17, 0.85);
                    border-left: 4px solid {sev_color};
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 10px;
                    border-top: 1px solid rgba(204, 200, 185, 0.1);
                    border-right: 1px solid rgba(204, 200, 185, 0.1);
                    border-bottom: 1px solid rgba(204, 200, 185, 0.1);
                    box-shadow: 0 4px 6px rgba(0,0,0,0.5);
                ">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #CCC8B9; opacity: 0.7;">
                        Type: {al.get('alert_type')} | Severity: {severity} | Date: {al.get('created_at', '')[:19]}
                    </div>
                    <div style="font-size: 1rem; color: #CCC8B9; margin-top: 4px; font-weight:600;">
                        {al.get('description')}
                    </div>
                </div>
            """, unsafe_allow_html=True)

with col_sub:
    st.markdown("### Create New Monitoring Subscription")
    with st.form("new_subscription_form"):
        sub_name = st.text_input("Target Name to Monitor")
        sub_freq = st.selectbox("Interval Frequency", options=["Daily", "Weekly"])
        sub_country = st.text_input("Target Country Context")
        
        submitted = st.form_submit_button("Subscribe Target to Scheduler")
        
        if submitted:
            if not sub_name or not sub_name.strip():
                st.error("Name is required to subscribe.")
            else:
                payload = {
                    "entity_name": sub_name.strip(),
                    "frequency": sub_freq,
                    "country": sub_country.strip() if sub_country else None
                }
                try:
                    asyncio.run(api_client.subscribe(payload))
                    st.success(f"Successfully subscribed {sub_name} to continuous monitoring checks.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Subscription creation failed: {e}")

    st.markdown("---")
    st.markdown("### Active Monitoring Subscriptions")
    if not subs:
        st.write("No active subscriptions.")
    else:
        for s in subs:
            ts = s.get('last_checked', '')
            st.markdown(f"**{s.get('entity_name')}** ({s.get('frequency')}) - Last checked: {ts[:19] if ts else 'N/A'}")
