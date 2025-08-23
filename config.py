"""config.py
+---------------------------------
Production-ready configuration module powered by **Pydantic**.

Key benefits over the previous dataclass implementation:
1. Single-source-of-truth – each field defined once (removes duplicates).
2. Built-in validation & type coercion.
3. Rich `.model_dump()` / `.model_json()` for observability.
4. Environment-variable parsing with prefix support.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import BaseSettings, Field, ValidationError, field_validator

# NOTE: keep a minimal dependency footprint; pydantic is already used by Prefect.


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Pydantic reads variables in the form `PREFECT_API_URL`, `IMAGE_REPO` …
    Values can also be overridden by `.env` file when present.
    """

    # ---------------------------------------------------------------------
    # Core runtime
    # ---------------------------------------------------------------------
    environment: str = Field("development", description="Runtime environment switch: development/staging/production")
    log_level: str = Field("INFO", description="Root log level")

    # ---------------------------------------------------------------------
    # Prefect & deployment
    # ---------------------------------------------------------------------
    prefect_api_url: str = Field("http://172.31.0.55:4200/api", alias="PREFECT_API_URL")
    work_pool_name: str = Field("my-docker-pool2", alias="WORK_POOL_NAME")

    # ---------------------------------------------------------------------
    # Docker build / image
    # ---------------------------------------------------------------------
    image_repo: str = Field("ghcr.io/samples28/cicd-example", alias="IMAGE_REPO")
    image_tag: Optional[str] = Field(default=None, alias="IMAGE_TAG")

    # ---------------------------------------------------------------------
    # Scheduling / timeouts
    # ---------------------------------------------------------------------
    schedule_interval: int = Field(3600, ge=60, description="Default schedule interval in seconds")
    api_timeout: int = Field(300, gt=0, alias="API_TIMEOUT")
    deployment_timeout: int = Field(60, gt=0, alias="DEPLOYMENT_TIMEOUT")

    # ---------------------------------------------------------------------
    # Feature flags
    # ---------------------------------------------------------------------
    deploy_mode: bool = Field(False, alias="DEPLOY_MODE")

    # ------------------------------------------------------------------
    # Derived helpers (computed properties)
    # ------------------------------------------------------------------
    @property
    def full_image_name(self) -> str:
        """Return repo:tag, if tag provided, else repo."""

        return f"{self.image_repo}:{self.image_tag}" if self.image_tag else self.image_repo

    @property
    def is_container_env(self) -> bool:  # noqa: D401
        """Detect if running inside Docker container."""

        return os.path.exists("/.dockerenv")

    @property
    def is_production(self) -> bool:  # noqa: D401
        """Quick production check."""

        return self.environment.lower() == "production"

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:  # noqa: D401, N805
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        v_up = v.upper()
        if v_up not in allowed:
            raise ValueError(f"Invalid log level: {v}. Allowed: {allowed}")
        return v_up

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        """Return a JSON-serialisable overview useful for diagnostics."""

        return {
            **self.model_dump(),
            "full_image_name": self.full_image_name,
            "is_container_env": self.is_container_env,
            "is_production": self.is_production,
        }

    def apply_prefect_env(self) -> None:
        """Export pref-required env vars so Prefect client picks them up."""

        os.environ["PREFECT_API_URL"] = self.prefect_api_url
        os.environ["PREFECT_LOGGING_LEVEL"] = self.log_level


# Singleton accessor --------------------------------------------------------


@lru_cache
def get_settings() -> Settings:  # noqa: D401
    """Return a cached Settings instance."""

    try:
        settings = Settings()  # type: ignore[call-arg]
        settings.apply_prefect_env()
        return settings
    except ValidationError as exc:  # pragma: no cover
        # Fail-fast – misconfiguration at import time is better than runtime errors.
        raise RuntimeError(f"Configuration validation failed: {exc.errors()}") from exc


# create a module-level alias for compatibility with legacy code
settings = get_settings()  # noqa: N816