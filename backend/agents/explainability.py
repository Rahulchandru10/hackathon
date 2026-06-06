from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState
from backend.services.llm import llm_client

class ExplainabilityAgent(BaseAgent):
    def __init__(self):
        super().__init__("explainability")

    async def run(self, state: ScreeningState) -> dict:
        resolved = state["resolved_entity"]
        risk_score = state["risk_score"]
        breakdown = state["risk_breakdown"]
        events = state["filtered_events"]
        peps = state["pep_matches"]
        sanctions = state["sanctions_matches"]
        
        # Build explanation prompt
        prompt = f"""
        Generate a detailed Explainability Report explaining the risk calculation for:
        Target Entity Name: {resolved['name']}
        Overall Risk Score: {risk_score}/100
        
        Risk Breakdown details:
        - Fraud & Adverse Media: {breakdown.get('fraud', 0)}
        - Regulatory Enforcement: {breakdown.get('regulatory', 0)}
        - PEP Exposure: {breakdown.get('pep', 0)}
        - Sanctions Watchlist match: {breakdown.get('sanctions', 0)}
        - Network/Contagion Risk: {breakdown.get('network', 0)}
        - AML/KYC Risk: {breakdown.get('aml_kyc', 0)}

        Key Evidence:
        - Number of Adverse Articles: {len(state.get('validated_articles', []))}
        - Number of Extracted Events: {len(events)}
        - PEP Matches: {len(peps)}
        - Sanctions Matches: {len(sanctions)}

        Generate a clear, structured compliance report in Markdown explaining:
        1. Executive Risk Summary
        2. Drivers of High/Low Risk scores (identify exactly which parameters pushed the score up or down)
        3. Auditability note (comment on the credibility of sources and the confidence of entity resolution matches)
        """
        
        system_prompt = "You are an AI Explainability Engine. Explain risk decisions clearly and objectively to compliance analysts."
        
        try:
            report = await llm_client.generate_response(prompt, system_prompt=system_prompt)
        except Exception as e:
            self.logger.error(f"Failed to generate explainability report: {e}")
            report = f"# Risk Score Explanation\n\nComposite score: {risk_score}/100.\nBreakdown: {breakdown}"

        self.logger.info("Explainability report generated.")
        return {"explainability_report": report}
