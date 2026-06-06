import streamlit as st

def render_kpi_card(value: str, label: str, icon: str = "📈"):
    """
    Renders a styled KPI numeric card inside Streamlit columns
    """
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(245, 51, 44, 0.12) 0%, rgba(18, 18, 17, 0.9) 100%);
            border: 1px solid rgba(245, 51, 44, 0.3);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        ">
            <div style="font-size: 2rem; margin-bottom: 8px;">{icon}</div>
            <div style="font-size: 2.2rem; font-weight: 700; color: #F5332C; line-height: 1;">
                {value}
            </div>
            <div style="font-size: 0.8rem; color: #CCC8B9; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-top: 6px;">
                {label}
            </div>
        </div>
    """, unsafe_allow_html=True)
