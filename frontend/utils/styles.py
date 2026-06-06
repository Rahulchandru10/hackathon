import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"]  {
            font-family: 'Outfit', sans-serif;
        }

        /* Title styling */
        .sentinel-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #F5332C 0%, #CCC8B9 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        /* Glassmorphic Cards */
        .glass-card {
            background: rgba(18, 18, 17, 0.75);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            border: 1px solid rgba(204, 200, 185, 0.15);
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        }

        .metric-card {
            background: linear-gradient(135deg, rgba(245, 51, 44, 0.1) 0%, rgba(0, 0, 0, 0.6) 100%);
            border: 1px solid rgba(245, 51, 44, 0.3);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #F5332C;
        }

        .metric-label {
            font-size: 0.85rem;
            color: #CCC8B9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Badge Pills */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 50px;
            text-align: center;
        }

        .badge-low { background-color: #0d2818; color: #4ade80; border: 1px solid #166534; }
        .badge-medium { background-color: #2b1b04; color: #facc15; border: 1px solid #78350f; }
        .badge-high { background-color: #3b0712; color: #f87171; border: 1px solid #991b1b; }
        .badge-critical { background-color: #4c0519; color: #fca5a5; border: 1px solid #e11d48; }

        /* Custom buttons styling */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #F5332C 0%, #000000 100%);
            color: #CCC8B9;
            border: 1px solid rgba(204, 200, 185, 0.3);
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px);
            color: white;
            border: 1px solid #F5332C;
            box-shadow: 0 4px 15px rgba(245, 51, 44, 0.5);
        }
        </style>
    """, unsafe_allow_html=True)
