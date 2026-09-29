from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import SettingsConfigDict
from zarreh_agentkit.settings import AgentSettings

from sentinel.store.pin_hash import FIXTURE_PEPPER


class Settings(AgentSettings):
    """Application configuration, sourced from the environment."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SENTINEL_", extra="ignore")

    langsmith_project: str = "secure-service-agent"

    policy_kb_path: str = "data/policy_clauses.json"
    accounts_db_path: str = "data/accounts.db"
    audit_db_path: str = "data/audit.db"
    checkpoint_db_path: str = "data/checkpoints.db"

    # Identity gate (D-A4-10): free attempts, then exponential backoff.
    pin_max_attempts: int = 3
    identity_db_path: str = "data/identity.db"
    # Held outside the database so a stolen accounts.db cannot be brute-forced offline.
    identity_pepper: str = FIXTURE_PEPPER

    max_request_body_bytes: int = 8_192

    @model_validator(mode="after")
    def _refuse_the_public_pepper_outside_development(self) -> "Settings":
        if self.environment not in {"development", "test"} and (
            self.identity_pepper == FIXTURE_PEPPER
        ):
            raise ValueError(
                "SENTINEL_IDENTITY_PEPPER must be set to a private value outside development"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
