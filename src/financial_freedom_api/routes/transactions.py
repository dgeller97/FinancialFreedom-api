from __future__ import annotations

from litestar import delete, get, patch, post
from litestar.exceptions import NotFoundException

from ..dtos import TransactionDTO, TransactionUpsertDTO
from ..services import store


@get("/transactions")
async def list_transactions() -> list[TransactionDTO]:
    return store.list_transactions()


@post("/transactions")
async def create_transaction(data: TransactionUpsertDTO) -> TransactionDTO:
    return store.create_transaction(data)


@patch("/transactions/{transaction_id:str}")
async def update_transaction(transaction_id: str, data: TransactionUpsertDTO) -> TransactionDTO:
    try:
        return store.update_transaction(transaction_id, data)
    except KeyError as exc:
        raise NotFoundException(detail=f"Transaction '{transaction_id}' was not found") from exc


@delete("/transactions/{transaction_id:str}", status_code=204)
async def delete_transaction(transaction_id: str) -> None:
    try:
        store.delete_transaction(transaction_id)
    except KeyError as exc:
        raise NotFoundException(detail=f"Transaction '{transaction_id}' was not found") from exc


transaction_handlers = [
    list_transactions,
    create_transaction,
    update_transaction,
    delete_transaction,
]
