from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState

class SearchQueryAgent(BaseAgent):
    def __init__(self):
        super().__init__("search_query")
        
        # Keywords translations for compliance patterns
        self.multilingual_keywords = {
            "en": ["fraud", "corruption", "bribery", "money laundering", "sanctions", "criminal charges", "investigation", "regulatory action", "enforcement", "tax evasion", "cybercrime", "litigation", "lawsuit", "data breach"],
            "es": ["fraude", "corrupción", "soborno", "lavado de dinero", "sanciones", "cargos criminales", "investigación", "demanda", "evasión fiscal"],
            "fr": ["fraude", "corruption", "pot-de-vin", "blanchiment d'argent", "sanctions", "poursuites pénales", "enquête", "procès", "évasion fiscale"],
            "zh": ["欺诈", "腐败", "贿赂", "洗钱", "制裁", "刑事指控", "调查", "诉讼", "逃税"],
            "ru": ["мошенничество", "коррупция", "взятка", "отмывание денег", "санкции", "уголовные обвинения", "расследование", "судебный иск"],
            "ar": ["احتيال", "فساد", "رشوة", "غسيل أموال", "عقوبات", "اتهامات جنائية", "تحقيق", "دعوى قضائية"],
            "hi": ["धोखाधड़ी", "भ्रष्टाचार", "रिश्वत", "मनी लॉन्ड्रिंग", "प्रतिबंध", "आपराधिक आरोप", "जांच", "मुकदमा"],
            "ta": ["மோசடி", "ஊழல்", "லஞ்சம்", "பண மோசடி", "தடைகள்", "குற்றவியல் குற்றச்சாட்டுகள்", "விசாரணை", "வழக்கு"]
        }

    async def run(self, state: ScreeningState) -> dict:
        resolved = state["resolved_entity"]
        name = resolved["name"]
        
        # Build set of target names to query (primary name + aliases)
        names_to_query = [name]
        if resolved.get("aliases"):
            names_to_query.extend(resolved["aliases"][:2]) # Limit to top 2 aliases to prevent explosion
            
        queries = []
        
        # Generate targeted searches across languages using core crime patterns
        for target_name in names_to_query:
            # English covers all 14 search patterns
            for term in self.multilingual_keywords["en"]:
                queries.append(f'"{target_name}" {term}')
            
            # For other languages, use top critical terms (e.g., fraud, money laundering, sanctions, investigation)
            # to cover multilingual bases without query bloating
            critical_indices = [0, 3, 4, 6] # fraud, money laundering, sanctions, investigation
            for lang, terms in self.multilingual_keywords.items():
                if lang == "en":
                    continue
                for idx in critical_indices:
                    if idx < len(terms):
                        queries.append(f'"{target_name}" {terms[idx]}')

        # Limit total queries to prevent API exhaustion, prioritizing English and primary name
        queries = list(dict.fromkeys(queries)) # deduplicate
        self.logger.info(f"Generated {len(queries)} multilingual search queries.")
        
        return {"search_queries": queries[:25]} # Return top 25 high-priority queries
