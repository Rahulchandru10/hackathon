from pydantic import BaseModel, Field
from typing import List, Optional

class EventModel(BaseModel):
    id: str
    case_id: str
    article_id: Optional[str] = None
    event_type: str = Field(..., description="E.g., Fraud, Money Laundering, Corruption, Sanctions Violations")
    severity: int = Field(..., ge=0, le=100, description="Risk severity from 0 to 100")
    description: str
    detected_date: Optional[str] = None
    location: Optional[str] = None
    entities_involved: List[str] = Field(default_factory=list)
