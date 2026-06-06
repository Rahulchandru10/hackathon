import pytest
from backend.agents.entity_resolution import EntityResolutionAgent
from backend.workflow.state import ScreeningState

@pytest.mark.asyncio
async def test_entity_resolution_no_metadata():
    agent = EntityResolutionAgent()
    
    # State with name only
    state: ScreeningState = {
        "resolved_entity": {
            "name": "Acme Corp",
            "entity_type": "Unknown",
            "country": "Unknown",
            "website": "",
            "registration_number": ""
        }
    }
    
    res = await agent.run(state)
    assert res["resolved_entity"]["resolution_match_type"] == "Partial Match"
    assert res["resolved_entity"]["resolution_confidence"] == 0.5
