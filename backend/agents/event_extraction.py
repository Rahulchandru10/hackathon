import uuid
from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.llm import llm_client

class EventExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__("event_extraction")

    async def run(self, state: ScreeningState) -> dict:
        articles = state["validated_articles"]
        if not articles:
            return {"extracted_events": []}

        extracted_events = []
        
        # We can extract events from each validated article
        for art in articles:
            prompt = f"""
            Analyze the following article details and extract any financial crime, regulatory, or litigation events:
            Article Title: {art.get('title')}
            Source: {art.get('source')}
            Snippet: {art.get('snippet')}
            Publish Date: {art.get('publish_date')}

            Valid Event Types to detect:
            - Fraud
            - Money Laundering
            - Corruption
            - Bribery
            - Terror Financing
            - Tax Evasion
            - Human Trafficking
            - Drug Trafficking
            - Insider Trading
            - Securities Violations
            - Sanctions Violations
            - AML Violations
            - KYC Violations
            - Regulatory Actions
            - Data Breaches
            - Cybercrime
            - Litigation
            - Criminal Charges
            - Convictions
            - Investigations

            Extract a list of events. For each event, output:
            1. event_type (MUST be one of the types above)
            2. severity (0 to 100 based on scale of severity)
            3. description (detailed summary of the event)
            4. detected_date (specific date or year mentioned, or publication date if none)
            5. location (country or region)
            6. entities_involved (list of names of persons/companies)
            """
            
            system_prompt = "You are a specialized compliance intelligence extraction system. Output exact JSON matching the requested structure."
            schema_desc = """
            {
                "events": [
                    {
                        "event_type": "Fraud",
                        "severity": 85,
                        "description": "Indictment of former executives regarding overstated earnings",
                        "detected_date": "2026-04-10",
                        "location": "Germany",
                        "entities_involved": ["Wirecard", "Markus Braun"]
                    }
                ]
            }
            """
            
            try:
                res = await llm_client.generate_structured(prompt, system_prompt=system_prompt, schema_desc=schema_desc)
                for item in res.get("events", []):
                    event_id = str(uuid.uuid4())
                    extracted_events.append({
                        "id": event_id,
                        "article_id": art.get("id", str(uuid.uuid4())),
                        "event_type": item.get("event_type", "Litigation"),
                        "severity": item.get("severity", 50),
                        "description": item.get("description", ""),
                        "detected_date": item.get("detected_date") or art.get("publish_date"),
                        "location": item.get("location") or state["resolved_entity"]["country"],
                        "entities_involved": item.get("entities_involved") or [state["resolved_entity"]["name"]]
                    })
            except Exception as e:
                self.logger.error(f"Failed to extract events for article {art.get('title')}: {e}")
                # Fallback basic extraction from keywords in title:
                title_lower = art.get("title", "").lower()
                detected_type = "Litigation"
                severity = 40
                
                for kw, etype, sev in [
                    ("fraud", "Fraud", 80),
                    ("corruption", "Corruption", 75),
                    ("bribery", "Bribery", 75),
                    ("money laundering", "Money Laundering", 90),
                    ("sanction", "Sanctions Violations", 95),
                    ("charge", "Criminal Charges", 80),
                    ("arrest", "Criminal Charges", 85),
                    ("indict", "Criminal Charges", 80),
                    ("investigat", "Investigations", 50),
                    ("sue", "Litigation", 45),
                    ("lawsuit", "Litigation", 45),
                    ("breach", "Data Breaches", 60),
                    ("evasion", "Tax Evasion", 85)
                ]:
                    if kw in title_lower:
                        detected_type = etype
                        severity = sev
                        break
                
                extracted_events.append({
                    "id": str(uuid.uuid4()),
                    "article_id": art.get("id"),
                    "event_type": detected_type,
                    "severity": severity,
                    "description": art.get("title", ""),
                    "detected_date": art.get("publish_date") or "2026-06-05",
                    "location": state["resolved_entity"]["country"],
                    "entities_involved": [state["resolved_entity"]["name"]]
                })

        self.logger.info(f"Event Extraction extracted {len(extracted_events)} events.")
        return {"extracted_events": extracted_events}
