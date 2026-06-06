from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.search.opensanctions import opensanctions_service
import uuid

class PEPScreeningAgent(BaseAgent):
    def __init__(self):
        super().__init__("pep_screening")

    async def run(self, state: ScreeningState) -> dict:
        resolved = state["resolved_entity"]
        name = resolved["name"]
        
        # Check primary name and aliases
        candidates = [name]
        if resolved.get("aliases"):
            candidates.extend(resolved["aliases"])
            
        pep_matches = []
        
        for cand in candidates:
            # Query OpenSanctions
            matches = await opensanctions_service.search_entity(
                name=cand,
                entity_type=resolved.get("entity_type"),
                country=resolved.get("country") if resolved.get("country") != "Unknown" else None
            )
            
            for m in matches:
                # Check if matches are PEPs (contains 'pep' topic or 'Person' schema and is matched as PEP in fallback)
                is_pep = "pep" in m.get("watchlists", []) or any("pep" in str(w).lower() for w in m.get("watchlists", []))
                
                # Check for high confidence matches (score >= 0.70)
                if is_pep and m.get("confidence", 0.0) >= 0.70:
                    pep_matches.append({
                        "id": m.get("id", str(uuid.uuid4())),
                        "entity_name": m.get("name"),
                        "confidence": m.get("confidence"),
                        "role": m.get("role", "Politically Exposed Person"),
                        "country": m.get("country", "Unknown"),
                        "justification": m.get("justification")
                    })

        self.logger.info(f"PEP Screening found {len(pep_matches)} PEP matches.")
        return {"pep_matches": pep_matches}
