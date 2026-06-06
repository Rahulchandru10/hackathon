import streamlit as st

def render_article_card(article: dict):
    """
    Renders a glassmorphic article summary card with source credibility badge
    """
    tier = article.get("source_tier", 3)
    score = article.get("credibility_score", 70)
    
    # Credibility color coding
    cred_color = "#4ade80" # Light Green
    if score < 50:
        cred_color = "#F5332C" # Red
    elif score < 75:
        cred_color = "#facc15" # Yellow/Orange

    st.markdown(f"""
        <div style="
            background: rgba(18, 18, 17, 0.85);
            border-left: 4px solid #F5332C;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
            border-top: 1px solid rgba(204, 200, 185, 0.1);
            border-right: 1px solid rgba(204, 200, 185, 0.1);
            border-bottom: 1px solid rgba(204, 200, 185, 0.1);
            box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        ">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 6px;">
                <span style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; color: #CCC8B9; opacity: 0.7;">
                    {article.get('source')} (Tier {tier})
                </span>
                <span style="
                    font-size: 0.75rem; 
                    font-weight: 600; 
                    padding: 2px 8px; 
                    border-radius: 20px; 
                    background-color: rgba(204, 200, 185, 0.1);
                    color: {cred_color};
                ">
                    Credibility: {score}/100
                </span>
            </div>
            <a href="{article.get('url')}" target="_blank" style="
                font-size: 1.1rem; 
                font-weight: 600; 
                color: #F5332C; 
                text-decoration: none;
                margin-bottom: 8px;
                display: block;
            ">
                {article.get('title')}
            </a>
            <div style="font-size: 0.9rem; color: #CCC8B9; line-height: 1.4;">
                {article.get('summary', 'No snippet summary provided.')}
            </div>
        </div>
    """, unsafe_allow_html=True)
