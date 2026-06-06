from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState

class EntityIntakeAgent(BaseAgent):
    def __init__(self):
        super().__init__("entity_intake")

    async def run(self, state: ScreeningState) -> dict:
        entity = state["entity_input"]
        warnings = []
        
        # Mandatory validation
        if not entity.name or not entity.name.strip():
            raise ValueError("Entity Name is a required input for screening.")
            
        # Check optional fields presence for warnings
        optional_fields = [
            entity.entity_type, entity.country, entity.industry, 
            entity.website, entity.registration_number, entity.aliases,
            entity.parent_company, entity.subsidiaries, entity.directors,
            entity.shareholders, entity.beneficial_owners
        ]
        
        has_optional_context = any(
            bool(field) if not isinstance(field, list) else len(field) > 0 
            for field in optional_fields if field is not None
        )
        
        if not has_optional_context:
            warnings.append("Limited entity context may increase false positives.")
            self.logger.warning("Intake received entity name only. Warning triggered.")
        
        # Prepare normalized resolved entity details
        resolved_details = {
            "name": entity.name.strip(),
            "entity_type": entity.entity_type or "Unknown",
            "country": entity.country.strip() if entity.country else "Unknown",
            "industry": entity.industry.strip() if entity.industry else "Unknown",
            "website": entity.website.strip() if entity.website else "",
            "registration_number": entity.registration_number.strip() if entity.registration_number else "",
            "aliases": [a.strip() for a in entity.aliases if a.strip()] if entity.aliases else [],
            "parent_company": entity.parent_company.strip() if entity.parent_company else "",
            "subsidiaries": [s.strip() for s in entity.subsidiaries if s.strip()] if entity.subsidiaries else [],
            "directors": [d.strip() for d in entity.directors if d.strip()] if entity.directors else [],
            "shareholders": [sh.strip() for sh in entity.shareholders if sh.strip()] if entity.shareholders else [],
            "beneficial_owners": [ubo.strip() for ubo in entity.beneficial_owners if ubo.strip()] if entity.beneficial_owners else []
        }

        return {
            "warnings": warnings,
            "resolved_entity": resolved_details
        }
