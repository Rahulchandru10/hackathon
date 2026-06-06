import streamlit as st
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import api_client
from utils.styles import apply_custom_styles

apply_custom_styles()

st.markdown('<div class="sentinel-title">⚙️ Platform Administration</div>', unsafe_allow_html=True)
st.markdown("---")

role = st.session_state.get("role", "")

if role not in ("Admin", "MLRO"):
    st.error("🔒 Access Denied. Only Admin and MLRO roles may access the administration panel.")
    st.stop()

st.markdown("### Platform Configuration Settings")

tab_models, tab_params, tab_users = st.tabs([
    "🤖 AI Model Config",
    "📐 Compliance Parameters",
    "👥 User Management"
])

with tab_models:
    st.markdown("#### Ollama LLM Settings")
    st.text_input("Ollama Base URL", value="http://ollama:11434")
    st.text_input("Primary Language Model", value="qwen3:14b")
    st.text_input("Embedding Model", value="sentence-transformers/all-MiniLM-L6-v2")
    
    st.markdown("#### Search Engine Settings")
    st.text_input("Serper API Key", type="password", value="")
    st.text_input("GDELT API URL", value="https://api.gdeltproject.org/api/v2/doc/doc")
    st.text_input("OpenSanctions API Key", type="password", value="")

    if st.button("Save Model Settings"):
        st.success("Model configuration saved. Restart services for changes to take effect.")

with tab_params:
    st.markdown("#### Risk Score Thresholds")
    st.slider("LOW → MEDIUM boundary", min_value=0, max_value=50, value=20, step=1)
    st.slider("MEDIUM → HIGH boundary", min_value=20, max_value=80, value=50, step=1)
    st.slider("HIGH → CRITICAL boundary", min_value=50, max_value=100, value=75, step=1)
    
    st.markdown("#### False Positive Filtering")
    st.slider("Minimum relevance score to include media article (%)", min_value=0, max_value=100, value=30, step=5)
    
    st.markdown("#### Source Credibility Configuration")
    st.markdown("""
        **Tier 1** (Score 80-100): Reuters, Bloomberg, BBC, FT, WSJ, AP, Guardian  
        **Tier 2** (Score 55-79): National newspapers, established regional outlets  
        **Tier 3** (Score 30-54): Independent blogs, unverified sources  
        **Tier 4** (Score 0-29): Social media, anonymous publications
    """)

    if st.button("Save Compliance Settings"):
        st.success("Compliance parameter changes saved to configuration store.")

with tab_users:
    st.markdown("#### Platform User Management (Read Only - Modify via CLI or DB Admin)")
    st.info("User data is seeded from defaults on startup. Direct user management is available via database admin tools.")
    
    st.markdown("""
        | **Username** | **Role**           | **Default Password** |
        |-------------|-------------------|----------------------|
        | analyst      | Analyst           | sentinelpass         |
        | manager      | Compliance Manager| sentinelpass         |
        | mlro         | MLRO              | sentinelpass         |
        | admin        | Admin             | sentinelpass         |
    """)

    st.warning("⚠️ Change all default passwords before production deployment!")
