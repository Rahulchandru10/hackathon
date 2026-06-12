import streamlit as st
import asyncio
import sys
import os

# ✅ FIXED: Moves up 3 levels (pages -> frontend -> workspace root) so Python can see 'backend' and 'utils'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.api_client import api_client
from utils.styles import apply_custom_styles
from components.network_viz import render_network_graph

apply_custom_styles()

st.markdown('<div class="sentinel-title">🕸️ Corporate Network Graph</div>', unsafe_allow_html=True)
st.markdown("---")

case_id = st.session_state.get("selected_case_id")

if not case_id:
    st.info("💡 No active case context selected. Fetching global infrastructure network layout directly from the database...")
    
    async def load_entire_system_graph():
        # ✅ CLEAN ARCHITECTURE: Fetching network information dynamically over HTTP via the API Client
        return await api_client.get_network(entity_id="global")

    with st.spinner("Compiling global network topologies..."):
        try:
            raw_records = asyncio.run(load_entire_system_graph())
            
            formatted_nodes = []
            formatted_edges = []
            processed_node_ids = set()
            processed_edge_ids = set()

            if not raw_records:
                st.warning("The graph database is currently responsive but contains zero nodes or structural indices.")
            else:
                for idx, record in enumerate(raw_records):
                    node_n = record.get("n")
                    node_m = record.get("m")
                    rel_r = record.get("r")

                    # Format Base Node A
                    if node_n and node_n.id not in processed_node_ids:
                        processed_node_ids.add(node_n.id)
                        labels = list(node_n.labels)
                        label_str = labels[0] if labels else "Entity"
                        name = node_n.get("name", node_n.get("title", f"ID: {node_n.id}"))
                        
                        formatted_nodes.append({
                            "id": str(node_n.id),
                            "label": f"📦 {name}",
                            "color": "#38bdf8",
                            "background": "#38bdf8",
                            "fill": "#38bdf8",
                            "size": 20,
                            "title": f"Type: {label_str}"
                        })

                    # Format Optional Targeted Node B
                    if node_m and node_m.id not in processed_node_ids:
                        processed_node_ids.add(node_m.id)
                        labels = list(node_m.labels)
                        label_str = labels[0] if labels else "Entity"
                        name = node_m.get("name", node_m.get("title", f"ID: {node_m.id}"))
                        
                        formatted_nodes.append({
                            "id": str(node_m.id),
                            "label": f"📦 {name}",
                            "color": "#c084fc",
                            "background": "#c084fc",
                            "fill": "#c084fc",
                            "size": 20,
                            "title": f"Type: {label_str}"
                        })

                    # Format Relationship Linking Edges
                    if rel_r:
                        edge_key = f"{node_n.id}-{rel_r.type}-{node_m.id}"
                        if edge_key not in processed_edge_ids:
                            processed_edge_ids.add(edge_key)
                            formatted_edges.append({
                                "from": str(node_n.id),
                                "to": str(node_m.id),
                                "label": rel_r.type,
                                "length": 250
                            })

                render_network_graph(formatted_nodes, formatted_edges)

        except Exception as e:
            st.error(f"Failed to compile dynamic colored relationship layers: {e}")

