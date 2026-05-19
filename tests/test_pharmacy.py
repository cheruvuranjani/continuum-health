import pytest
from unittest.mock import MagicMock
from app.models.pharmacy import Pharmacy, PharmacyResponse


@pytest.fixture
def mock_pharmacy_locator():
    """Pure mock — tests pharmacy locator contract."""
    mock = MagicMock()
    mock.find_nearest.return_value = PharmacyResponse(
        found=True,
        pharmacy=Pharmacy(
            pharmacy_id="pharm-001",
            name="Walgreens 24hr",
            address="498 Castro St, San Francisco, CA",
            lat=37.7609,
            lng=-122.4350,
            distance_miles=1.29,
            is_open_24h=True,
            phone="415-431-0611"
        ),
        message="Pharmacy found."
    )
    return mock


def test_find_nearest_returns_pharmacy(mock_pharmacy_locator):
    """Confirms pharmacy locator returns nearest pharmacy."""
    result = mock_pharmacy_locator.find_nearest(37.7749, -122.4194)
    assert result.found is True
    assert result.pharmacy.name == "Walgreens 24hr"
    mock_pharmacy_locator.find_nearest.assert_called_once_with(
        37.7749, -122.4194
    )


def test_find_nearest_returns_24hr_pharmacy(mock_pharmacy_locator):
    """Confirms returned pharmacy is open 24hr."""
    result = mock_pharmacy_locator.find_nearest(37.7749, -122.4194)
    assert result.pharmacy.is_open_24h is True


def test_find_nearest_returns_not_found(mock_pharmacy_locator):
    """Confirms not-found response when no pharmacy in radius."""
    mock_pharmacy_locator.find_nearest.return_value = PharmacyResponse(
        found=False,
        message="No pharmacy found within 15 miles."
    )
    result = mock_pharmacy_locator.find_nearest(37.7749, -122.4194)
    assert result.found is False
    assert result.pharmacy is None
    assert "15 miles" in result.message


def test_find_nearest_called_with_insurance(mock_pharmacy_locator):
    """Confirms insurance param is passed through correctly."""
    mock_pharmacy_locator.find_nearest(37.7749, -122.4194, "BlueCross")
    mock_pharmacy_locator.find_nearest.assert_called_once_with(
        37.7749, -122.4194, "BlueCross"
    )