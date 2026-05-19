import httpx
from math import radians, sin, cos, sqrt, atan2

from app.core.config import get_settings
from app.models.geo import DistanceMatrixRequest, DistanceMatrixResponse


class GeoService:
    """
    Calculates drive time between patient and provider
    using Google Distance Matrix API.

    Requires GOOGLE_MAPS_KEY in .env.
    Falls back to Haversine when key not configured.
    Production: factors real traffic via departure_time=now.
    """

    def __init__(self):
        self._settings = get_settings()

    async def drive_time_minutes(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float
    ) -> float:
        """
        Public — returns drive time in minutes between two coordinates.
        Google API when key configured, Haversine fallback otherwise.
        """
        if not self._settings.google_maps_key:
            return self._haversine_fallback(
                origin_lat, origin_lng,
                dest_lat, dest_lng
            )
        result = await self.__call_google_api(
            origin_lat, origin_lng,
            dest_lat, dest_lng
        )
        return result.drive_time_minutes

    async def __call_google_api(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float
    ) -> DistanceMatrixResponse:
        """Private — calls Google Distance Matrix API."""
        request = DistanceMatrixRequest.from_coordinates(
            origin_lat, origin_lng,
            dest_lat, dest_lng,
            self._settings.google_maps_key
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._settings.google_maps_base_url,
                params=request.model_dump()
            )
            data = response.json()
            element = data["rows"][0]["elements"][0]
            return DistanceMatrixResponse(
                drive_time_seconds=element["duration"]["value"],
                drive_time_minutes=round(element["duration"]["value"] / 60, 1),
                distance_meters=element["distance"]["value"],
                status=element["status"]
            )

    def _haversine_fallback(
        self,
        lat1: float, lng1: float,
        lat2: float, lng2: float
    ) -> float:
        """
        Protected — Haversine fallback when API key not configured.
        """
        R = 3958.8
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat, dlng = lat2 - lat1, lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        return round(2 * R * atan2(sqrt(a), sqrt(1-a)), 2)