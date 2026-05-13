from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _bool(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Load from environment (optionally via .env in the current working directory)."""

    base_url: str
    username: str
    password: str
    auth_mode: str  # "jwt" | "session"
    verify_ssl: bool
    jwt_duration: int | None
    connect_timeout: float
    read_timeout: float

    @staticmethod
    def load() -> "Settings":
        load_dotenv()
        base = (os.getenv("SDWAN_BASE_URL") or os.getenv("SDWAN_MANAGER") or "").strip().rstrip("/")
        if not base:
            raise ValueError("Set SDWAN_BASE_URL (preferred) or SDWAN_MANAGER to the Manager base URL")
        user = os.environ["SDWAN_USERNAME"]
        password = os.environ["SDWAN_PASSWORD"]
        mode = os.getenv("SDWAN_AUTH_MODE", "jwt").strip().lower()
        if mode not in {"jwt", "session", "auto"}:
            raise ValueError("SDWAN_AUTH_MODE must be 'jwt', 'session', or 'auto'")
        dur_raw = os.getenv("SDWAN_JWT_DURATION", "").strip()
        jwt_duration = int(dur_raw) if dur_raw else None
        return Settings(
            base_url=base,
            username=user,
            password=password,
            auth_mode=mode,
            verify_ssl=_bool("SDWAN_VERIFY_SSL", "true"),
            jwt_duration=jwt_duration,
            connect_timeout=float(os.getenv("SDWAN_CONNECT_TIMEOUT", "30")),
            read_timeout=float(os.getenv("SDWAN_READ_TIMEOUT", "120")),
        )
