import asyncio
from itertools import chain

from app.interfaces.slot_repository import ISlotRepository
from app.models.provider import Provider
from app.models.network_provider import NetworkProvider
from app.repository.fhir_slot_repository import FHIRSlotRepository


class FederatedSlotRepository(ISlotRepository):
    """
    Queries multiple independent FHIR endpoints in parallel.
    The routing engine never knows how many health systems
    are in the federation.

    Adding a new health system = one new FHIRSlotRepository instance.
    Zero changes to the routing engine above this layer.

    Production: each FHIRSlotRepository connects to a real
    GCP Healthcare API endpoint, not mock JSON.
    """

    def __init__(self, sources: list[FHIRSlotRepository]):
        self._sources = sources

    async def get_slots(
        self,
        specialty: str,
        lat: float,
        lng: float,
        radius_miles: int = 15
    ) -> list[Provider]:
        """
        Public async — queries all health systems in parallel.
        Merges results and sorts by drive time across all networks.
        If one source fails, others still return — no single point of failure.
        """
        tasks = [
            source.get_slots(specialty, lat, lng, radius_miles)
            for source in self._sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_providers = list(chain.from_iterable(
            r for r in results if isinstance(r, list)
        ))

        return sorted(all_providers, key=lambda p: p.distance_miles)

    async def get_urgent_care(
        self,
        lat: float,
        lng: float
    ) -> list[NetworkProvider]:
        """
        Public async — queries urgent care across all networks in parallel.
        Called when primary care slots are exhausted across the federation.
        """
        tasks = [
            source.get_urgent_care(lat, lng)
            for source in self._sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_urgent = list(chain.from_iterable(
            r for r in results if isinstance(r, list)
        ))

        return sorted(all_urgent, key=lambda p: p.distance_miles)

    async def get_pharmacies(
        self,
        lat: float,
        lng: float
    ) -> list[NetworkProvider]:
        """
        Public async — queries in-network pharmacies across all sources.
        Insurance plan determines which networks are in the federation.
        """
        tasks = [
            source.get_pharmacies(lat, lng)
            for source in self._sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_pharmacies = list(chain.from_iterable(
            r for r in results if isinstance(r, list)
        ))

        return sorted(all_pharmacies, key=lambda p: p.distance_miles)