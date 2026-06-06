import streamlit as st
import asyncio
import sys
import os

# Make utils and components importable when running from the frontend directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.api_client import api_client
from utils.styles import apply_custom_styles

# Set page config
st.set_page_config(
    page_title="Project Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global styles
apply_custom_styles()

def show_login():
    st.markdown('<div class="sentinel-title">🛡️ Project Sentinel</div>', unsafe_allow_html=True)
    st.markdown('<h4>AI-Native Financial Crime Intelligence Platform</h4>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
            ### Platform Overview
            Welcome to the local-first, enterprise-grade Financial Crime Intelligence Platform.
            Log in with any of the seeded roles below for validation:
            - **analyst** (password: `sentinelpass`) - Case screening and copilot.
            - **manager** (password: `sentinelpass`) - Case assignment and QA.
            - **mlro** (password: `sentinelpass`) - Sign-off and decisions.
            - **admin** (password: `sentinelpass`) - Full settings configuration.
        """)

    with col2:
        with st.form("login_form"):
            st.subheader("Compliance Staff Portal")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")
            
            if submitted:
                success = asyncio.run(api_client.login(username, password))
                if success:
                    st.success(f"Logged in as {username.capitalize()} ({api_client.role})!")
                    st.session_state.username = username
                    st.session_state.role = api_client.role
                    st.session_state.token = api_client.token
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please verify your entries.")

def main():
    # Session state initialization
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "token" not in st.session_state:
        st.session_state.token = None
    if "selected_case_id" not in st.session_state:
        st.session_state.selected_case_id = None

    if not st.session_state.token:
        show_login()
    else:
        api_client.set_token(st.session_state.token, st.session_state.role, st.session_state.username)
        
        st.sidebar.markdown(f"### Current User: **{st.session_state.username.upper()}**")
        st.sidebar.markdown(f"Role: `{st.session_state.role}`")
        
        if st.sidebar.button("Sign Out"):
            api_client.clear_auth()
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.token = None
            st.rerun()
            
        st.sidebar.markdown("---")
        
        st.markdown('<div class="sentinel-title">🛡️ Project Sentinel</div>', unsafe_allow_html=True)
        st.markdown('<h4>AI-Native Financial Crime Intelligence Platform</h4>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("""
            Select pages on the sidebar to proceed:
            1. **Dashboard** — Monitor case queues, open alerts and platform KPI metrics.
            2. **Screening** — Launch real-time adverse media, PEP, and sanctions screening.
            3. **Results** — Audit case risk scores, event timelines, and extracted media.
            4. **Network Graph** — Explore Neo4j interactive entity relationships and corporate networks.
            5. **Investigation Copilot** — Chat interactively with the RAG-backed case investigator.
            6. **Reports** — Generate and download official PDF compliance summaries.
            7. **Monitoring** — Manage periodic subscription configurations and system alerts.
            8. **Administration** — Configure server instances, models, and compliance parameters.
        """)

if __name__ == "__main__":
    main()
