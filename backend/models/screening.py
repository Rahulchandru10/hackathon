from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.models.entity import EntityIntake, EntityResponse

class ArticleModel(BaseModel):
    id: str
    title: str
    url: str
    source: str
    source_tier: int
    credibility_score: int
    publish_date: Optional[datetime] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    language: str = "en"
    cluster_id: Optional[str] = None

class SanctionMatch(BaseModel):
    watchlist: str
    entity_name: str
    confidence: float
    justification: str

class PEPMatch(BaseModel):
    entity_name: str
    confidence: float
    role: str
    country: str
    justification: str

class ScreeningRequest(BaseModel):
    entity: EntityIntake
    monitoring_frequency: Optional[str] = "One-time" # "One-time", "Daily", "Weekly"

class ScreeningResponse(BaseModel):
    case_id: str
    entity: EntityResponse
    warnings: List[str] = []
    risk_score: int
    risk_breakdown: Dict[str, int]
    recommendation: str
    recommendation_justification: str
    regulator_qa_status: str
    regulator_qa_deficiencies: List[str] = []
    articles: List[ArticleModel] = []
    pep_matches: List[PEPMatch] = []
    sanctions_matches: List[SanctionMatch] = []
    created_at: datetime
