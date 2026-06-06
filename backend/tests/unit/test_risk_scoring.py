import pytest
from backend.agents.risk_scoring import RiskScoringAgent
from backend.workflow.state import ScreeningState

@pytest.mark.asyncio
async def test_risk_scoring_low_risk():
    agent = RiskScoringAgent()
    
    # State with no adverse hits
    state: ScreeningState = {
        "filtered_events": [],
        "pep_matches": [],
        "sanctions_matches": [],
        "network_edges": []
    }
    
    res = await agent.run(state)
    assert "risk_score" in res
    assert "risk_breakdown" in res
    assert res["risk_score"] == 0
    assert res["risk_breakdown"]["overall"] == 0

@pytest.mark.asyncio
async def test_risk_scoring_sanctions_critical():
    agent = RiskScoringAgent()
    
    # State with sanctions matches
    state: ScreeningState = {
        "filtered_events": [],
        "pep_matches": [],
        "sanctions_matches": [{"confidence": 0.95}],
        "network_edges": [{"label": "SANCTIONED_BY"}]
    }
    
    res = await agent.run(state)
    assert res["risk_score"] > 40 # Sanctions trigger high scores
    assert res["risk_breakdown"]["sanctions"] == 95
