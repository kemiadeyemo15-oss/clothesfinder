"""Runtime configuration. Everything that differs between dev and prod is here.

Dev (no env set) → in-memory repo, stub embedder, seed inventory. Runs with
zero keys. Set the env vars below to flip each subsystem to its real impl
independently — you don't have to switch them all at once.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CF_", extra="ignore")

    # --- which implementation of each subsystem to use ---
    repo_backend: Literal["memory", "postgres"] = "memory"
    embedder: Literal["stub", "lykdat"] = "stub"
    inventory: Literal["seed", "shopping_api"] = "seed"
    query_parser: Literal["rules", "llm"] = "rules"

    # --- Postgres (only read when repo_backend=postgres) ---
    database_url: str = "postgresql+asyncpg://clothesfinder:clothesfinder@localhost:5432/clothesfinder"

    # --- external services (only read when selected above) ---
    lykdat_api_key: str = ""
    lykdat_base_url: str = "https://api.lykdat.com/v1"
    shopping_api_key: str = ""
    shopping_api_url: str = ""          # e.g. a SerpApi-compatible endpoint
    llm_api_key: str = ""
    llm_model: str = "claude-3-5-haiku"

    embedding_dim: int = 512            # must match the model you wire in

    @field_validator("database_url")
    @classmethod
    def _async_driver(cls, v: str) -> str:
        # Managed hosts (Render/Railway) inject a plain postgres:// URL; the
        # async engine needs the asyncpg driver. Normalise it here.
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    # --- app ---
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    max_results: int = 24
    trust_weight: float = 0.15          # how much shipping/trust can move ranking
    env: Literal["dev", "prod"] = "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()
