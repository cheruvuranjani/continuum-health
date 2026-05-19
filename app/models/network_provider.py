from dataclasses import dataclass, field


@dataclass
class NetworkProvider:
    """
    Represents a provider result tagged with its health system network.
    Used by FederatedSlotRepository to track which FHIR endpoint
    each result came from.

    Production: hydrated from GCP Healthcare API response,
    tagged with the originating EHR system identifier.
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
    def from_dict(
        cls,
        data: dict,
        drive_time: float,
        network: str
    ) -> "NetworkProvider":
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