from abc import ABC, abstractmethod
from app.models.patient import PatientSearchRequest
from app.models.provider import RouteResponse


class IRoutingEngine(ABC):
    """
        Abstracts the agentic routing decision layer.

        The concrete implementation uses Claude with tool_use to decide
        whether to route to primary care or escalate to urgent care.
        Keeping this behind an interface means the LLM provider is
        swappable without touching the API layer.
        """
    @abstractmethod
    def route(self, request: PatientSearchRequest)->RouteResponse:
        """
                Core routing method — takes a patient request, returns a
                fully resolved care pathway with MTTR recorded.
                This is the method that drives the north star metric.
                """
        ...

