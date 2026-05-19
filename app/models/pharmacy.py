from pydantic import BaseModel
from typing import Optional


class Pharmacy(BaseModel):
    """
    Represents a pharmacy within the patient's search radius.
    24h availability is critical — a prescription at 9pm is only
    useful if the pharmacy can fill it tonight.
    """
    pharmacy_id: str
    name: str
    address: str
    lat: float
    lng: float
    distance_miles: Optional[float] = None
    is_open_24h: bool = False           # key filter for late-night prescriptions
    phone: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Pharmacy":
        """Factory — maps raw provider dict to Pharmacy model."""
        return cls(
            pharmacy_id=data["provider_id"],
            name=data["name"],
            address=data["address"],
            lat=data["lat"],
            lng=data["lng"],
            distance_miles=data.get("distance_miles"),
            is_open_24h=data.get("is_open_24h", False),
            phone=data.get("phone")
        )


class PharmacyResponse(BaseModel):
    """Output of the pharmacy locator service."""
    found: bool
    pharmacy: Optional[Pharmacy] = None
    message: str = ""                   # human-readable status e.g. "No pharmacy found within 15 miles"

