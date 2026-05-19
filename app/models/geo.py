from pydantic import BaseModel


class DistanceMatrixRequest(BaseModel):
    """
    Google Distance Matrix API request payload.
    Keeps API params typed and validated — out of service logic.
    """
    origins: str
    destinations: str
    mode: str = "driving"
    departure_time: str = "now"
    key: str

    @classmethod
    def from_coordinates(
        cls,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        api_key: str
    ) -> "DistanceMatrixRequest":
        """Factory — builds request from raw coordinates."""
        return cls(
            origins=f"{origin_lat},{origin_lng}",
            destinations=f"{dest_lat},{dest_lng}",
            key=api_key
        )


class DistanceMatrixResponse(BaseModel):
    """
    Parsed response from Google Distance Matrix API.
    drive_time_minutes is what the routing engine uses for sorting.
    """
    drive_time_minutes: float
    drive_time_seconds: int
    distance_meters: int
    status: str = "OK"