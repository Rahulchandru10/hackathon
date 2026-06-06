from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.search.opensanctions import opensanctions_service
from backend.services.databases.neo4j import neo4j_client
import uuid

class SanctionsScreeningAgent(BaseAgent):
    def __init__(self):
        super().__init__("sanctions_screening")

    async def run(self, state: ScreeningState) -> dict:
        resolved = state["resolved_entity"]
        name = resolved["name"]
        case_id = state["case_id"]
        
        candidates = [name]
        if resolved.get("aliases"):
            candidates.extend(resolved["aliases"])
            
        sanctions_matches = []
        
        for cand in candidates:
            matches = await opensanctions_service.search_entity(
                name=cand,
                entity_type=resolved.get("entity_type"),
                country=resolved.get("country") if resolved.get("country") != "Unknown" else None
            )
            
            for m in matches:
                # Check if matches are sanctioned (contains 'sanction' topic or listed on major watchlists)
                is_sanction = "sanction" in m.get("watchlists", []) or any("sanction" in str(w).lower() for w in m.get("watchlists", []))
                
                # Check for high confidence matches (score >= 0.70)
                if is_sanction and m.get("confidence", 0.0) >= 0.70:
                    match_record = {
                        "id": m.get("id", str(uuid.uuid4())),
                        "entity_name": m.get("name"),
                        "confidence": m.get("confidence"),
                        "watchlist": ", ".join(m.get("watchlists", ["Global Watchlist"])),
                        "justification": m.get("justification")
                    }
                    sanctions_matches.append(match_record)
                    
                    # Update Neo4j graph relationships
                    try:
                        # Add sanction node and link to target entity
                        sanction_id = f"sanc-{m.get('id')}"
                        watchlist_str = ", ".join(m.get("watchlists", ["Sanction Watchlist"]))
                        
                        await neo4j_client.add_sanction_relationship(
                            entity_id=case_id,
                            sanction_id=sanction_id,
                            watchlist=watchlist_str,
                            justification=m.get("justification")
                        )
                        
                        # Also add sanction node to local network list for frontend rendering
                        state["network_nodes"].append({
                            "id": sanction_id,
                            "label": f"Sanction: {watchlist_str}",
                            "group": "Sanction",
                            "type": "Sanction",
                            "risk_score": 100
                        })
                        state["network_edges"].append({
                            "from": case_id,
                            "to": sanction_id,
                            "label": "SANCTIONED_BY"
                        })
                    except Exception as e:
                        self.logger.error(f"Failed to add sanction relation to Neo4j: {e}")

        self.logger.info(f"Sanctions Screening found {len(sanctions_matches)} sanction matches.")
        return {
            "sanctions_matches": sanctions_matches,
            "network_nodes": state["network_nodes"],
            "network_edges": state["network_edges"]
        }
