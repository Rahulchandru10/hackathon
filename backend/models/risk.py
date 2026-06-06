from pydantic import BaseModel, Field
from typing import Dict

class RiskBreakdown(BaseModel):
    overall: int = Field(..., ge=0, le=100)
    fraud: int = Field(default=0, ge=0, le=100)
    regulatory: int = Field(default=0, ge=0, le=100)
    network: int = Field(default=0, ge=0, le=100)
    sanctions: int = Field(default=0, ge=0, le=100)
    pep: int = Field(default=0, ge=0, le=100)
    aml_kyc: int = Field(default=0, ge=0, le=100)

class RiskScoreResponse(BaseModel):
    case_id: str
    risk_level: str # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    breakdown: RiskBreakdown
    justification: str
