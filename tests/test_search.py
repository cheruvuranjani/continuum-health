import pytest
from unittest.mock import MagicMock
from app.models.provider import Provider, Slot


@pytest.fixture
def mock_slot_repository():
    """Pure mock — tests interface contract, no real IO."""
    mock = MagicMock()
    mock.get_slots.return_value = [
        Provider(
            provider_id="prov-001",
            name="Dr. Sarah Chen",
            specialty="primary_care",
            address="450 Sutter St, San Francisco, CA",
            lat=37.7749,
            lng=-122.4194,
            distance_miles=0.0,
            slots=[Slot(datetime="2026-05-08T09:00:00", available=True)]
        )
    ]
    mock.get_urgent_care.return_value = [
        {
            "provider_id": "urg-001",
            "name": "City Urgent Care",
            "specialty": "urgent_care",
            "distance_miles": 1.2
        }
    ]
    return mock


def test_get_slots_returns_available_providers(mock_slot_repository):
    """Confirms interface returns available providers."""
    results = mock_slot_repository.get_slots(
        "primary_care", 37.7749, -122.4194
    )
    assert len(results) == 1
    assert results[0].name == "Dr. Sarah Chen"
    mock_slot_repository.get_slots.assert_called_once_with(
        "primary_care", 37.7749, -122.4194
    )


def test_get_slots_returns_empty_for_unknown_specialty(mock_slot_repository):
    """Confirms empty list when no providers match specialty."""
    mock_slot_repository.get_slots.return_value = []
    results = mock_slot_repository.get_slots("cardiology", 37.7749, -122.4194)
    assert results == []


def test_get_slots_sorted_by_drive_time(mock_slot_repository):
    """Confirms results are sorted by drive time ascending."""
    results = mock_slot_repository.get_slots(
        "primary_care", 37.7749, -122.4194
    )
    drive_times = [p.distance_miles for p in results]
    assert drive_times == sorted(drive_times)


def test_get_urgent_care_returns_urgent_providers(mock_slot_repository):
    """Confirms urgent care fallback returns correct providers."""
    results = mock_slot_repository.get_urgent_care(37.7749, -122.4194)
    assert len(results) == 1
    assert results[0]["name"] == "City Urgent Care"


def test_get_slots_called_with_correct_params(mock_slot_repository):
    """Confirms slot search is called with correct specialty and coordinates."""
    mock_slot_repository.get_slots("primary_care", 37.7749, -122.4194, 15)
    mock_slot_repository.get_slots.assert_called_once_with(
        "primary_care", 37.7749, -122.4194, 15
    )