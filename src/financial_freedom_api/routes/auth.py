from __future__ import annotations

from litestar import get, post
from litestar.connection import Request

from ..dtos import AuthRequestDTO, AuthResponseDTO, UserDTO
from ..supabase_auth import supabase_auth_service


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization")
    if not header or not header.lower().startswith("bearer "):
        return None
    return header.split(" ", maxsplit=1)[1]


@post("/auth/login")
async def login(data: AuthRequestDTO) -> AuthResponseDTO:
    return await supabase_auth_service.login(data)


@post("/auth/signup")
async def signup(data: AuthRequestDTO) -> AuthResponseDTO:
    return await supabase_auth_service.signup(data)


@post("/auth/logout")
async def logout(request: Request) -> dict[str, bool]:
    return await supabase_auth_service.logout(_bearer_token(request))


@get("/auth/me")
async def me(request: Request) -> UserDTO:
    return await supabase_auth_service.current_user(_bearer_token(request))


auth_handlers = [login, signup, logout, me]
