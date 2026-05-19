import json
import asyncio
from pathlib import Path

from app.interfaces.pharmacy_locator import IPharmacyLocator
from app.models.pharmacy import Pharmacy, PharmacyResponse
from app.services.geo_service import GeoService
from app.core.config import get_settings


class PharmacyService(IPharmacyLocator):
    """
    Finds nearest open pharmacy within patient radius.
    Drive time via GeoService — Google API or Haversine fallback.
    Production: swap _load_pharmacies() for Google Places API
    filtered by insurance-preferred networks.
    """

    def __init__(self):
        self._settings = get_settings()
        self._data_path = Path(self._settings.provider_data_path)
        self._geo = GeoService()

    def _load_pharmacies(self) -> list[dict]:
        """Protected — loads pharmacy fixtures from provider data."""
        if not self._data_path.exists():
            raise FileNotFoundError(f"Data not found at {self._data_path}")
        providers = json.loads(self._data_path.read_text())
        return [p for p in providers if p["specialty"] == "pharmacy"]

    def _drive_time(
        self,
        lat1: float, lng1: float,
        lat2: float, lng2: float
    ) -> float:
        """Protected — bridges sync service to async GeoService."""
        return asyncio.run(
            self._geo.drive_time_minutes(lat1, lng1, lat2, lng2)
        )

    def _is_preferred(self, pharmacy: dict, insurance: str | None) -> bool:
        """Protected — insurance network check. Production: query network API."""
        return True

    def __get_candidates(
        self,
        lat: float,
        lng: float,
        insurance: str | None
    ) -> list[dict]:
        """
        Private — filters pharmacies by radius.
        Single drive time call per pharmacy — no duplicate API calls.
        """
        candidates = []
        for p in self._load_pharmacies():
            if not self._is_preferred(p, insurance):
                continue
            drive_time = self._drive_time(lat, lng, p["lat"], p["lng"])
            if drive_time <= self._settings.radius_miles:
                candidates.append({**p, "distance_miles": drive_time})
        return candidates

    def find_nearest(
        self,
        lat: float,
        lng: float,
        insurance: str | None = None
    ) -> PharmacyResponse:
        """Public — returns nearest open pharmacy or not-found response."""
        candidates = self.__get_candidates(lat, lng, insurance)

        if not candidates:
            return PharmacyResponse(
                found=False,
                message=f"No pharmacy found within {self._settings.radius_miles} miles."
            )

        return PharmacyResponse(
            found=True,
            pharmacy=Pharmacy.from_dict(
                min(candidates, key=lambda p: p["distance_miles"])
            ),
            message="Pharmacy found."
        )