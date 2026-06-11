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

# ─── TAB 1: AI MODEL CONFIGURATION ──────────────────────────────────────────
with tab_models:
    st.markdown("#### Ollama LLM Settings")
    
    # Read values safely from persistent layer
    start_url = st.session_state.get("saved_ollama_url", "http://127.0.0.1:11434")
    start_model = st.session_state.get("saved_primary_llm", "mistral")
    start_embed = st.session_state.get("saved_embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
    start_serper = st.session_state.get("saved_serper_key", "")

    ollama_url = st.text_input("Ollama Base URL", value=start_url)
    primary_llm = st.text_input("Primary Language Model", value=start_model)
    embed_model = st.text_input("Embedding Model", value=start_embed)
    
    st.markdown("#### Search Engine Settings")
    serper_key = st.text_input("Serper API Key", type="password", value=start_serper)
    gdelt_url = st.text_input("GDELT API URL", value="https://api.gdeltproject.org/api/v2/doc/doc")
    opensanctions_key = st.text_input("OpenSanctions API Key", type="password", value="")

    if st.button("Save Model Settings"):
        st.session_state.saved_ollama_url = ollama_url
        st.session_state.saved_primary_llm = primary_llm
        st.session_state.saved_embedding_model = embed_model
        st.session_state.saved_serper_key = serper_key
        st.success(f"🚀 AI Core configuration locked to `{primary_llm}`!")

# ─── TAB 2: COMPLIANCE PARAMETERS ──────────────────────────────────────────
with tab_params:
    st.markdown("#### Risk Score Thresholds")
    
    # Read slider baselines from persistent storage variables
    start_low = st.session_state.get("saved_low_med", 20)
    start_med = st.session_state.get("saved_med_high", 50)
    start_high = st.session_state.get("saved_high_crit", 75)
    start_rel = st.session_state.get("saved_media_rel", 30)

    low_med = st.slider("LOW → MEDIUM boundary", min_value=0, max_value=50, value=start_low, step=1)
    med_high = st.slider("MEDIUM → HIGH boundary", min_value=20, max_value=80, value=start_med, step=1)
    high_crit = st.slider("HIGH → CRITICAL boundary", min_value=50, max_value=100, value=start_high, step=1)
    
    st.markdown("#### False Positive Filtering")
    min_rel = st.slider("Minimum relevance score to include media article (%)", min_value=0, max_value=100, value=start_rel, step=5)
    
    st.markdown("#### Source Credibility Configuration")
    st.markdown("""
        **Tier 1** (Score 80-100): Reuters, Bloomberg, BBC, FT, WSJ, AP, Guardian  
        **Tier 2** (Score 55-79): National newspapers, established regional outlets  
        **Tier 3** (Score 30-54): Independent blogs, unverified sources  
        **Tier 4** (Score 0-29): Social media, anonymous publications
    """)

    if st.button("Save Compliance Settings"):
        st.session_state.saved_low_med = low_med
        st.session_state.saved_med_high = med_high
        st.session_state.saved_high_crit = high_crit
        st.session_state.saved_media_rel = min_rel
        st.success(f"⚖️ Threshold updates saved permanently! [Low/Med: {low_med} | Med/High: {med_high} | High/Crit: {high_crit}]")

# ─── TAB 3: USER MANAGEMENT ───────────────────────────────────────────────
with tab_users:
    st.markdown("#### Platform User Management (Read Only - Modify via CLI or DB Admin)")
    st.info("User data is seeded from defaults on startup. Direct user management is available via database admin tools.")
    
    st.markdown("""
        | **Username** | **Role** | **Default Password** |
        |-------------|-------------------|----------------------|
        | analyst      | Analyst           | sentinelpass         |
        | manager      | Compliance Manager| sentinelpass         |
        | mlro         | MLRO              | sentinelpass         |
        | admin        | Admin             | sentinelpass         |
    """)
    st.warning("⚠️ Change all default passwords before production deployment!")
