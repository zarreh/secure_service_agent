from functools import lru_cache

from pydantic_settings import SettingsConfigDict
from zarreh_agentkit.settings import AgentSettings


class Settings(AgentSettings):
    """Application configuration, sourced from the environment."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SECUREAGENT_", extra="ignore")

    langsmith_project: str = "secure-service-agent"

    # A customer message is a sentence or two; a large body is an attack, not a request.
    max_request_body_bytes: int = 4_096


@lru_cache
def get_settings() -> Settings:
    return Settings()
