from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.llm import llm_client

class RegulatorQAAgent(BaseAgent):
    def __init__(self):
        super().__init__("regulator_qa")

    async def run(self, state: ScreeningState) -> dict:
        resolved = state["resolved_entity"]
        risk_score = state["risk_score"]
        recommendation = state["recommendation"]
        justification = state["recommendation_justification"]
        articles = state["validated_articles"]
        peps = state["pep_matches"]
        sanctions = state["sanctions_matches"]
        
        prompt = f"""
        Act as a strict Regulatory Auditor. Review the compliance file below and challenge the findings for:
        Target Entity Name: {resolved['name']}
        Risk Score: {risk_score}/100
        Recommendation: {recommendation}
        Recommendation Justification: {justification}
        Number of Articles: {len(articles)}
        PEP Matches: {len(peps)}
        Sanctions Matches: {len(sanctions)}

        Evaluate these specific challenge criteria:
        1. **Weak Evidence**: Are matches or events based on sketchy source tiers (e.g. tier 4 blogs) rather than tier 1/2?
        2. **Unsupported Conclusions**: Does the recommendation align logically with the risk score?
        3. **Missing Citations**: Do the matches list source watchlists or specific urls?
        4. **Poor Entity Resolution**: Was the match confidence too low to justify the sanction/PEP label?
        5. **Weak Risk Logic**: Is the final score justified?

        Return a JSON response:
        - status: "PASS" or "FAIL"
        - deficiencies: a list of strings detailing any gaps, or empty if status is "PASS"
        """
        
        system_prompt = "You are a regulatory examiner verifying that compliance cases meet all statutory audit standards."
        schema_desc = """
        {
            "status": "PASS",
            "deficiencies": []
        }
        """
        
        try:
            res = await llm_client.generate_structured(prompt, system_prompt=system_prompt, schema_desc=schema_desc)
            status = res.get("status", "PASS")
            deficiencies = res.get("deficiencies", [])
        except Exception as e:
            self.logger.error(f"Regulator QA agent failed to call LLM: {e}")
            # Fallback checks:
            status = "PASS"
            deficiencies = []
            if not articles and not peps and not sanctions and risk_score > 20:
                status = "FAIL"
                deficiencies.append("Risk score is positive but no adverse media, PEP, or sanction findings are present.")
            if risk_score > 75 and recommendation == "CLEAR":
                status = "FAIL"
                deficiencies.append("High risk score assigned but recommendation is set to CLEAR. Unsupported conclusion.")
                
        self.logger.info(f"Regulator QA Audit complete. Status: {status}")
        return {
            "regulator_qa_status": status,
            "regulator_qa_deficiencies": deficiencies
        }