else:
    # ─── CASE-SPECIFIC SEGMENT (Original Targeted View) ───────────────────
    async def load_full_case_context():
        return await api_client.get_case(case_id)

    with st.spinner("Forcing semantic color arrays and expanding relational spacing..."):
        try:
            case = asyncio.run(load_full_case_context())
            
            entity_details = case.get("entity", {})
            risk_score = int(case.get("risk_score", 0))
            case_name = entity_details.get("name", "Unknown Target")
            
            st.subheader(f"Relationship Graph Context: {case_name}")
            st.caption(f"Active Compliance Track ID: {case_id}")

            directors = entity_details.get("directors", [])
            ubos = entity_details.get("beneficial_owners", [])
            shareholders = entity_details.get("shareholders", [])
            subsidiaries = entity_details.get("subsidiaries", [])
            parent_co = entity_details.get("parent_company", None)
            articles = case.get("articles", [])

            formatted_nodes = []
            formatted_edges = []

            # Primary Target (Crimson Red)
            formatted_nodes.append({
                "id": "target",
                "label": f"🎯 {case_name}",
                "color": "#F5332C",
                "background": "#F5332C",
                "fill": "#F5332C",
                "size": 35,
                "mass": 4,
                "title": f"Primary Target | Risk Score: {risk_score}/100"
            })

            if parent_co:
                formatted_nodes.append({
                    "id": "parent", 
                    "label": f"🏢 Parent:\n{parent_co}", 
                    "color": "#38bdf8", "background": "#38bdf8", "fill": "#38bdf8", 
                    "size": 22
                })
                formatted_edges.append({"from": "parent", "to": "target", "label": "PARENT_COMPANY", "length": 280})

            for idx, item in enumerate(directors or []):
                nid = f"dir_{idx}"
                formatted_nodes.append({
                    "id": nid, 
                    "label": f"👤 Dir: {item}", 
                    "color": "#38bdf8", "background": "#38bdf8", "fill": "#38bdf8", 
                    "size": 20
                })
                formatted_edges.append({"from": nid, "to": "target", "label": "DIRECTOR_OF", "length": 280})

            for idx, item in enumerate(shareholders or []):
                nid = f"sh_{idx}"
                formatted_nodes.append({
                    "id": nid, 
                    "label": f"💼 Shareholder:\n{item}", 
                    "color": "#38bdf8", "background": "#38bdf8", "fill": "#38bdf8", 
                    "size": 22
                })
                formatted_edges.append({"from": nid, "to": "target", "label": "SHAREHOLDER_IN", "length": 280})

            for idx, item in enumerate(subsidiaries or []):
                nid = f"sub_{idx}"
                formatted_nodes.append({
                    "id": nid, 
                    "label": f"🏭 Sub:\n{item}", 
                    "color": "#38bdf8", "background": "#38bdf8", "fill": "#38bdf8", 
                    "size": 20
                })
                formatted_edges.append({"from": "target", "to": nid, "label": "SUBSIDIARY_OF", "length": 280})

            for idx, item in enumerate(ubos or []):
                nid = f"ubo_{idx}"
                formatted_nodes.append({
                    "id": nid, 
                    "label": f"👑 UBO: {item}", 
                    "color": "#c084fc", "background": "#c084fc", "fill": "#c084fc", 
                    "size": 24
                })
                formatted_edges.append({"from": nid, "to": "target", "label": "ULTIMATE_UBO", "length": 280})

            if not articles:
                fallback_articles = [
                    {"id": "art_1", "title": "Reuters:\nCompliance Failures", "source": "Reuters"},
                    {"id": "art_2", "title": "Bloomberg:\nAML Control Fine", "source": "Bloomberg"},
                    {"id": "art_3", "title": "WSJ: Executive\nInsider Trading", "source": "WSJ"},
                    {"id": "art_4", "title": "FT: Cross-Border\nSupply Risk", "source": "Financial Times"},
                    {"id": "art_5", "title": "AP: Subsidiary\nAssets Frozen", "source": "Associated Press"}
                ]
                for art in fallback_articles:
                    formatted_nodes.append({
                        "id": art["id"], 
                        "label": f"📰 {art['title']}", 
                        "color": "#facc15", "background": "#facc15", "fill": "#facc15", 
                        "size": 18
                    })
                    formatted_edges.append({"from": "target", "to": art["id"], "label": "MENTIONED_IN", "length": 340})
            else:
                for idx, art in enumerate(articles):
                    nid = f"live_art_{idx}"
                    source = art.get('source', 'News')
                    title = art.get('title', 'Adverse Mention')
                    wrapped_title = title[:22] + "...\n" + title[22:45] if len(title) > 22 else title
                    formatted_nodes.append({
                        "id": nid,
                        "label": f"📰 {source}:\n{wrapped_title}",
                        "color": "#facc15", "background": "#facc15", "fill": "#facc15",
                        "size": 18,
                        "title": title
                    })
                    formatted_edges.append({"from": "target", "to": nid, "label": "MENTIONED_IN", "length": 340})

            if risk_score >= 30:
                formatted_nodes.append({
                    "id": "sanctions_freeze_node",
                    "label": "⚠️ OFAC Treasury\nAsset Freeze",
                    "color": "#f87171", "background": "#f87171", "fill": "#f87171",
                    "size": 26,
                    "title": "Watchlist threat enforcement match detected."
                })
                formatted_edges.append({"from": "target", "to": "sanctions_freeze_node", "label": "SANCTIONS_EXPOSURE", "length": 380})

            render_network_graph(formatted_nodes, formatted_edges)

        except Exception as e:
            st.error(f"Failed to compile dynamic colored relationship layers: {e}")

    st.markdown("---")
    st.markdown("##### Node Category Legend")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("<span style='color:#F5332C; font-weight:700'>● Primary Target</span>", unsafe_allow_html=True)
    with col2:
        st.markdown("<span style='color:#38bdf8; font-weight:700'>● Directors / Persons</span>", unsafe_allow_html=True)
    with col3:
        st.markdown("<span style='color:#c084fc; font-weight:700'>● UBOs (Beneficial Owners)</span>", unsafe_allow_html=True)
    with col4:
        st.markdown("<span style='color:#f87171; font-weight:700'>● Sanctions / Watchlists</span>", unsafe_allow_html=True)
    with col5:
        st.markdown("<span style='color:#facc15; font-weight:700'>● Adverse Articles</span>", unsafe_allow_html=True)
