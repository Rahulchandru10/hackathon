from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.models.entity import EntityResponse

class UserBase(BaseModel):
    username: str
    email: str
    role: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class CaseUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    recommendation: Optional[str] = None
    assigned_to: Optional[int] = None

class AuditLogResponse(BaseModel):
    id: int
    case_id: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    details: Optional[str] = None
    timestamp: datetime

class CaseResponse(BaseModel):
    id: str
    entity: EntityResponse
    status: str
    risk_score: int
    risk_breakdown: Dict[str, Any]  # raw dict from DB/workflow - no nested model needed
    recommendation: Optional[str] = None
    recommendation_justification: Optional[str] = None
    regulator_qa_status: str
    regulator_qa_deficiencies: List[str] = []
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

