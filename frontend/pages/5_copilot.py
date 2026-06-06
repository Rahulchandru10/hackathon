import streamlit as st
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import api_client
from utils.styles import apply_custom_styles

apply_custom_styles()

st.markdown('<div class="sentinel-title">💬 AI Investigation Copilot</div>', unsafe_allow_html=True)
st.markdown("---")

case_id = st.session_state.get("selected_case_id")

if not case_id:
    st.info("No active case context. Please select a case from the Dashboard or run a new Screening query.")
else:
    st.subheader(f"Investigating Case: {case_id}")
    st.markdown("Ask the copilot questions about the entity, fraud events, sanctions links, and score factors.")
    
    # Initialize message history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask: 'Why is the risk high for this company?'"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("AI Copilot analyzing case findings & vector indexes..."):
            try:
                answer = asyncio.run(api_client.copilot_chat(case_id, prompt))
                with st.chat_message("assistant"):
                    st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Failed to fetch response from Copilot: {e}")
