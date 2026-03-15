from __future__ import annotations

from litestar import delete, get, patch, post
from litestar.exceptions import NotFoundException
from supabase import AsyncClient

from .. import services
from ..dtos import AccountDTO, AccountUpsertDTO


@get("/accounts")
async def list_accounts(client: AsyncClient) -> list[AccountDTO]:
    return await services.list_accounts(client)


@post("/accounts")
async def create_account(client: AsyncClient, data: AccountUpsertDTO) -> AccountDTO:
    return await services.create_account(client, data)


@patch("/accounts/{account_id:str}")
async def update_account(client: AsyncClient, account_id: str, data: AccountUpsertDTO) -> AccountDTO:
    return await services.update_account(client, account_id, data)


@delete("/accounts/{account_id:str}", status_code=204)
async def archive_account(client: AsyncClient, account_id: str) -> None:
    await services.archive_account(client, account_id)


account_handlers = [list_accounts, create_account, update_account, archive_account]
