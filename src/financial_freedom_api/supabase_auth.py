from __future__ import annotations

from dataclasses import dataclass

import httpx
from litestar.exceptions import HTTPException, ImproperlyConfiguredException

from .config import settings
from .dtos import AuthRequestDTO, AuthResponseDTO, UserDTO


@dataclass(slots=True)
class SupabaseAuthService:
    timeout_seconds: float = 15.0

    @property
    def _base_url(self) -> str:
        if not settings.supabase_url:
            raise ImproperlyConfiguredException(detail="SUPABASE_URL is required for auth.")
        return settings.supabase_url.rstrip("/")

    @property
    def _api_key(self) -> str:
        api_key = settings.supabase_anon_key or settings.supabase_service_role_key
        if not api_key:
            raise ImproperlyConfiguredException(
                detail="Set SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY to enable auth."
            )
        return api_key

    async def login(self, data: AuthRequestDTO) -> AuthResponseDTO:
        payload = await self._request(
            "POST",
            "/auth/v1/token",
            params={"grant_type": "password"},
            json={"email": data.email, "password": data.password},
        )
        return self._build_auth_response(payload)

    async def signup(self, data: AuthRequestDTO) -> AuthResponseDTO:
        payload = await self._request(
            "POST",
            "/auth/v1/signup",
            json={"email": data.email, "password": data.password},
        )
        return self._build_auth_response(payload)

    async def logout(self, access_token: str | None) -> dict[str, bool]:
        if not access_token:
            return {"success": True}
        await self._request(
            "POST",
            "/auth/v1/logout",
            access_token=access_token,
        )
        return {"success": True}

    async def current_user(self, access_token: str | None) -> UserDTO:
        if not access_token:
            raise HTTPException(status_code=401, detail="Missing bearer token.")
        payload = await self._request(
            "GET",
            "/auth/v1/user",
            access_token=access_token,
        )
        return UserDTO(
            id=payload["id"],
            email=payload.get("email", ""),
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, str] | None = None,
        access_token: str | None = None,
    ) -> dict:
        headers = {
            "apikey": self._api_key,
            "Content-Type": "application/json",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        async with httpx.AsyncClient(base_url=self._base_url, timeout=self.timeout_seconds) as client:
            response = await client.request(
                method,
                path,
                params=params,
                json=json,
                headers=headers,
            )

        if response.is_success:
            if not response.content:
                return {}
            return response.json()

        try:
            payload = response.json()
        except ValueError:
            payload = {}

        message = (
            payload.get("msg")
            or payload.get("error_description")
            or payload.get("error")
            or payload.get("message")
            or "Supabase auth request failed."
        )
        raise HTTPException(status_code=response.status_code, detail=message)

    def _build_auth_response(self, payload: dict) -> AuthResponseDTO:
        session_user = payload.get("user") or {}
        access_token = payload.get("access_token")
        refresh_token = payload.get("refresh_token")

        if not access_token or not refresh_token or not session_user.get("id"):
            raise HTTPException(
                status_code=502,
                detail="Supabase auth response did not include a full session.",
            )

        return AuthResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserDTO(
                id=session_user["id"],
                email=session_user.get("email", ""),
            ),
        )


supabase_auth_service = SupabaseAuthService()
