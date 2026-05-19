from app.agents.base import IToolHandler
from app.interfaces.pharmacy_locator import IPharmacyLocator
from app.models.patient import PatientSearchRequest


class PharmacyAgent(IToolHandler):
    """
    Handles find_pharmacy tool call.
    Always called last — closes the care loop.
    24hr availability is critical for late night prescriptions.
    """

    def __init__(self, pharmacy_locator: IPharmacyLocator):
        self._locator = pharmacy_locator

    def execute(self, tool_input: dict, request: PatientSearchRequest) -> str:
        result = self._locator.find_nearest(
            request.lat,
            request.lng,
            request.insurance
        )

        if not result.found:
            return result.message

        return (
            f"Nearest pharmacy: {result.pharmacy.name} "
            f"at {result.pharmacy.address}. "
            f"24hr open: {result.pharmacy.is_open_24h}"
        )