import logging
import uuid
import datetime
from langgraph.graph import StateGraph, END
from backend.workflow.state import ScreeningState
from backend.workflow.nodes import (
    node_intake, node_resolution, node_search_query, node_media_collection,
    node_duplicate_detection, node_source_credibility, node_event_extraction,
    node_false_positive, node_timeline, node_network_intelligence,
    node_pep_screening, node_sanctions_screening, node_risk_scoring,
    node_recommendation, node_explainability, node_regulator_qa, node_monitoring
)
from backend.models.entity import EntityIntake
from backend.services.databases.postgres import AsyncSessionLocal, DBCase, DBArticle, DBEvent
from backend.services.databases.qdrant import qdrant_client
from backend.services.embeddings import embedding_service

logger = logging.getLogger(__name__)

def build_workflow_graph():
    # Initialize the graph
    workflow = StateGraph(ScreeningState)

    # Add nodes
    workflow.add_node("intake", node_intake)
    workflow.add_node("resolution", node_resolution)
    workflow.add_node("search_query", node_search_query)
    workflow.add_node("media_collection", node_media_collection)
    workflow.add_node("duplicate_detection", node_duplicate_detection)
    workflow.add_node("source_credibility", node_source_credibility)
    workflow.add_node("event_extraction", node_event_extraction)
    workflow.add_node("false_positive", node_false_positive)
    workflow.add_node("timeline_generation", node_timeline)
    workflow.add_node("network_intelligence", node_network_intelligence)
    workflow.add_node("pep_screening", node_pep_screening)
    workflow.add_node("sanctions_screening", node_sanctions_screening)
    workflow.add_node("risk_scoring", node_risk_scoring)
    workflow.add_node("recommendation_generation", node_recommendation)
    workflow.add_node("explainability", node_explainability)
    workflow.add_node("regulator_qa", node_regulator_qa)
    workflow.add_node("monitoring", node_monitoring)

    # Set Entry Point
    workflow.set_entry_point("intake")

    # Define linear execution flow
    workflow.add_edge("intake", "resolution")
    workflow.add_edge("resolution", "search_query")
    workflow.add_edge("search_query", "media_collection")
    workflow.add_edge("media_collection", "duplicate_detection")
    workflow.add_edge("duplicate_detection", "source_credibility")
    workflow.add_edge("source_credibility", "event_extraction")
    workflow.add_edge("event_extraction", "false_positive")
    workflow.add_edge("false_positive", "timeline_generation")
    workflow.add_edge("timeline_generation", "network_intelligence")
    workflow.add_edge("network_intelligence", "pep_screening")
    workflow.add_edge("pep_screening", "sanctions_screening")
    workflow.add_edge("sanctions_screening", "risk_scoring")
    workflow.add_edge("risk_scoring", "recommendation_generation")
    workflow.add_edge("recommendation_generation", "explainability")
    workflow.add_edge("explainability", "regulator_qa")
    workflow.add_edge("regulator_qa", "monitoring")
    workflow.add_edge("monitoring", END)

    # Compile the graph
    return workflow.compile()

compiled_graph = build_workflow_graph()

