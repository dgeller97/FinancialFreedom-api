from __future__ import annotations

from litestar import delete, get, patch, post
from supabase import AsyncClient

from .. import services
from ..dtos import TransactionDTO, TransactionUpsertDTO


@get("/transactions")
async def list_transactions(client: AsyncClient) -> list[TransactionDTO]:
    return await services.list_transactions(client)


@post("/transactions")
async def create_transaction(client: AsyncClient, data: TransactionUpsertDTO) -> TransactionDTO:
    return await services.create_transaction(client, data)


@patch("/transactions/{transaction_id:str}")
async def update_transaction(client: AsyncClient, transaction_id: str, data: TransactionUpsertDTO) -> TransactionDTO:
    return await services.update_transaction(client, transaction_id, data)


@delete("/transactions/{transaction_id:str}", status_code=204)
async def delete_transaction(client: AsyncClient, transaction_id: str) -> None:
    await services.delete_transaction(client, transaction_id)


transaction_handlers = [
    list_transactions,
    create_transaction,
    update_transaction,
    delete_transaction,
]
