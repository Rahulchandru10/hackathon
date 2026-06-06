import streamlit as st
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_client import api_client
from utils.styles import apply_custom_styles

apply_custom_styles()

st.markdown('<div class="sentinel-title">📁 Reports Generation & PDF Exports</div>', unsafe_allow_html=True)
st.markdown("---")

case_id = st.session_state.get("selected_case_id")

if not case_id:
    st.info("No active case context. Please select a case from the Dashboard or run a new Screening query.")
else:
    st.subheader(f"Generate Compliance Report for: {case_id}")
    st.markdown("""
        The generated PDF contains the following standard examiner sections:
        1. Executive Summary
        2. Entity Profile
        3. Adverse Media Findings
        4. PEP Findings
        5. Sanctions Findings
        6. Timeline
        7. Network Analysis
        8. Risk Scoring
        9. Recommendations
        10. Evidence Appendix
        11. Audit Trail
    """)

    async def get_report_bytes():
        pdf = await api_client.get_report_pdf(case_id)
        return pdf

    if st.button("Compile & Generate Official PDF Report"):
        with st.spinner("Compiling ReportLab layout sheets and signatures..."):
            try:
                pdf_data = asyncio.run(get_report_bytes())
                st.success("Report successfully compiled!")
                st.download_button(
                    label="Download Report PDF",
                    data=pdf_data,
                    file_name=f"ProjectSentinel_Report_{case_id}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Failed to generate report PDF: {e}")
