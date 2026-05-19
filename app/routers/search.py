import asyncio

from fastapi import APIRouter, HTTPException

from app.models.patient import PatientSearchRequest
from app.models.provider import Provider
from app.services.network_resolver import NetworkResolver

router = APIRouter(tags=["search"])


@router.post("/search", response_model=list[Provider])
def search_providers(request: PatientSearchRequest) -> list[Provider]:
    """
    Search available providers within patient radius.

    Network resolved by insurance plan:
        HMO (Kaiser)    → Kaiser network only
        PPO (BlueCross) → Sutter + Stanford
        Uninsured       → all available networks

    Returns providers sorted by drive time — closest first.
    """
    repo = NetworkResolver().resolve(request.insurance)

    providers = asyncio.run(
        repo.get_slots(
            specialty=request.specialty,
            lat=request.lat,
            lng=request.lng,
            radius_miles=request.radius_miles
        )
    )

    if not providers:
        raise HTTPException(
            status_code=404,
            detail=f"No {request.specialty} providers found within {request.radius_miles} miles."
        )

    return providers