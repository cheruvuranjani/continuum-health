import json
from pathlib import Path

from app.interfaces.slot_repository import ISlotRepository
from app.models.provider import Provider
from app.models.network_provider import NetworkProvider
from app.services.geo_service import GeoService
from app.core.config import get_settings


class FHIRSlotRepository(ISlotRepository):
    """
    Represents a single EHR endpoint one health system, one data source.

    Each instance is initialized with a network-specific data path,
    simulating an independent FHIR endpoint per health system.

    """

    def __init__(
        self,
        data_path: str = None,
        network_name: str = "default"
    ):
        self._settings = get_settings()
        self._data_path = Path(data_path or self._settings.provider_data_path)
        self._network_name = network_name
        self._geo = GeoService()

    def _load_providers(self) -> list[dict]:
        """Protected — loads provider fixtures from disk."""
        if not self._data_path.exists():
            raise FileNotFoundError(
                f"Provider data not found at {self._data_path}"
            )
        return json.loads(self._data_path.read_text())

    async def get_slots(
        self,
        specialty: str,
        lat: float,
        lng: float,
        radius_miles: int = 15
    ) -> list[Provider]:
        """
        Public async — available providers sorted by drive time.
        Designed for parallel execution via asyncio.gather().
        """
        providers = self._load_providers()
        results = []

        for p in providers:
            if p["specialty"] != specialty:
                continue
            if not any(s["available"] for s in p.get("slots", [])):
                continue

            drive_time = await self._geo.drive_time_minutes(
                lat, lng, p["lat"], p["lng"]
            )
            if drive_time > radius_miles:
                continue
            results.append(Provider.from_dict(p, drive_time))

        return sorted(results, key=lambda p: p.distance_miles)

    async def get_urgent_care(
        self,
        lat: float,
        lng: float
    ) -> list[NetworkProvider]:
        """
        Public async — urgent care options sorted by drive time.
        Called only when primary care slots are exhausted across
        all networks.
        """
        providers = self._load_providers()
        results = []

        for p in providers:
            if p["specialty"] != "urgent_care":
                continue

            drive_time = await self._geo.drive_time_minutes(
                lat, lng, p["lat"], p["lng"]
            )
            if drive_time > 15:
                continue
            results.append(
                NetworkProvider.from_dict(p, drive_time, self._network_name)
            )

        return sorted(results, key=lambda p: p.distance_miles)

    async def get_pharmacies(
        self,
        lat: float,
        lng: float
    ) -> list[NetworkProvider]:
        """
        Public async — in-network pharmacies sorted by drive time.
        Insurance plan determines which network's pharmacies are surfaced.
        """
        providers = self._load_providers()
        results = []

        for p in providers:
            if p["specialty"] != "pharmacy":
                continue

            drive_time = await self._geo.drive_time_minutes(
                lat, lng, p["lat"], p["lng"]
            )
            results.append(
                NetworkProvider.from_dict(p, drive_time, self._network_name)
            )

        return sorted(results, key=lambda p: p.distance_miles)