from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from models.state import AgentState


class BaseAgent(ABC):
    """Base class for all kitchen assistant agents"""

    @abstractmethod
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Process the current state and return updates

        Args:
            state: Current state of the workflow

        Returns:
            Dict containing updates to the state
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the agents"""
        pass

    @property
    def required_input_keys(self) -> list[str]:
        """Keys required in the state for this agents to function"""
        return ["query"]

    def validate_inputs(self, state: AgentState) -> bool:
        """Validate that all required inputs are present in the state"""
        return all(key in state for key in self.required_input_keys)