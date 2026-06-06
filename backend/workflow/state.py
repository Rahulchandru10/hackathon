from typing import TypedDict, List, Dict, Any
from backend.models.entity import EntityIntake, EntityResponse
from backend.models.screening import ArticleModel, SanctionMatch, PEPMatch
from backend.models.events import EventModel
from backend.models.risk import RiskBreakdown

class ScreeningState(TypedDict):
    # Inputs
    entity_input: EntityIntake
    monitoring_frequency: str
    
    # Session / Audit Metadata
    case_id: str
    warnings: List[str]
    errors: List[str]
    
    # Processed / Extracted fields
    resolved_entity: Dict[str, Any] # Resolved details (aliases, website etc)
    search_queries: List[str]
    raw_articles: List[Dict[str, Any]]
    deduplicated_articles: List[Dict[str, Any]]
    validated_articles: List[Dict[str, Any]]
    extracted_events: List[Dict[str, Any]]
    filtered_events: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    pep_matches: List[Dict[str, Any]]
    sanctions_matches: List[Dict[str, Any]]
    network_nodes: List[Dict[str, Any]]
    network_edges: List[Dict[str, Any]]
    
    # Scoring & Decisioning
    risk_breakdown: Dict[str, int]
    risk_score: int
    recommendation: str
    recommendation_justification: str
    explainability_report: str
    regulator_qa_status: str # "PASS" or "FAIL"
    regulator_qa_deficiencies: List[str]
    
    # Monitoring logs/deltas
    is_delta_detected: bool
    delta_details: List[str]