async def run_screening_workflow(entity: EntityIntake, monitoring_frequency: str = "One-time") -> dict:
    case_id = f"case-{uuid.uuid4().hex[:12]}"
    
    # Define initial state
    initial_state: ScreeningState = {
        "entity_input": entity,
        "monitoring_frequency": monitoring_frequency,
        "case_id": case_id,
        "warnings": [],
        "errors": [],
        "resolved_entity": {},
        "search_queries": [],
        "raw_articles": [],
        "deduplicated_articles": [],
        "validated_articles": [],
        "extracted_events": [],
        "filtered_events": [],
        "timeline": [],
        "pep_matches": [],
        "sanctions_matches": [],
        "network_nodes": [],
        "network_edges": [],
        "risk_breakdown": {},
        "risk_score": 0,
        "recommendation": "",
        "recommendation_justification": "",
        "explainability_report": "",
        "regulator_qa_status": "PENDING",
        "regulator_qa_deficiencies": [],
        "is_delta_detected": False,
        "delta_details": []
    }

    logger.info(f"Starting Project Sentinel screening graph for case: {case_id}")
    final_state = await compiled_graph.ainvoke(initial_state, config={"recursion_limit": 50})
    logger.info(f"Screening graph completed for case: {case_id}")

    # Normalize articles in final_state["validated_articles"] to prevent Pydantic validation errors
    import dateutil.parser
    for art in final_state["validated_articles"]:
        # 1. Assign ID if missing
        if not art.get("id"):
            art["id"] = f"art-{uuid.uuid4().hex[:12]}"
        
        # 2. Parse publish_date into datetime or fallback
        p_date = art.get("publish_date")
        if p_date:
            if isinstance(p_date, str):
                try:
                    art["publish_date"] = dateutil.parser.parse(p_date)
                except Exception:
                    art["publish_date"] = datetime.datetime.utcnow()
            elif not isinstance(p_date, datetime.datetime):
                art["publish_date"] = datetime.datetime.utcnow()
        else:
            art["publish_date"] = datetime.datetime.utcnow()

    # ─── Persist to PostgreSQL ───
    async with AsyncSessionLocal() as session:
        try:
            # Create Case record
            db_case = DBCase(
                id=case_id,
                entity_name=entity.name,
                entity_type=final_state["resolved_entity"].get("entity_type", "Unknown"),
                country=final_state["resolved_entity"].get("country"),
                industry=final_state["resolved_entity"].get("industry"),
                website=final_state["resolved_entity"].get("website"),
                registration_number=final_state["resolved_entity"].get("registration_number"),
                aliases=final_state["resolved_entity"].get("aliases", []),
                parent_company=final_state["resolved_entity"].get("parent_company"),
                subsidiaries=final_state["resolved_entity"].get("subsidiaries", []),
                directors=final_state["resolved_entity"].get("directors", []),
                shareholders=final_state["resolved_entity"].get("shareholders", []),
                beneficial_owners=final_state["resolved_entity"].get("beneficial_owners", []),
                status="OPEN",
                risk_score=final_state["risk_score"],
                risk_breakdown=final_state["risk_breakdown"],
                recommendation=final_state["recommendation"],
                recommendation_justification=final_state["recommendation_justification"],
                regulator_qa_status=final_state["regulator_qa_status"],
                regulator_qa_deficiencies=final_state["regulator_qa_deficiencies"],
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            session.add(db_case)

            # Create Articles records
            articles_to_save = []
            for art in final_state["validated_articles"]:
                db_art = DBArticle(
                    id=art["id"],
                    case_id=case_id,
                    title=art.get("title", "Adverse Article"),
                    url=art.get("url", ""),
                    source=art.get("source", "Web"),
                    source_tier=art.get("source_tier", 3),
                    credibility_score=art.get("credibility_score", 70),
                    publish_date=art["publish_date"],
                    summary=art.get("snippet", ""),
                    content=art.get("content", ""),
                    language=art.get("language", "en"),
                    cluster_id=art.get("cluster_id")
                )
                session.add(db_art)
                articles_to_save.append(db_art)

            # Create Event records
            for ev in final_state["filtered_events"]:
                db_ev = DBEvent(
                    id=ev.get("id") or f"ev-{uuid.uuid4().hex[:12]}",
                    case_id=case_id,
                    article_id=ev.get("article_id"),
                    event_type=ev.get("event_type", "General"),
                    severity=ev.get("severity", 50),
                    description=ev.get("description", ""),
                    detected_date=ev.get("detected_date", ""),
                    location=ev.get("location", ""),
                    entities_involved=ev.get("entities_involved", [])
                )
                session.add(db_ev)

            await session.commit()
            logger.info(f"Case data saved to Postgres for case: {case_id}")
        except Exception as e:
            logger.error(f"Error persisting case to PostgreSQL: {e}")
            await session.rollback()

    # ─── Persist to Qdrant (RAG Vector Store) ───
    # Initialize case_findings collection with dimension of 384 (all-MiniLM-L6-v2 default)
    try:
        qdrant_client.create_collection_if_not_exists("case_findings", vector_size=384)
        
        # We index article snippets and final recommendations for copilot queries
        points_ids = []
        vectors = []
        payloads = []
        
        for art in final_state["validated_articles"]:
            text = f"Title: {art.get('title')}\nSnippet: {art.get('snippet')}\nSource: {art.get('source')}"
            vec = embedding_service.get_embedding(text)
            
            p_id = str(uuid.uuid4())
            points_ids.append(p_id)
            vectors.append(vec)
            payloads.append({
                "case_id": case_id,
                "title": art.get("title"),
                "text": text,
                "type": "adverse_media"
            })

        # Also index the final explainability report
        report_text = final_state["explainability_report"]
        if report_text:
            vec = embedding_service.get_embedding(report_text)
            p_id = str(uuid.uuid4())
            points_ids.append(p_id)
            vectors.append(vec)
            payloads.append({
                "case_id": case_id,
                "title": "Final Explainability Report",
                "text": report_text,
                "type": "explainability"
            })

        if points_ids:
            qdrant_client.upsert_vectors("case_findings", points_ids, vectors, payloads)
            logger.info(f"Indexed case findings to Qdrant for case: {case_id}")
    except Exception as e:
        logger.error(f"Failed to populate Qdrant vector store: {e}")

    return {
        "case_id": case_id,
        "entity": {
            "id": case_id,
            **final_state["resolved_entity"]
        },
        "warnings": final_state["warnings"],
        "risk_score": final_state["risk_score"],
        "risk_breakdown": final_state["risk_breakdown"],
        "recommendation": final_state["recommendation"],
        "recommendation_justification": final_state["recommendation_justification"],
        "regulator_qa_status": final_state["regulator_qa_status"],
        "regulator_qa_deficiencies": final_state["regulator_qa_deficiencies"],
        "articles": final_state["validated_articles"],
        "events": final_state["filtered_events"],
        "pep_matches": final_state["pep_matches"],
        "sanctions_matches": final_state["sanctions_matches"],
        "created_at": datetime.datetime.utcnow()
    }
