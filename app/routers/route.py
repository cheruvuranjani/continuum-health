from fastapi import APIRouter, HTTPException

from app.models.patient import PatientSearchRequest
from app.models.provider import RouteResponse
from app.agents.routing_engine import RoutingEngine
from app.services.pharmacy_service import PharmacyService
from app.services.metrics_service import metrics_service

router = APIRouter(tags=["route"])

@router.post("/route", response_model=RouteResponse)
def route_patient(request: PatientSearchRequest) -> RouteResponse:
    """
    Core Continuum endpoint — federated agentic patient routing.

    Insurance plan resolves the provider network automatically:
        HMO (Kaiser)    → routes exclusively within Kaiser network
        PPO (BlueCross) → federates across Sutter + Stanford
        Uninsured       → open network, maximum coverage

    Claude autonomously routes across the resolved network.
    MTTR tracked end to end.
    """
    engine = RoutingEngine(pharmacy_locator=PharmacyService())
    response = engine.route(request)
    metrics_service.record(response)

    if not response.resolved:
        raise HTTPException(
            status_code=503,
            detail="Unable to resolve care pathway. Patient may need manual triage."
        )

    return response