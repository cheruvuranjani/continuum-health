from abc import ABC, abstractmethod
from app.models.pharmacy import PharmacyResponse
from typing import Optional


class IPharmacyLocator(ABC):
    """
    Abstracts pharmacy lookup from its data source.

    In production this hits Google Places API filtered by
    insurance-preferred networks. Current implementation
    uses mock fixtures to keep the demo self-contained.
    """

    @abstractmethod
    def find_nearest(
        self,
        lat: float,
        lng: float,
        insurance: Optional[str] = None
    ) -> PharmacyResponse:
        """
        Returns the nearest open pharmacy within radius.
        Insurance filter ensures in-network results only.
        """
        ...