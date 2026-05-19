from abc import ABC, abstractmethod
from app.models.patient import PatientSearchRequest


class IToolHandler(ABC):
    """
    Base contract for all Claude tool handlers.
    One handler, one responsibility, one tool.
    """

    @abstractmethod
    def execute(self, tool_input: dict, request: PatientSearchRequest) -> str:
        """Execute tool logic and return result string for Claude."""
        ...