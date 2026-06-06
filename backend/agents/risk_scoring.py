from backend.agents.base import BaseAgent
from backend.workflow.state import ScreeningState

class RiskScoringAgent(BaseAgent):
    def __init__(self):
        super().__init__("risk_scoring")

    async def run(self, state: ScreeningState) -> dict:
        events = state["filtered_events"]
        peps = state["pep_matches"]
        sanctions = state["sanctions_matches"]
        network_edges = state["network_edges"]
        
        # Calculate sub-scores
        fraud_score = 0
        regulatory_score = 0
        network_score = 0
        pep_score = 0
        sanctions_score = 0
        aml_kyc_score = 0

        # Event risk calculation
        if events:
            fraud_events = [e for e in events if e["event_type"] in ["Fraud", "Bribery", "Corruption", "Insider Trading", "Tax Evasion"]]
            reg_events = [e for e in events if e["event_type"] in ["Regulatory Actions", "Litigation", "Criminal Charges", "Convictions", "Investigations"]]
            aml_events = [e for e in events if e["event_type"] in ["Money Laundering", "AML Violations", "KYC Violations", "Terror Financing", "Sanctions Violations"]]
            
            if fraud_events:
                fraud_score = int(sum(e["severity"] for e in fraud_events) / len(fraud_events))
            if reg_events:
                regulatory_score = int(sum(e["severity"] for e in reg_events) / len(reg_events))
            if aml_events:
                aml_kyc_score = int(sum(e["severity"] for e in aml_events) / len(aml_events))

        # PEP Risk (0-100 scale based on highest confidence match)
        if peps:
            pep_score = int(max(p["confidence"] for p in peps) * 100)
            
        # Sanctions Risk (100 if active, scaled by confidence)
        if sanctions:
            sanctions_score = int(max(s["confidence"] for s in sanctions) * 100)

        # Network risk (base network propagation score)
        # e.g., count connections and add indirect risk if any connected node is a Sanction or PEP
        connection_count = len(network_edges)
        has_sanctioned_neighbor = any(e["label"] == "SANCTIONED_BY" for e in network_edges)
        
        network_score = min(connection_count * 5, 40)
        if has_sanctioned_neighbor:
            network_score = min(network_score + 50, 100)

        # Overall composite weighted score
        # Sanctions is highest weight, followed by PEP and AML/Fraud
        weights = {
            "sanctions": 0.40,
            "aml_kyc": 0.20,
            "fraud": 0.15,
            "regulatory": 0.10,
            "pep": 0.10,
            "network": 0.05
        }
        
        weighted_overall = (
            (sanctions_score * weights["sanctions"]) +
            (aml_kyc_score * weights["aml_kyc"]) +
            (fraud_score * weights["fraud"]) +
            (regulatory_score * weights["regulatory"]) +
            (pep_score * weights["pep"]) +
            (network_score * weights["network"])
        )
        
        overall_score = min(max(int(weighted_overall), 0), 100)

        # Format breakdown object
        breakdown = {
            "overall": overall_score,
            "fraud": fraud_score,
            "regulatory": regulatory_score,
            "network": network_score,
            "sanctions": sanctions_score,
            "pep": pep_score,
            "aml_kyc": aml_kyc_score
        }

        self.logger.info(f"Risk Scoring completed. Overall: {overall_score}/100")
        return {
            "risk_score": overall_score,
            "risk_breakdown": breakdown
        }
