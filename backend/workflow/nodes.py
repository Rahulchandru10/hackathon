import logging
import uuid
from backend.workflow.state import ScreeningState
from backend.agents.entity_intake import EntityIntakeAgent
from backend.agents.entity_resolution import EntityResolutionAgent
from backend.agents.search_query import SearchQueryAgent
from backend.agents.media_collection import MediaCollectionAgent
from backend.agents.duplicate_detection import DuplicateDetectionAgent
from backend.agents.source_credibility import SourceCredibilityAgent
from backend.agents.event_extraction import EventExtractionAgent
from backend.agents.false_positive import FalsePositiveAgent
from backend.agents.timeline import TimelineAgent
from backend.agents.network_intelligence import NetworkIntelligenceAgent
from backend.agents.pep_screening import PEPScreeningAgent
from backend.agents.sanctions_screening import SanctionsScreeningAgent
from backend.agents.risk_scoring import RiskScoringAgent
from backend.agents.recommendation import RecommendationAgent
from backend.agents.explainability import ExplainabilityAgent
from backend.agents.regulator_qa import RegulatorQAAgent
from backend.agents.monitoring import MonitoringAgent

# Dynamic Graph Database Bridge Connection
from backend.services.databases.neo4j import neo4j_client

logger = logging.getLogger(__name__)

# Instantiate all orchestration agents
intake_agent = EntityIntakeAgent()
resolution_agent = EntityResolutionAgent()
search_query_agent = SearchQueryAgent()
media_collection_agent = MediaCollectionAgent()
duplicate_detection_agent = DuplicateDetectionAgent()
source_credibility_agent = SourceCredibilityAgent()
event_extraction_agent = EventExtractionAgent()
false_positive_agent = FalsePositiveAgent()
timeline_agent = TimelineAgent()
network_agent = NetworkIntelligenceAgent()
pep_agent = PEPScreeningAgent()
sanctions_agent = SanctionsScreeningAgent()
risk_agent = RiskScoringAgent()
rec_agent = RecommendationAgent()
explain_agent = ExplainabilityAgent()
qa_agent = RegulatorQAAgent()
mon_agent = MonitoringAgent()

# ─── LANGGRAPH NODE WRAPPERS ──────────────────────────────────────────────────

async def node_intake(state: ScreeningState):
    logger.info("Executing Node: Intake")
    res = await intake_agent.run(state)
    return res

async def node_resolution(state: ScreeningState):
    logger.info("Executing Node: Resolution")
    res = await resolution_agent.run(state)
    return res

async def node_search_query(state: ScreeningState):
    logger.info("Executing Node: Search Query")
    res = await search_query_agent.run(state)
    return res

async def node_media_collection(state: ScreeningState):
    logger.info("Executing Node: Media Collection")
    res = await media_collection_agent.run(state)
    
    # Extract operational parameters from state context
    case_id = state.get("case_id")
    validated_articles = res.get("validated_articles", [])
    
    # Real-time data pipeline serialization to Graph Store
    try:
        for idx, art in enumerate(validated_articles):
            art_id = art.get("id") or f"{case_id}-art-{uuid.uuid4().hex[:6]}"
            await neo4j_client.add_article_relationship(
                entity_id=case_id,
                article_id=art_id,
                article_title=art.get("title", "Adverse Media Report"),
                url=art.get("url", ""),
                credibility_score=art.get("credibility_score", 70)
            )
        logger.info(f"Successfully serialized {len(validated_articles)} adverse media node vectors.")
    except Exception as e:
        logger.error(f"Graph pipeline serialization failure during media stream extraction: {e}")
        
    return res

async def node_duplicate_detection(state: ScreeningState):
    logger.info("Executing Node: Duplicate Detection")
    res = await duplicate_detection_agent.run(state)
    return res

async def node_source_credibility(state: ScreeningState):
    logger.info("Executing Node: Source Credibility")
    res = await source_credibility_agent.run(state)
    return res

async def node_event_extraction(state: ScreeningState):
    logger.info("Executing Node: Event Extraction")
    res = await event_extraction_agent.run(state)
    return res

async def node_false_positive(state: ScreeningState):
    logger.info("Executing Node: False Positive Elimination")
    res = await false_positive_agent.run(state)
    return res

async def node_timeline(state: ScreeningState):
    logger.info("Executing Node: Timeline Generation")
    res = await timeline_agent.run(state)
    return res

