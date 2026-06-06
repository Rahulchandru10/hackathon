from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState

class TimelineAgent(BaseAgent):
    def __init__(self):
        super().__init__("timeline")

    async def run(self, state: ScreeningState) -> dict:
        events = state["filtered_events"]
        
        # Sort events by date. Since date is a string, let's parse or sort gracefully.
        # Format dates often come as YYYY-MM-DD or YYYY. Let's do a fallback sort.
        def get_sort_key(ev):
            date_str = ev.get("detected_date", "") or ""
            # Simple normalization to make it sortable
            clean_date = date_str.replace("/", "-").strip()
            # If empty or not starting with digit, put at end
            if not clean_date or not clean_date[0].isdigit():
                return "9999-12-31"
            return clean_date

        sorted_events = sorted(events, key=get_sort_key)
        
        timeline = []
        for i, ev in enumerate(sorted_events, 1):
            timeline.append({
                "sequence": i,
                "date": ev.get("detected_date", "Unknown Date"),
                "event_type": ev.get("event_type", "General Risk Event"),
                "severity": ev.get("severity", 50),
                "description": ev.get("description", ""),
                "location": ev.get("location", "Unknown"),
                "entities_involved": ev.get("entities_involved", []),
                "article_id": ev.get("article_id")
            })

        self.logger.info(f"Timeline Agent sorted and built timeline of {len(timeline)} events.")
        return {"timeline": timeline}
