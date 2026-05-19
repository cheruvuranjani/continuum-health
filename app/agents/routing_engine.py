import asyncio
import time
import yaml
from pathlib import Path

import anthropic
from anthropic.types import Message, MessageParam

from app.interfaces.routing_engine import IRoutingEngine
from app.interfaces.pharmacy_locator import IPharmacyLocator
from app.models.patient import PatientSearchRequest
from app.models.provider import RouteResponse, RouteState
from app.repository.federated_slot_repository import FederatedSlotRepository
from app.services.network_resolver import NetworkResolver
from app.core.config import get_settings
from app.core.cache import InMemoryCache
from app.agents.slot_agent import SlotAgent
from app.agents.urgent_care_agent import UrgentCareAgent
from app.agents.pharmacy_agent import PharmacyAgent


class RoutingEngine(IRoutingEngine):
    """
    Agentic routing engine powered by Claude tool_use.

    Insurance plan resolves the provider network via NetworkResolver.
    Claude then autonomously routes across the resolved network:
        primary care available  → route to primary care
        primary care exhausted  → escalate to urgent care index
        always                  → find nearest in-network pharmacy

    Agentic because: Claude decides the pathway — no hardcoded routing rules.

    Production path: Vertex AI (Gemini 2.0 Flash) for sub-second
    patient-intent matching within GCP's HIPAA-aligned boundary —
    keeping PHI off third-party infrastructure end to end.
    GCP Healthcare API replaces mock FHIR fixtures.
    """

    _cache = InMemoryCache()

    def __init__(self, pharmacy_locator: IPharmacyLocator):
        self._pharmacy_locator = pharmacy_locator
        self._network_resolver = NetworkResolver()
        self._settings = get_settings()
        self._client = anthropic.Anthropic(
            api_key=self._settings.anthropic_api_key
        )

    def __get_federated_repository(
        self,
        request: PatientSearchRequest
    ) -> FederatedSlotRepository:
        """
        Private — resolves insurance plan to provider network.
        HMO → single system. PPO → multiple systems in parallel.
        """
        return self._network_resolver.resolve(request.insurance)

    def __register_handlers(
        self,
        slot_repository: FederatedSlotRepository
    ) -> dict:
        """
        Private — registers tool name to agent handler.
        New tool = new agent class + one new line here.
        """
        return {
            "get_available_slots": SlotAgent(slot_repository),
            "get_urgent_care":     UrgentCareAgent(slot_repository),
            "find_pharmacy":       PharmacyAgent(self._pharmacy_locator)
        }

    def _load_tools(self) -> list[dict]:
        """
        Protected — cache-aside pattern for tool definitions.
        Cache hit  → memory
        Cache miss → YAML → populate cache
        TTL: 1 hour. Production: swap InMemoryCache for Redis.
        """
        cache_key = "claude:tools:v1"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        tools_path = Path(self._settings.tools_config_path)
        tools = yaml.safe_load(tools_path.read_text())["tools"]
        self._cache.set(cache_key, tools, ttl_seconds=3600)
        return tools

    def _dispatch(
        self,
        tool_name: str,
        tool_input: dict,
        request: PatientSearchRequest,
        handlers: dict
    ) -> str:
        """Protected — O(1) dict lookup routes tool call to correct handler."""
        handler = handlers.get(tool_name)
        if not handler:
            return f"Unknown tool: {tool_name}"
        return handler.execute(tool_input, request)

    def _build_prompt(self, request: PatientSearchRequest) -> str:
        """Protected — loads prompt template and injects request values."""
        template = Path(self._settings.prompt_template_path).read_text()
        return template.format(
            specialty=request.specialty,
            lat=request.lat,
            lng=request.lng,
            insurance=request.insurance or "not provided",
            radius_miles=request.radius_miles
        )

    def _call_claude(self, messages: list[MessageParam]) -> Message:
        """
        Protected — single place for all Claude API calls.
        Model and token limits are config driven.
        Production: Vertex AI (Gemini 2.0 Flash).
        """
        return self._client.messages.create(
            model=self._settings.claude_model,
            max_tokens=self._settings.claude_max_tokens,
            tools=self._load_tools(),
            messages=messages
        )

    def __extract_reasoning(self, response: Message) -> str:
        """Private — extracts Claude's reasoning from response."""
        return next(
            (block.text for block in response.content if hasattr(block, "text")),
            ""
        )

    def _process_tool_calls(
        self,
        response: Message,
        request: PatientSearchRequest,
        state: RouteState,
        handlers: dict,
        slot_repository: FederatedSlotRepository
    ) -> list[dict]:
        """
        Protected — processes all tool calls in a single Claude response.
        Updates RouteState as each tool returns results.
        """
        tool_results = []

        for block in response.content:
            if block.type != "tool_use":
                continue

            result = self._dispatch(
                block.name, block.input, request, handlers
            )
            self.__update_state(
                block.name, result, request, state, slot_repository
            )

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result
            })

        return tool_results

    def __update_state(
        self,
        tool_name: str,
        result: str,
        request: PatientSearchRequest,
        state: RouteState,
        slot_repository: FederatedSlotRepository
    ) -> None:
        """Private — updates RouteState after each tool call."""
        match tool_name:
            case "get_available_slots" if "Found" in result:
                state.primary_care = asyncio.run(
                    slot_repository.get_slots(
                        request.specialty,
                        request.lat,
                        request.lng,
                        request.radius_miles
                    )
                )

            case "get_urgent_care" if "Found" in result:
                from dataclasses import asdict
                urgent = asyncio.run(
                    slot_repository.get_urgent_care(
                        request.lat,request.lng)
                )
                state.urgent_care = [asdict(u) for u in urgent]

            case "find_pharmacy":
                pharmacy_result = self._pharmacy_locator.find_nearest(
                    request.lat, request.lng, request.insurance
                )
                if pharmacy_result.found:
                    state.pharmacy = pharmacy_result.pharmacy.model_dump()

            case _:
                pass

    def __build_response(
        self,
        state: RouteState,
        start_time: float
    ) -> RouteResponse:
        """Private — builds final RouteResponse from resolved RouteState."""
        return RouteResponse(
            resolved=state.resolved,
            mttr_seconds=round(time.time() - start_time, 2),
            primary_care=state.primary_care or None,
            urgent_care=state.urgent_care or None,
            pharmacy=state.pharmacy or None,
            agent_reasoning=state.agent_reasoning
        )

    def route(self, request: PatientSearchRequest) -> RouteResponse:
        """
        Public — entry point for the agentic routing loop.

        Resolves insurance → provider network → Claude tool_use loop.
        MTTR measured from first call to full resolution.

        for/else pattern:
            break → Claude resolved successfully
            else  → max iterations exhausted, return unresolved
        """
        start_time = time.time()

        slot_repository = self.__get_federated_repository(request)
        handlers = self.__register_handlers(slot_repository)

        messages: list[MessageParam] = [
            {"role": "user", "content": self._build_prompt(request)}
        ]
        state = RouteState()

        for _ in range(self._settings.claude_max_iterations):
            response = self._call_claude(messages)
            state.agent_reasoning = self.__extract_reasoning(response)

            if response.stop_reason == "end_turn":
                state.resolved = True
                break

            if response.stop_reason == "tool_use":
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                tool_results = self._process_tool_calls(
                    response, request, state, handlers, slot_repository
                )
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

        else:
            state.agent_reasoning = (
                f"Routing unresolved after "
                f"{self._settings.claude_max_iterations} iterations. "
                f"Patient may need manual triage."
            )

        return self.__build_response(state, start_time)
