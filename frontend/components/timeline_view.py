import streamlit as st
from typing import List, Dict, Any

def render_timeline(events: List[Dict[str, Any]]):
    """
    Renders a clean vertical markdown/HTML timeline list for adverse media events
    """
    if not events:
        st.info("No timeline events to display.")
        return

    st.markdown("""
        <style>
        .timeline-container {
            border-left: 3px solid #F5332C;
            padding-left: 20px;
            margin-left: 10px;
            position: relative;
        }
        .timeline-item {
            margin-bottom: 25px;
            position: relative;
        }
        .timeline-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #F5332C;
            position: absolute;
            left: -28px;
            top: 4px;
            border: 2px solid #000000;
        }
        .timeline-date {
            font-weight: 700;
            color: #F5332C;
            font-size: 0.9rem;
            margin-bottom: 4px;
        }
        .timeline-title {
            font-weight: 600;
            font-size: 1.1rem;
            color: #CCC8B9;
            margin-bottom: 6px;
        }
        .timeline-desc {
            font-size: 0.95rem;
            color: #CCC8B9;
            line-height: 1.4;
            opacity: 0.9;
        }
        .severity-badge {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            float: right;
        }
    """, unsafe_allow_html=True)

    st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
    
    for ev in events:
        sev = ev.get("severity", 50)
        sev_color = "background-color: rgba(74, 222, 128, 0.15); color: #4ade80;"
        if sev > 75:
            sev_color = "background-color: rgba(245, 51, 44, 0.25); color: #fca5a5;"
        elif sev > 50:
            sev_color = "background-color: rgba(250, 204, 21, 0.15); color: #facc15;"
        elif sev > 20:
            sev_color = "background-color: rgba(250, 204, 21, 0.15); color: #facc15;"
            
        st.markdown(f"""
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div class="timeline-date">{ev.get('date', 'N/A')}</div>
                <div class="timeline-title">
                    {ev.get('event_type')}
                    <span class="severity-badge" style="{sev_color}">Severity {sev}/100</span>
                </div>
                <div class="timeline-desc">{ev.get('description')}</div>
                <div style="font-size: 0.8rem; color: #CCC8B9; opacity: 0.7; margin-top: 4px;">
                    Involved: {", ".join(ev.get('entities_involved', []))} | Location: {ev.get('location', 'Global')}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
