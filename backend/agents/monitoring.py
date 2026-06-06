from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState

class MonitoringAgent(BaseAgent):
    def __init__(self):
        super().__init__("monitoring")

    async def run(self, state: ScreeningState) -> dict:
        monitoring_freq = state["monitoring_frequency"]
        
        # Check if we are running in monitoring mode (Daily/Weekly vs One-time)
        if monitoring_freq == "One-time":
            return {
                "is_delta_detected": False,
                "delta_details": []
            }
            
        # The scheduler handles the actual DB comparison,
        # but here we can flag if this screening contains new elements:
        delta_details = []
        is_delta = False
        
        articles = state["validated_articles"]
        sanctions = state["sanctions_matches"]
        
        # Look for new entries (e.g., published in the last 24 hours/7 days)
        # We can implement a simplified logical check
        if len(articles) > 0:
            is_delta = True
            delta_details.append(f"Detected {len(articles)} adverse media articles during this monitoring cycle.")
            
        if len(sanctions) > 0:
            is_delta = True
            delta_details.append(f"Detected {len(sanctions)} active sanctions watchlist matches.")

        return {
            "is_delta_detected": is_delta,
            "delta_details": delta_details
        }
