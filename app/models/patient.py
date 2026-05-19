from pydantic import BaseModel
from typing import Optional


class PatientSearchRequest(BaseModel):
    """
    Inbound patient search request — entry point into the Continuum routing engine.
    Equivalent to a Spring Boot @RequestBody DTO.
    """
    lat: float
    lng: float
    specialty: str
    insurance: Optional[str] = None
    radius_miles: int = 15              # default 15-mile radius per Continuum spec
    query: Optional[str] = None         # natural language input passed to Claude