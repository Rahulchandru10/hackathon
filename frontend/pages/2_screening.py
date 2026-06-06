import streamlit as st
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import api_client
from utils.styles import apply_custom_styles

apply_custom_styles()

st.markdown('<div class="sentinel-title">🔍 Screening & Onboarding Intake</div>', unsafe_allow_html=True)
st.markdown("---")

st.markdown("### Entity Intake Details")
st.caption("Provide entity details to launch Project Sentinel's adverse media and sanctions intelligence graph.")

with st.form("screening_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Basic Identifiers")
        name = st.text_input("Entity Name *", placeholder="Enter legal name or person full name")
        entity_type = st.selectbox("Entity Type", options=["Company", "Individual", "Unknown"])
        country = st.text_input("Country", placeholder="E.g., Germany, Russia, United States")
        industry = st.text_input("Industry", placeholder="E.g., Financial Services, Mining, Logistics")
        website = st.text_input("Website URL", placeholder="E.g., https://example.com")
        reg_number = st.text_input("Registration / Tax Number", placeholder="E.g., HRB 12345")
        
    with col2:
        st.markdown("##### Relationship & Network Context (Comma Separated)")
        aliases_str = st.text_input("Aliases", placeholder="Alias A, Alias B")
        parent_company = st.text_input("Parent Company", placeholder="Parent organization name")
        subsidiaries_str = st.text_area("Subsidiaries", placeholder="Sub A, Sub B", height=50)
        directors_str = st.text_area("Directors", placeholder="Director A, Director B", height=50)
        shareholders_str = st.text_area("Shareholders", placeholder="Shareholder A, Shareholder B", height=50)
        ubos_str = st.text_area("Beneficial Owners (UBOs)", placeholder="UBO A, UBO B", height=50)

    st.markdown("##### Monitoring Parameters")
    frequency = st.selectbox("Continuous Monitoring Subscription Frequency", options=["One-time", "Daily", "Weekly"])

    submitted = st.form_submit_button("Initiate Intelligence Screening")
    
    if submitted:
        if not name or not name.strip():
            st.error("Entity Name is a required field.")
        else:
            entity_data = {
                "name": name.strip(),
                "entity_type": entity_type,
                "country": country.strip() if country else None,
                "industry": industry.strip() if industry else None,
                "website": website.strip() if website else None,
                "registration_number": reg_number.strip() if reg_number else None,
                "aliases": [x.strip() for x in aliases_str.split(",") if x.strip()] if aliases_str else [],
                "parent_company": parent_company.strip() if parent_company else None,
                "subsidiaries": [x.strip() for x in subsidiaries_str.split(",") if x.strip()] if subsidiaries_str else [],
                "directors": [x.strip() for x in directors_str.split(",") if x.strip()] if directors_str else [],
                "shareholders": [x.strip() for x in shareholders_str.split(",") if x.strip()] if shareholders_str else [],
                "beneficial_owners": [x.strip() for x in ubos_str.split(",") if x.strip()] if ubos_str else []
            }
            
            with st.spinner("Executing 18-agent LangGraph workflow. Collecting adverse media and evaluating risk..."):
                try:
                    result = asyncio.run(api_client.screen_entity(entity_data, frequency))
                    
                    st.success("Screening successfully completed!")
                    st.session_state.selected_case_id = result["case_id"]
                    
                    st.markdown(f"**Case Assigned ID:** `{result['case_id']}`")
                    st.markdown(f"**Risk Score:** `{result['risk_score']}/100`")
                    st.markdown(f"**Recommendation:** `{result['recommendation']}`")
                    
                    if result.get("warnings"):
                        for warn in result["warnings"]:
                            st.warning(warn)
                            
                    st.info("Navigate to the Results tab to view timeline events and adverse articles.")
                except Exception as e:
                    st.error(f"Screening execution failed: {e}")
