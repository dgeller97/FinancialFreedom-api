from __future__ import annotations

from litestar import Litestar, Router
from litestar.config.cors import CORSConfig

from .config import settings
from .dependencies import dependencies
from .routes import route_handlers

api_router = Router(path=settings.api_prefix, route_handlers=route_handlers)

app = Litestar(
    route_handlers=[api_router],
    dependencies=dependencies,
    debug=settings.debug,
    cors_config=CORSConfig(
        allow_origins=list(settings.allowed_origins),
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_methods=["*"],
        allow_headers=["*"],
    ),
)
