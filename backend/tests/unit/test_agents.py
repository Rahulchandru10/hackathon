import pytest
from backend.agents.entity_intake import EntityIntakeAgent
from backend.agents.search_query import SearchQueryAgent
from backend.agents.timeline import TimelineAgent
from backend.workflow.state import ScreeningState
from backend.models.entity import EntityIntake

@pytest.mark.asyncio
async def test_entity_intake_warning_name_only():
    agent = EntityIntakeAgent()
    entity = EntityIntake(name="Test Name")
    
    state: ScreeningState = {
        "entity_input": entity
    }
    
    res = await agent.run(state)
    assert "Limited entity context may increase false positives." in res["warnings"]

@pytest.mark.asyncio
async def test_search_query_generation():
    agent = SearchQueryAgent()
    
    state: ScreeningState = {
        "resolved_entity": {
            "name": "Jane Doe",
            "aliases": ["J. Doe"]
        }
    }
    
    res = await agent.run(state)
    assert len(res["search_queries"]) > 0
    assert any("Jane Doe" in q for q in res["search_queries"])

@pytest.mark.asyncio
async def test_timeline_sorting():
    agent = TimelineAgent()
    
    state: ScreeningState = {
        "filtered_events": [
            {"detected_date": "2026-05-10", "event_type": "Enforcement"},
            {"detected_date": "2024-01-15", "event_type": "Charges"},
            {"detected_date": "2025-11-20", "event_type": "Arrest"}
        ]
    }
    
    res = await agent.run(state)
    timeline = res["timeline"]
    assert len(timeline) == 3
    assert timeline[0]["date"] == "2024-01-15"
    assert timeline[1]["date"] == "2025-11-20"
    assert timeline[2]["date"] == "2026-05-10"
