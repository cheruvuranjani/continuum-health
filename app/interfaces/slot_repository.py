from abc import ABC, abstractmethod
from app.models.provider import Provider


class ISlotRepository(ABC):


    """
        Abstracts slot retrieval from the underlying EHR system.

        Today this runs against mock JSON fixtures. When the health
        system connects their FHIR endpoint, only the concrete
        implementation changes — nothing above this layer needs to.
        """


@abstractmethod
def get_slots(self,specialty: str, lat: float, lng: float,radius_miles: int) -> list[Provider]:
    """Returns available providers within radius, sorted by distance."""
    ...


@abstractmethod
def get_urgent_care(self, lat: float, lng: float) -> list[dict]:
    """
            Called only when primary care slots = 0.
            This is the agentic failover path — not the happy path.
            """
    ...
