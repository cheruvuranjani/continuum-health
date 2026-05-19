import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.geo_service import GeoService


@pytest.mark.asyncio
async def test_drive_time_uses_haversine_when_no_key(monkeypatch):
    """Confirms Haversine fallback when no API key configured."""
    monkeypatch.setattr("app.services.geo_service.get_settings", lambda: MagicMock(
        google_maps_key="",
        google_maps_base_url=""
    ))
    service = GeoService()
    result = await service.drive_time_minutes(37.77, -122.41, 37.78, -122.42)
    assert isinstance(result, float)
    assert result > 0


@pytest.mark.asyncio
async def test_drive_time_calls_google_api_when_key_configured(monkeypatch):
    """Confirms Google API is called when key is present."""
    monkeypatch.setattr("app.services.geo_service.get_settings", lambda: MagicMock(
        google_maps_key="fake-key",
        google_maps_base_url="https://maps.googleapis.com/maps/api/distancematrix/json"
    ))
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "rows": [{
            "elements": [{
                "duration": {"value": 900},
                "distance": {"value": 5000},
                "status": "OK"
            }]
        }]
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        service = GeoService()
        result = await service.drive_time_minutes(37.77, -122.41, 37.78, -122.42)
        assert result == 15.0


def test_haversine_fallback_returns_positive_distance():
    """Confirms Haversine returns sensible distance between two SF coordinates."""
    service = GeoService()
    result = service._haversine_fallback(37.77, -122.41, 37.78, -122.42)
    assert result > 0
    assert result < 5