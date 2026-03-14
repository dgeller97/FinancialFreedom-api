from __future__ import annotations

from dataclasses import dataclass, field
import os

from dotenv import load_dotenv


load_dotenv(".env")
load_dotenv("env")


@dataclass(slots=True)
class Settings:
    app_name: str = "Financial Freedom API"
    api_prefix: str = "/api"
    debug: bool = os.getenv("LITESTAR_DEBUG", "true").lower() == "true"
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    database_url: str | None = os.getenv("DATABASE_URL")
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_anon_key: str | None = os.getenv("SUPABASE_ANON_KEY")
    supabase_service_role_key: str | None = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    allowed_origins: list[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "ALLOWED_ORIGINS",
                "http://localhost:3000,http://localhost:5173,http://localhost:8000,http://localhost:8080",
            ).split(",")
            if origin.strip()
        ]
    )


settings = Settings()
