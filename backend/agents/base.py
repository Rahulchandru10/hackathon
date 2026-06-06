import logging
from abc import ABC, abstractmethod
from backend.workflow.state import ScreeningState
from backend.services.llm import llm_client

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"backend.agents.{self.name}")

    @abstractmethod
    async def run(self, state: ScreeningState) -> dict:
        """
        Executes the agent logic.
        Returns a dict containing fields to update in the ScreeningState.
        """
        pass
