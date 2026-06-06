from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SubscriptionCreate(BaseModel):
    entity_name: str
    entity_type: Optional[str] = "Company"
    country: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = None
    frequency: str = Field(default="Weekly", description="Daily, Weekly, One-time")

class SubscriptionResponse(SubscriptionCreate):
    id: int
    created_by: int
    last_checked: datetime
    is_active: bool
    created_at: datetime

class AlertResponse(BaseModel):
    id: str
    subscription_id: int
    case_id: Optional[str] = None
    alert_type: str # 'New Article', 'Risk Score Change', 'Sanction Match'
    description: str
    severity: str # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    is_read: bool
    created_at: datetime
