from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    anthropic_api_key: str
    environment: str = "development"
    radius_miles: int = 15
    provider_data_path: str = "app/data/providers.json"
    tools_config_path: str = "app/data/tools.yaml"
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 1024
    claude_max_iterations: int = 10
    prompt_template_path: str = "app/data/routing_prompt.txt"
    google_maps_key: str = ""
    google_maps_base_url: str = "https://maps.googleapis.com/maps/api/distancematrix/json"

    # Federated network data paths
    healthfirst_data_path: str = "app/data/providers_healthfirst.json"
    bayview_data_path: str = "app/data/providers_bayview.json"
    pacific_data_path: str = "app/data/providers_pacific.json"
    quickcare_data_path: str = "app/data/providers_quickcare.json"
    cityurgent_data_path: str = "app/data/providers_cityurgent.json"
    network_config_path: str = "app/core/network_config.yaml"

    allowed_origins: list = [
        "http://localhost:8501",  # local — needs port
        "https://continuum-health-chat.onrender.com"  # production — no port
    ]
    model_config = {"env_file": str(BASE_DIR / ".env")}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
