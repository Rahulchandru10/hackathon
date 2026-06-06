from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState

class SourceCredibilityAgent(BaseAgent):
    def __init__(self):
        super().__init__("source_credibility")
        
        # Mapping known sources to tiers and scores
        self.known_sources = {
            "reuters": {"tier": 1, "score": 98, "name": "Reuters"},
            "bloomberg": {"tier": 1, "score": 96, "name": "Bloomberg"},
            "wsj": {"tier": 1, "score": 97, "name": "Wall Street Journal"},
            "financial times": {"tier": 1, "score": 96, "name": "Financial Times"},
            "ft": {"tier": 1, "score": 96, "name": "Financial Times"},
            "ap": {"tier": 1, "score": 95, "name": "Associated Press"},
            "associated press": {"tier": 1, "score": 95, "name": "Associated Press"},
            "gov": {"tier": 2, "score": 90, "name": "Government Portal"},
            "sec": {"tier": 2, "score": 92, "name": "Securities and Exchange Commission"},
            "fca": {"tier": 2, "score": 92, "name": "Financial Conduct Authority"},
            "ofac": {"tier": 2, "score": 95, "name": "Office of Foreign Assets Control"},
            "justice": {"tier": 2, "score": 92, "name": "Department of Justice"},
            "court": {"tier": 2, "score": 88, "name": "Court Records"},
        }

    async def run(self, state: ScreeningState) -> dict:
        articles = state["deduplicated_articles"]
        validated_articles = []

        for art in articles:
            source = art.get("source", "").lower().strip()
            title = art.get("title", "")
            
            # Simple heuristic tier matching
            tier = 3 # Default to regional media
            score = 70
            
            matched = False
            for key, val in self.known_sources.items():
                if key in source or key in art.get("url", "").lower():
                    tier = val["tier"]
                    score = val["score"]
                    matched = True
                    break
            
            if not matched:
                # Detect Blogs/Forums
                if any(x in source or x in art.get("url", "").lower() for x in ["blog", "forum", "wordpress", "reddit", "twitter", "medium.com"]):
                    tier = 4
                    score = 40
            
            # Formulate detailed score attributes for auditability
            art["source_tier"] = tier
            art["credibility_score"] = score
            art["credibility_breakdown"] = {
                "authority": 90 if tier == 1 else (80 if tier == 2 else (65 if tier == 3 else 40)),
                "editorial_standards": 95 if tier == 1 else (85 if tier == 2 else (60 if tier == 3 else 30)),
                "reliability": 95 if tier == 1 else (90 if tier == 2 else (70 if tier == 3 else 50)),
                "bias_risk": 90 if tier == 1 else (80 if tier == 2 else (60 if tier == 3 else 40)),
                "manipulation_risk": 95 if tier == 1 else (90 if tier == 2 else (75 if tier == 3 else 45))
            }
            
            validated_articles.append(art)

        self.logger.info(f"Source Credibility evaluated {len(validated_articles)} articles.")
        return {"validated_articles": validated_articles}
