from __future__ import annotations

from litestar import delete, get, patch, post
from litestar.exceptions import NotFoundException

from ..dtos import AccountDTO, AccountUpsertDTO
from ..services import store


@get("/accounts")
async def list_accounts() -> list[AccountDTO]:
    return store.list_accounts()


@post("/accounts")
async def create_account(data: AccountUpsertDTO) -> AccountDTO:
    return store.create_account(data)


@patch("/accounts/{account_id:str}")
async def update_account(account_id: str, data: AccountUpsertDTO) -> AccountDTO:
    try:
        return store.update_account(account_id, data)
    except KeyError as exc:
        raise NotFoundException(detail=f"Account '{account_id}' was not found") from exc


@delete("/accounts/{account_id:str}", status_code=204)
async def archive_account(account_id: str) -> None:
    try:
        store.archive_account(account_id)
    except KeyError as exc:
        raise NotFoundException(detail=f"Account '{account_id}' was not found") from exc


account_handlers = [list_accounts, create_account, update_account, archive_account]
