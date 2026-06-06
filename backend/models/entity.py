from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal

class EntityIntake(BaseModel):
    name: str = Field(..., description="Legal name or individual full name of the target entity")
    entity_type: Optional[Literal["Company", "Individual", "Unknown"]] = Field(default="Unknown", description="Type of the target entity")
    country: Optional[str] = Field(default=None, description="Country of registration or residence")
    industry: Optional[str] = Field(default=None, description="Industry sector for companies")
    website: Optional[str] = Field(default=None, description="Official website URL")
    registration_number: Optional[str] = Field(default=None, description="Company registration ID or tax number")
    aliases: Optional[List[str]] = Field(default_factory=list, description="Known alternate names or doing business as (DBA)")
    parent_company: Optional[str] = Field(default=None, description="Parent entity name if company")
    subsidiaries: Optional[List[str]] = Field(default_factory=list, description="Subsidiary names")
    directors: Optional[List[str]] = Field(default_factory=list, description="Names of directors")
    shareholders: Optional[List[str]] = Field(default_factory=list, description="Names of corporate or individual shareholders")
    beneficial_owners: Optional[List[str]] = Field(default_factory=list, description="Ultimate Beneficial Owners (UBOs)")

class EntityResponse(EntityIntake):
    id: str
