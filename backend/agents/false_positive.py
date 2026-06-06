from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.llm import llm_client

class FalsePositiveAgent(BaseAgent):
    def __init__(self):
        super().__init__("false_positive")

    async def run(self, state: ScreeningState) -> dict:
        events = state["extracted_events"]
        resolved = state["resolved_entity"]
        
        if not events:
            return {"filtered_events": []}

        filtered_events = []
        
        # Verify each event with LLM to prevent false positives
        for ev in events:
            prompt = f"""
            Verify if the following event is a False Positive for our target entity:
            Target Entity Profile:
            - Legal Name: {resolved['name']}
            - Aliases: {resolved['aliases']}
            - Country: {resolved['country']}
            - Industry: {resolved['industry']}
            - Website: {resolved['website']}
            - Directors: {resolved['directors']}

            Extracted Event to verify:
            - Event Type: {ev['event_type']}
            - Description: {ev['description']}
            - Entities Involved in Event: {ev['entities_involved']}
            - Location of Event: {ev['location']}

            Analyze if this event is about a different entity with the same name, or a completely unrelated entity, or is indeed a match for our target entity.
            Return a JSON dict:
            - is_false_positive (boolean: true if it is a false positive, false if it is a true match)
            - justification (explanation of why)
            """
            
            system_prompt = "You are an audit agent that eliminates false positive compliance matches. Be precise."
            schema_desc = """
            {
                "is_false_positive": false,
                "justification": "The event lists Markus Braun, who is the confirmed former CEO of Wirecard AG, matching our target."
            }
            """
            
            try:
                res = await llm_client.generate_structured(prompt, system_prompt=system_prompt, schema_desc=schema_desc)
                if not res.get("is_false_positive", False):
                    ev["false_positive_justification"] = res.get("justification", "Verified as a valid event match.")
                    filtered_events.append(ev)
                else:
                    self.logger.info(f"Filtered out false positive event: {ev['description']} - Justification: {res.get('justification')}")
            except Exception as e:
                self.logger.error(f"False Positive verification failed for event {ev['description']}: {e}")
                # Fallback to keep event if the entities list has any substring match with target or aliases:
                match_found = False
                for ent in ev['entities_involved']:
                    if resolved['name'].lower() in ent.lower() or ent.lower() in resolved['name'].lower():
                        match_found = True
                        break
                    for al in resolved['aliases']:
                        if al.lower() in ent.lower() or ent.lower() in al.lower():
                            match_found = True
                            break
                if match_found or not ev['entities_involved']:
                    ev["false_positive_justification"] = "Kept via fallback substring matching."
                    filtered_events.append(ev)

        self.logger.info(f"False Positive agent kept {len(filtered_events)} events out of {len(events)}.")
        return {"filtered_events": filtered_events}
