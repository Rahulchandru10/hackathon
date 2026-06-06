from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.llm import llm_client
import json

class EntityResolutionAgent(BaseAgent):
    def __init__(self):
        super().__init__("entity_resolution")

    async def run(self, state: ScreeningState) -> dict:
        resolved = state["resolved_entity"]
        
        # If we have only name and no other data, resolution is limited
        if resolved["country"] == "Unknown" and not resolved["website"] and not resolved["registration_number"]:
            return {
                "resolved_entity": {
                    **resolved,
                    "resolution_match_type": "Partial Match",
                    "resolution_confidence": 0.5,
                    "resolution_justification": "Only entity name was provided. High likelihood of partial matches and same-name-different-entity occurrences."
                }
            }

        prompt = f"""
        Analyze the following entity profile and resolve the match category and confidence:
        Entity Profile:
        - Legal Name: {resolved['name']}
        - Type: {resolved['entity_type']}
        - Country: {resolved['country']}
        - Website: {resolved['website']}
        - Registration Number: {resolved['registration_number']}
        - Aliases: {resolved['aliases']}
        - Directors: {resolved['directors']}
        - Shareholders: {resolved['shareholders']}
        - Ultimate Beneficial Owners: {resolved['beneficial_owners']}

        Determine if an external database record containing these details should be classified as:
        1. "Exact Match"
        2. "Alias Match"
        3. "Partial Match"
        4. "Same Name Different Entity"
        5. "False Positive"

        Analyze the attributes (country, website, registration number, directors) to provide:
        - match_type (one of the 5 categories above)
        - confidence (float between 0.0 and 1.0)
        - justification (clear reason why)
        """
        
        system_prompt = "You are an expert compliance officer. Analyze corporate records and resolve entity identities accurately."
        schema_desc = """
        {
            "match_type": "string",
            "confidence": 0.95,
            "justification": "string"
        }
        """
        
        try:
            res = await llm_client.generate_structured(prompt, system_prompt=system_prompt, schema_desc=schema_desc)
            resolved["resolution_match_type"] = res.get("match_type", "Partial Match")
            resolved["resolution_confidence"] = res.get("confidence", 0.5)
            resolved["resolution_justification"] = res.get("justification", "Resolution analyzed via LLM metadata matching.")
        except Exception as e:
            self.logger.error(f"Resolution agent LLM call failed, fallback to defaults: {e}")
            resolved["resolution_match_type"] = "Exact Match" if resolved["registration_number"] else "Partial Match"
            resolved["resolution_confidence"] = 0.8 if resolved["registration_number"] else 0.6
            resolved["resolution_justification"] = "Resolution resolved using default heuristic parameters."

        return {"resolved_entity": resolved}
