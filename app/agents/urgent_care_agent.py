import asyncio
from app.agents.base import IToolHandler
from app.interfaces.slot_repository import ISlotRepository
from app.models.patient import PatientSearchRequest


class UrgentCareAgent(IToolHandler):
    """
    Handles get_urgent_care tool call.
    Fallback path — only triggered when primary care slots are exhausted.
    """

    def __init__(self, slot_repository: ISlotRepository):
        self._repo = slot_repository

    def execute(self, tool_input: dict, request: PatientSearchRequest) -> str:
        urgent = asyncio.run(
            self._repo.get_urgent_care(request.lat, request.lng)
        )

        if not urgent:
            return "No urgent care found within radius."

        summary = ", ".join(
            f"{u.name} ({u.distance_miles}mi)" for u in urgent
        )
        return f"Found {len(urgent)} urgent care options: {summary}"