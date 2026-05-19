from pydantic import BaseModel
from typing import Optional, List
from dataclasses import dataclass, field


class Slot(BaseModel):
    """Represents a single appointment slot from the FHIR layer."""
    datetime: str
    available: bool


class Provider(BaseModel):
    """A healthcare provider returned by the slot search."""
    provider_id: str
    name: str
    specialty: str
    address: str
    lat: float
    lng: float
    distance_miles: Optional[float] = None
    slots: List[Slot] = []

    @classmethod
    def from_dict(cls, data: dict, drive_time: float) -> "Provider":
        """Factory — maps raw FHIR dict to Provider model."""
        return cls(
            provider_id=data["provider_id"],
            name=data["name"],
            specialty=data["specialty"],
            address=data["address"],
            lat=data["lat"],
            lng=data["lng"],
            distance_miles=drive_time,
            slots=[Slot(**s) for s in data.get("slots", [])]
        )


class RouteResponse(BaseModel):
    """Final response returned to the patient after agentic routing."""
    resolved: bool
    mttr_seconds: float
    primary_care: Optional[List[Provider]] = None
    urgent_care: Optional[List[dict]] = None
    pharmacy: Optional[dict] = None
    agent_reasoning: str = ""

@dataclass
class RouteState:
    """
    Mutable routing state tracked across the agentic loop.
    """
    primary_care: list = field(default_factory=list)
    urgent_care: list = field(default_factory=list)
    pharmacy: dict = field(default_factory=dict)
    agent_reasoning: str = ""
    resolved: bool = False
@dataclass
class NetworkProvider:
    """
    Represents a provider result tagged with its health system network.
    Used by FederatedSlotRepository to track which FHIR endpoint
    each result came from.
    """
    provider_id: str
    name: str
    specialty: str
    address: str
    lat: float
    lng: float
    distance_miles: float
    network: str
    is_open_24h: bool = False
    phone: str = ""
    slots: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict, drive_time: float, network: str) -> "NetworkProvider":
        """Factory — maps raw FHIR dict to NetworkProvider."""
        return cls(
            provider_id=data["provider_id"],
            name=data["name"],
            specialty=data["specialty"],
            address=data["address"],
            lat=data["lat"],
            lng=data["lng"],
            distance_miles=drive_time,
            network=network,
            is_open_24h=data.get("is_open_24h", False),
            phone=data.get("phone", ""),
            slots=data.get("slots", [])
        )