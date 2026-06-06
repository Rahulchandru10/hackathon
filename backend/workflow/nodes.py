import logging
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

logger = logging.getLogger(__name__)

# Instantiate all agents
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

# LangGraph Node Wrappers
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
    return res

async def node_pep_screening(state: ScreeningState):
    logger.info("Executing Node: PEP Screening")
    res = await pep_agent.run(state)
    return res

async def node_sanctions_screening(state: ScreeningState):
    logger.info("Executing Node: Sanctions Screening")
    res = await sanctions_agent.run(state)
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