async def node_network_intelligence(state: ScreeningState):
    logger.info("Executing Node: Network Intelligence")
    res = await network_agent.run(state)
    
    case_id = state.get("case_id")
    
    # 1. Fall back gracefully to raw user intake data if LLM resolution arrays are empty
    resolved_entity = res.get("resolved_entity") if res.get("resolved_entity") else {}
    intake_entity = state.get("entity_input")

    if hasattr(intake_entity, "model_dump"):
        intake_dict = intake_entity.model_dump()
    elif hasattr(intake_entity, "__dict__"):
        intake_dict = vars(intake_entity)
    else:
        intake_dict = intake_entity if isinstance(intake_entity, dict) else {}

    # Extract labels directly by prioritizing resolved data, falling back to form data
    entity_name = resolved_entity.get("name") or intake_dict.get("name", "Unknown Focus Target")
    entity_type = resolved_entity.get("entity_type") or intake_dict.get("entity_type", "Company")
    country = resolved_entity.get("country") or intake_dict.get("country", None)
    risk_score = state.get("risk_score") or res.get("risk_score", 0)

    # Reconstruct structural nodes programmatically to map real fields
    try:
        # A. Register Primary Target Root Node
        await neo4j_client.add_entity_node(
            entity_id=case_id,
            name=entity_name,
            entity_type=entity_type,
            country=country,
            risk_score=int(risk_score)
        )
        
        # B. Map metadata matrix groupings extracted directly from input arrays
        directors = resolved_entity.get("directors") or intake_dict.get("directors", [])
        ubos = resolved_entity.get("beneficial_owners") or intake_dict.get("beneficial_owners", [])
        shareholders = resolved_entity.get("shareholders") or intake_dict.get("shareholders", [])
        subsidiaries = resolved_entity.get("subsidiaries") or intake_dict.get("subsidiaries", [])
        parent_co = resolved_entity.get("parent_company") or intake_dict.get("parent_company", None)

        if parent_co:
            parent_id = f"{case_id}-parent"
            await neo4j_client.add_entity_node(parent_id, str(parent_co).strip(), "Company", country)
            await neo4j_client.add_relationship(parent_id, case_id, "PARENT_COMPANY", {"source": "intake_registry"})

        for idx, item in enumerate(directors or []):
            if item and str(item).strip():
                node_id = f"{case_id}-dir-{idx}"
                await neo4j_client.add_entity_node(node_id, str(item).strip(), "Individual")
                await neo4j_client.add_relationship(node_id, case_id, "DIRECTOR", {"source": "intake_registry"})
                
        for idx, item in enumerate(ubos or []):
            if item and str(item).strip():
                node_id = f"{case_id}-ubo-{idx}"
                await neo4j_client.add_entity_node(node_id, str(item).strip(), "Individual")
                await neo4j_client.add_relationship(node_id, case_id, "BENEFICIAL_OWNER", {"source": "intake_registry"})

        for idx, item in enumerate(shareholders or []):
            if item and str(item).strip():
                node_id = f"{case_id}-sh-{idx}"
                await neo4j_client.add_entity_node(node_id, str(item).strip(), "Company")
                await neo4j_client.add_relationship(node_id, case_id, "SHAREHOLDER", {"source": "intake_registry"})

        for idx, item in enumerate(subsidiaries or []):
            if item and str(item).strip():
                node_id = f"{case_id}-sub-{idx}"
                await neo4j_client.add_entity_node(node_id, str(item).strip(), "Company")
                await neo4j_client.add_relationship(case_id, node_id, "SUBSIDIARY", {"source": "intake_registry"})

        # C. Inject Dynamic Media Nodes directly from the validated collection array
        validated_articles = state.get("validated_articles", []) or res.get("validated_articles", [])
        for idx, art in enumerate(validated_articles or []):
            art_id = art.get("id") or f"{case_id}-art-{idx}"
            await neo4j_client.add_article_relationship(
                entity_id=case_id,
                article_id=art_id,
                article_title=art.get("title", "Adverse Media Report"),
                url=art.get("url", ""),
                credibility_score=art.get("credibility_score", 70)
            )

        logger.info(f"✅ Graph pipeline structures populated successfully for targeted case context: {case_id}")
    except Exception as e:
        logger.error(f"❌ Graph engine fault while serializing intake structural relationships: {e}")

    return res

async def node_pep_screening(state: ScreeningState):
    logger.info("Executing Node: PEP Screening")
    res = await pep_agent.run(state)
    return res

async def node_sanctions_screening(state: ScreeningState):
    logger.info("Executing Node: Sanctions Screening")
    res = await sanctions_agent.run(state)
    
    case_id = state.get("case_id")
    sanctions_matches = res.get("sanctions_matches", [])
    
    # Real-time conditional check. Materialize danger nodes if watchlist hits trigger
    try:
        for idx, match in enumerate(sanctions_matches or []):
            sanc_id = f"{case_id}-sanc-{idx}"
            await neo4j_client.add_sanction_relationship(
                entity_id=case_id,
                sanction_id=sanc_id,
                watchlist=match.get("watchlist", "Global Watchlist"),
                justification=match.get("justification", "Compliance Risk Threshold Cleared")
            )
        if sanctions_matches:
            logger.warning(f"Materialized {len(sanctions_matches)} watchlist vector alerts to case: {case_id}")
    except Exception as e:
        logger.error(f"Graph pipeline serialization failure during sanction match stream extraction: {e}")
        
    return res

async def node_risk_scoring(state: ScreeningState):
    logger.info("Executing Node: Risk Scoring")
    res = await risk_agent.run(state)
    return res

async def node_recommendation(state: ScreeningState):
    logger.info("Executing Node: Recommendation Engine")
    res = await rec_agent.run(state)
    return res

async def node_explainability(state: ScreeningState):
    logger.info("Executing Node: Explainability Engine")
    res = await explain_agent.run(state)
    return res

async def node_regulator_qa(state: ScreeningState):
    logger.info("Executing Node: Regulator QA Agent")
    res = await qa_agent.run(state)
    return res

async def node_monitoring(state: ScreeningState):
    logger.info("Executing Node: Monitoring Agent")
    res = await mon_agent.run(state)
    return res
