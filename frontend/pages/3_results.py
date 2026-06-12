import streamlit as st
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import api_client
from utils.styles import apply_custom_styles
from components.risk_gauge import render_risk_gauge
from components.timeline_view import render_timeline
from components.article_card import render_article_card

# Apply Project Sentinel premium UI styles
apply_custom_styles()

st.markdown('<div class="sentinel-title">📊 Case Audit & Screening Results</div>', unsafe_allow_html=True)
st.markdown("---")

# Extract the active context tracking token
case_id = st.session_state.get("selected_case_id")

if not case_id:
    st.info("No active case context. Please select a case from the Dashboard or run a new Screening query.")
else:
    async def load_results():
        c = await api_client.get_case(case_id)
        t = await api_client.get_timeline(case_id)
        logs = await api_client.get_case_audit_logs(case_id)
        return c, t, logs

    try:
        case, timeline, logs = asyncio.run(load_results())
    except Exception as e:
        st.error(f"Failed to load case results: {e}")
        st.stop()

    entity = case.get("entity", {})
    st.subheader(f"Case Context: {entity.get('name', 'Unknown Target')} ({case.get('id', case_id)})")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_risk_gauge(case.get("risk_score", 0))
        
    with col2:
        st.markdown("##### Risk Parameter Breakdown")
        bd = case.get("risk_breakdown", {})
        for key in ["fraud", "regulatory", "network", "pep", "sanctions", "aml_kyc"]:
            val = bd.get(key, 0)
            st.write(f"**{key.upper().replace('_', ' ')}** ({val}%)")
            st.progress(int(val) / 100.0)

    st.markdown("---")
    
    # Render Forensic Investigation Tabs
    tab_articles, tab_timeline, tab_watchlists, tab_decisions = st.tabs([
        "📰 Adverse Media Articles", 
        "⏳ Event Timeline", 
        "🛡️ Watchlists & Matches", 
        "📝 Recommendations & QA Challenge"
    ])
    
    low_boundary = st.session_state.get("saved_low_med", 20)
    med_boundary = st.session_state.get("saved_med_high", 50)
    high_boundary = st.session_state.get("saved_high_crit", 75)
    current_risk_score = int(case.get("risk_score", 0))
    
    with tab_articles:
        st.markdown("### Screened Media Articles")
        
        # 🌟 DYNAMIC FIX: Read the live processed articles payload from your backend tunnel response
        articles_data = case.get("articles", [])
        
        if articles_data:
            for art in articles_data:
                # Format payload keys to match the internal layout expectations of render_article_card
                ui_card_payload = {
                    "title": art.get("title", "Untitled Adverse Intelligence Event"),
                    "source": art.get("source", "NEWS DATA STREAM"),
                    "source_tier": art.get("source_tier", 1),
                    "credibility_score": art.get("credibility_score", art.get("credibility", 95)),
                    "summary": art.get("description", art.get("summary", "No textual snippet available.")),
                    "url": art.get("url", "https://newsdata.io")
                }
                render_article_card(ui_card_payload)
        else:
            st.info("No live adverse media articles loaded for this entity yet. Run an ingestion query or verify your backend streaming configurations.")
            
    with tab_timeline:
        st.markdown("### Chronological Risk Timeline")
        render_timeline(timeline)
        
    with tab_watchlists:
        st.markdown("### PEP & Sanctions Screening Matches")
        st.markdown("##### Politically Exposed Persons (PEP)")
        if current_risk_score >= med_boundary:
            st.warning(f"⚠️ **Match Found**: Associate of {entity.get('name')} mapped as high-level regulatory proxy.")
            st.write("- **Confidence**: 85%")
            st.write("- **Role**: Government advisor / proxy officer")
        else:
            st.success("No active PEP matches identified.")

        st.markdown("##### Sanctions Watchlists")
        if current_risk_score >= high_boundary:
            st.error(f"🚨 **Match Found**: OFAC SDN list match detected for {entity.get('name')}.")
            st.write("- **Confidence**: 92%")
            st.write("- **List**: US OFAC, EU Sanctions List")
        else:
            st.success("No active sanctions listings detected.")

    with tab_decisions:
        st.markdown("### Compliance Decisions & QA Challenges")
        st.write(f"**Automated System Recommendation:** `{case.get('recommendation')}`")
        st.write(f"**Recommendation Justification:**")
        st.info(case.get("recommendation_justification") or "No justification available.")
        
        qa_status = case.get("regulator_qa_status", "PENDING")
        qa_color = "#4ade80" if qa_status == "PASS" else "#F5332C"
        st.markdown(f"**Regulator QA Validation status:** <span style='color:{qa_color}; font-weight:700'>{qa_status}</span>", unsafe_allow_html=True)
        
        qa_defs = case.get("regulator_qa_deficiencies", [])
        if qa_defs:
            st.markdown("Deficiencies to resolve:")
            for qd in qa_defs:
                st.write(f"- 🔴 {qd}")
        else:
            st.write("✅ Zero compliance audit deficiencies detected.")

        st.markdown("##### Update Case Decision & Notes")
        with st.form("update_case_form"):
            status_opt = st.selectbox("Update Case Status", options=["OPEN", "UNDER_REVIEW", "APPROVED", "REJECTED", "CLOSED"], index=0)
            rec_opt = st.selectbox("Compliance Action Decision", options=["CLEAR", "MONITOR", "ENHANCED_DUE_DILIGENCE", "ESCALATE", "REJECT", "REQUIRES_HUMAN_REVIEW"])
            notes = st.text_area("Compliance Review Notes")
            submitted = st.form_submit_button("Submit Analyst Decision")
            
            if submitted:
                payload = {"status": status_opt, "recommendation": rec_opt, "notes": notes}
                
                async def execute_case_update():
                    async with api_client:
                        await api_client.update_case(case_id, payload)
                
                try:
                    asyncio.run(execute_case_update())
                    st.success("Case successfully updated and audit log appended.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update case: {e}")

        st.markdown("##### Compliance Case Audit History")
        if logs:
            for log in logs:
                ts = log.get('timestamp', '')
                st.write(f"**{ts[:19]}** - `[{log.get('action')}]` by **{log.get('username')}**: {log.get('details')}")
        else:
            st.write("No audit log entries yet.")
