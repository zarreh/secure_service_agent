from functools import lru_cache

from pydantic_settings import SettingsConfigDict
from zarreh_agentkit.settings import AgentSettings


class Settings(AgentSettings):
    """Application configuration, sourced from the environment."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SENTINEL_", extra="ignore")

    langsmith_project: str = "secure-service-agent"

    policy_kb_path: str = "data/policy_clauses.json"
    accounts_db_path: str = "data/accounts.db"
    audit_db_path: str = "data/audit.db"
    checkpoint_db_path: str = "data/checkpoints.db"

    # docs/PLAN.md Phase 2 — identity gate lockout policy.
    pin_max_attempts: int = 3

    max_request_body_bytes: int = 8_192


@lru_cache
def get_settings() -> Settings:
    return Settings()
