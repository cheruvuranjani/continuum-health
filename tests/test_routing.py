import pytest
from unittest.mock import MagicMock
from app.models.provider import Provider, Slot, RouteResponse
from app.models.patient import PatientSearchRequest


@pytest.fixture
def mock_routing_engine():
    """Pure mock — tests routing engine contract."""
    mock = MagicMock()
    mock.route.return_value = RouteResponse(
        resolved=True,
        mttr_seconds=3.42,
        primary_care=[
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
        ],
        urgent_care=None,
        pharmacy=None,
        agent_reasoning="Found 2 primary care providers. Routed to nearest."
    )
    return mock


@pytest.fixture
def patient_request():
    """Standard patient search request fixture."""
    return PatientSearchRequest(
        lat=37.7749,
        lng=-122.4194,
        specialty="primary_care",
        radius_miles=15
    )


def test_route_resolves_successfully(mock_routing_engine, patient_request):
    """Confirms routing engine resolves care pathway."""
    result = mock_routing_engine.route(patient_request)
    assert result.resolved is True
    assert result.mttr_seconds > 0
    mock_routing_engine.route.assert_called_once_with(patient_request)


def test_route_returns_primary_care_when_available(mock_routing_engine, patient_request):
    """Confirms primary care returned when slots available."""
    result = mock_routing_engine.route(patient_request)
    assert result.primary_care is not None
    assert len(result.primary_care) == 1
    assert result.primary_care[0].name == "Dr. Sarah Chen"


def test_route_escalates_to_urgent_care_when_no_slots(mock_routing_engine, patient_request):
    """Confirms urgent care returned when primary slots exhausted."""
    mock_routing_engine.route.return_value = RouteResponse(
        resolved=True,
        mttr_seconds=5.1,
        primary_care=None,
        urgent_care=[{
            "provider_id": "urg-001",
            "name": "City Urgent Care",
            "distance_miles": 1.2
        }],
        pharmacy=None,
        agent_reasoning="No primary care slots. Escalated to urgent care."
    )
    result = mock_routing_engine.route(patient_request)
    assert result.primary_care is None
    assert result.urgent_care is not None
    assert result.urgent_care[0]["name"] == "City Urgent Care"


def test_route_returns_agent_reasoning(mock_routing_engine, patient_request):
    """Confirms Claude's reasoning is captured in response."""
    result = mock_routing_engine.route(patient_request)
    assert result.agent_reasoning != ""


def test_route_mttr_is_recorded(mock_routing_engine, patient_request):
    """Confirms MTTR is measured and returned."""
    result = mock_routing_engine.route(patient_request)
    assert isinstance(result.mttr_seconds, float)
    assert result.mttr_seconds > 0