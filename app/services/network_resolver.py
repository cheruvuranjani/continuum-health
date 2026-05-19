import yaml
from pathlib import Path

from app.core.config import get_settings
from app.core.cache import InMemoryCache
from app.repository.fhir_slot_repository import FHIRSlotRepository
from app.repository.federated_slot_repository import FederatedSlotRepository


class NetworkResolver:
    """
    Config-driven insurance network resolution.

    Resolves a patient's insurance plan to the correct provider
    network by reading from network_config.yaml.

    Adding a new insurance plan = one new entry in network_config.yaml.
    Zero code changes, zero global state, fully debuggable.

    Production path: YAML remains the source of truth for network config.
    If runtime plan updates without redeployment are needed,
    back with PostgreSQL insurance_networks table + Redis cache-aside.
    """

    _cache = InMemoryCache()

    def __init__(self):
        self._settings = get_settings()

    def __load_config(self) -> dict:
        """Private — loads network config with cache-aside pattern."""
        cache_key = "continuum:networks:v1"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        config_path = Path(self._settings.network_config_path)
        config = yaml.safe_load(config_path.read_text())["networks"]
        self._cache.set(cache_key, config, ttl_seconds=3600)
        return config

    def __build_repository(self, config: dict) -> FederatedSlotRepository:
        """Private — builds repository from network config."""
        sources = [
            FHIRSlotRepository(s["path"], s["network"])
            for s in config["sources"]
        ]
        return FederatedSlotRepository(sources)

    def resolve(self, insurance: str | None) -> FederatedSlotRepository:
        """
        Public — resolves insurance plan to provider network.
        Falls back to open network if plan not found.
        Case-insensitive — matches how patients enter plan names.
        """
        config = self.__load_config()
        plan = insurance.lower().strip() if insurance else "uninsured"
        network_config = config.get(plan) or config["uninsured"]
        return self.__build_repository(network_config)