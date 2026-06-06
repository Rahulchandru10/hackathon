from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.llm import llm_client

class RecommendationAgent(BaseAgent):
    def __init__(self):
        super().__init__("recommendation")

    async def run(self, state: ScreeningState) -> dict:
        risk_score = state["risk_score"]
        warnings = state["warnings"]
        peps = state["pep_matches"]
        sanctions = state["sanctions_matches"]
        
        # Base decision threshold
        if sanctions:
            base_rec = "REJECT"
        elif risk_score >= 76:
            base_rec = "REJECT" if any(s["confidence"] > 0.85 for s in sanctions) else "ESCALATE"
        elif risk_score >= 51:
            base_rec = "ENHANCED_DUE_DILIGENCE"
        elif risk_score >= 21:
            base_rec = "MONITOR"
        else:
            base_rec = "CLEAR"

        # Apply context override if warnings or PEP matches are present
        if warnings and base_rec == "CLEAR":
            base_rec = "REQUIRES_HUMAN_REVIEW"
        elif peps and base_rec in ["CLEAR", "MONITOR"]:
            base_rec = "ENHANCED_DUE_DILIGENCE"

        # Call LLM to generate an compliance-approved justification
        prompt = f"""
        Analyze the screening metrics and generate a professional, compliance-compliant recommendation justification:
        Target Entity Name: {state['resolved_entity']['name']}
        Overall Risk Score: {risk_score}/100
        Sanctions Matches: {len(sanctions)}
        PEP Matches: {len(peps)}
        Warnings present: {warnings}
        Proposed Action: {base_rec}

        Explain clearly:
        1. Why this action is recommended.
        2. The primary risks driving this recommendation.
        3. Immediate next steps for compliance analysts.
        """
        
        system_prompt = "You are a Chief Compliance Officer writing final recommendation rationales for client files."
        
        try:
            justification = await llm_client.generate_response(prompt, system_prompt=system_prompt)
        except Exception as e:
            self.logger.error(f"Failed to generate justification via LLM: {e}")
            justification = f"Automated decision of {base_rec} made based on composite risk score of {risk_score}."

        self.logger.info(f"Recommendation determined: {base_rec}")
        return {
            "recommendation": base_rec,
            "recommendation_justification": justification
        }
