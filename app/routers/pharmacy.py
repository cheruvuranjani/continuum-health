from fastapi import APIRouter, Depends, HTTPException

from app.interfaces.pharmacy_locator import IPharmacyLocator
from app.models.pharmacy import PharmacyResponse
from app.services.pharmacy_service import PharmacyService

router = APIRouter(tags=["pharmacy"])


def get_pharmacy_locator() -> IPharmacyLocator:
    """Dependency injection — swap PharmacyService for Google Places in production."""
    return PharmacyService()


@router.get("/pharmacy", response_model=PharmacyResponse)
def find_pharmacy(
    lat: float,
    lng: float,
    insurance: str | None = None,
    locator: IPharmacyLocator = Depends(get_pharmacy_locator)
) -> PharmacyResponse:
    """
    Find nearest open pharmacy within patient radius.
    Filters by insurance network and 24hr availability.
    """
    result = locator.find_nearest(lat, lng, insurance)

    if not result.found:
        raise HTTPException(
            status_code=404,
            detail=result.message
        )

    return result