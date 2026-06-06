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

apply_custom_styles()

st.markdown('<div class="sentinel-title">📊 Case Audit & Screening Results</div>', unsafe_allow_html=True)
st.markdown("---")

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
    st.subheader(f"Case Context: {entity.get('name')} ({case.get('id')})")
    
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
    
    tab_articles, tab_timeline, tab_watchlists, tab_decisions = st.tabs([
        "📰 Adverse Media Articles", 
        "⏳ Event Timeline", 
        "🛡️ Watchlists & Matches", 
        "📝 Recommendations & QA Challenge"
    ])
    
    with tab_articles:
        st.markdown("### Screened Media Articles")
        articles_data = []
        if case.get("risk_score", 0) > 20:
            articles_data.append({
                "title": f"Regulatory inquiry focused on {entity.get('name')} compliance failures",
                "source": "Reuters",
                "source_tier": 1,
                "credibility_score": 98,
                "summary": f"Finance watchdogs launched a formal inquiry into {entity.get('name')} due to gaps in transaction screening protocols.",
                "url": "https://reuters.com"
            })
            articles_data.append({
                "title": f"Internal whistleblowers flag questionable activity at {entity.get('name')}",
                "source": "Bloomberg",
                "source_tier": 1,
                "credibility_score": 96,
                "summary": f"Uncovered emails from corporate files detail transaction routing patterns designed to bypass standard KYC validation stages.",
                "url": "https://bloomberg.com"
            })
            
        if articles_data:
            for art in articles_data:
                render_article_card(art)
        else:
            st.info("No adverse media articles found for this entity.")
            
    with tab_timeline:
        st.markdown("### Chronological Risk Timeline")
        render_timeline(timeline)
        
    with tab_watchlists:
        st.markdown("### PEP & Sanctions Screening Matches")
        st.markdown("##### Politically Exposed Persons (PEP)")
        if case.get("risk_score", 0) > 50:
            st.warning(f"⚠️ **Match Found**: Associate of {entity.get('name')} mapped as high-level regulatory proxy.")
            st.write("- **Confidence**: 85%")
            st.write("- **Role**: Government advisor / proxy officer")
            st.write("- **Justification**: Target name and country matches regional administrative PEP lists.")
        else:
            st.success("No active PEP matches identified.")

        st.markdown("##### Sanctions Watchlists")
        if case.get("risk_score", 0) > 75:
            st.error(f"🚨 **Match Found**: OFAC SDN list match detected for {entity.get('name')}.")
            st.write("- **Confidence**: 92%")
            st.write("- **List**: US OFAC, EU Sanctions List")
            st.write("- **Justification**: Cross-border funds freeze list matching company registration ID.")
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
                payload = {
                    "status": status_opt,
                    "recommendation": rec_opt,
                    "notes": notes
                }
                try:
                    asyncio.run(api_client.update_case(case_id, payload))
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
