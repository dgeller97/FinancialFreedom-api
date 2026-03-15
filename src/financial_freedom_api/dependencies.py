from __future__ import annotations

from typing import AsyncGenerator

from litestar.connection import Request
from litestar.di import Provide
from litestar.exceptions import HTTPException
from supabase import AsyncClient, ClientOptions, create_async_client

from .config import settings


class StatelessAsyncStorage:
    """Dummy async storage to satisfy Supabase's async GoTrue client in a stateless API."""
    
    async def get_item(self, key: str) -> str | None:
        return None

    async def set_item(self, key: str, value: str) -> None:
        pass

    async def remove_item(self, key: str) -> None:
        pass


async def provide_supabase_client(request: Request) -> AsyncGenerator[AsyncClient, None]:
    """Dependency injection to provide an authenticated Supabase client for a request."""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Bearer token")
        
    token = auth_header.split(" ", maxsplit=1)[1]
    
    # Create an async Supabase client using the settings
    # Pass our custom async storage so set_session can await it safely
    client = await create_async_client(
        settings.supabase_url,
        settings.supabase_anon_key or settings.supabase_service_role_key or "",
        options=ClientOptions(
            schema="app",
            storage=StatelessAsyncStorage()
        )
    )
    
    # Authenticate the client with the user's JWT so RLS policies apply
    await client.auth.set_session(access_token=token, refresh_token="")
    
    yield client


dependencies = {"client": Provide(provide_supabase_client)}