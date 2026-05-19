import asyncio
from app.agents.base import IToolHandler
from app.interfaces.slot_repository import ISlotRepository
from app.models.patient import PatientSearchRequest


class SlotAgent(IToolHandler):
    """
    Handles get_available_slots tool call.
    Fetches primary care providers within patient radius.
    """

    def __init__(self, slot_repository: ISlotRepository):
        self._repo = slot_repository

    def execute(self, tool_input: dict, request: PatientSearchRequest) -> str:
        providers = asyncio.run(
            self._repo.get_slots(
                specialty=tool_input.get("specialty", request.specialty),
                lat=request.lat,
                lng=request.lng,
                radius_miles=tool_input.get("radius_miles", request.radius_miles)
            )
        )

        if not providers:
            return "No primary care slots available within radius."

        summary = ", ".join(
            f"{p.name} ({p.distance_miles}mi)" for p in providers
        )
        return f"Found {len(providers)} providers: {summary}"