from __future__ import annotations

from supabase import AsyncClient
from litestar.exceptions import NotFoundException
from datetime import datetime

from .dtos import (
    AccountDTO,
    AccountUpsertDTO,
    CategoryDTO,
    CategoryGroupDTO,
    TransactionDTO,
    TransactionUpsertDTO,
)


async def _get_household_id(client: AsyncClient) -> str:
    res = await client.table("households").select("id").limit(1).execute()
    data = res.data
    if not data:
        raise NotFoundException("User has no household.")
    return data[0]["id"]


async def _get_user_id(client: AsyncClient) -> str:
    res = await client.table("profiles").select("id").limit(1).execute()
    data = res.data
    if not data:
        raise NotFoundException("User has no profile.")
    return data[0]["id"]


async def list_accounts(client: AsyncClient) -> list[AccountDTO]:
    res = await client.table("accounts").select("*").eq("status", "active").execute()
    
    accounts = []
    for row in res.data:
        accounts.append(AccountDTO(
            id=row["id"],
            name=row["name"],
            account_type=row["kind"],
            currency_code=row["currency"],
            opening_balance_cents=row["opening_balance_cents"],
            current_balance_cents=row["current_balance_cents"],
            is_archived=row["status"] == "archived",
        ))
    return accounts


async def create_account(client: AsyncClient, data: AccountUpsertDTO) -> AccountDTO:
    household_id = await _get_household_id(client)
    user_id = await _get_user_id(client)
    
    payload = {
        "household_id": household_id,
        "created_by_user_id": user_id,
        "name": data.name,
        "kind": data.account_type,
        "currency": data.currency_code,
        "opening_balance_cents": data.opening_balance_cents,
        "current_balance_cents": data.current_balance_cents if data.current_balance_cents is not None else data.opening_balance_cents,
        "status": "archived" if data.is_archived else "active",
    }
    
    res = await client.table("accounts").insert(payload).execute()
    row = res.data[0]
    
    return AccountDTO(
        id=row["id"],
        name=row["name"],
        account_type=row["kind"],
        currency_code=row["currency"],
        opening_balance_cents=row["opening_balance_cents"],
        current_balance_cents=row["current_balance_cents"],
        is_archived=row["status"] == "archived",
    )


async def update_account(client: AsyncClient, account_id: str, data: AccountUpsertDTO) -> AccountDTO:
    payload = {
        "name": data.name,
        "kind": data.account_type,
        "currency": data.currency_code,
        "opening_balance_cents": data.opening_balance_cents,
        "status": "archived" if data.is_archived else "active",
    }
    if data.current_balance_cents is not None:
        payload["current_balance_cents"] = data.current_balance_cents

    res = await client.table("accounts").update(payload).eq("id", account_id).execute()
    if not res.data:
        raise NotFoundException(f"Account '{account_id}' was not found")
    
    row = res.data[0]
    return AccountDTO(
        id=row["id"],
        name=row["name"],
        account_type=row["kind"],
        currency_code=row["currency"],
        opening_balance_cents=row["opening_balance_cents"],
        current_balance_cents=row["current_balance_cents"],
        is_archived=row["status"] == "archived",
    )


async def archive_account(client: AsyncClient, account_id: str) -> None:
    res = await client.table("accounts").update({"status": "archived"}).eq("id", account_id).execute()
    if not res.data:
        raise NotFoundException(f"Account '{account_id}' was not found")


async def list_category_groups(client: AsyncClient) -> list[CategoryGroupDTO]:
    res = await client.table("category_groups").select("*").order("sort_order").execute()
    return [
        CategoryGroupDTO(id=row["id"], name=row["name"], sort_order=row["sort_order"])
        for row in res.data
    ]


async def list_categories(client: AsyncClient) -> list[CategoryDTO]:
    res = await client.table("categories").select("*").order("sort_order").execute()
    return [
        CategoryDTO(
            id=row["id"],
            category_group_id=row["category_group_id"] or "",
            name=row["name"],
            kind=row["kind"]
        )
        for row in res.data
    ]


def _parse_date(sys_date: str) -> datetime:
    from dateutil.parser import isoparse
    return isoparse(sys_date)


async def list_transactions(client: AsyncClient) -> list[TransactionDTO]:
    res = await client.table("transactions").select("*").order("posted_at", desc=True).execute()
    
    txs = []
    for row in res.data:
        txs.append(TransactionDTO(
            id=row["id"],
            account_id=row["account_id"],
            category_id=row["category_id"],
            amount_cents=row["amount_cents"],
            direction="income" if row["is_income"] else "expense",
            transaction_date=_parse_date(row["posted_at"]),
            payee=row["merchant_name"] or "",
            notes=row["description"] or "",
            is_cleared=row["status"] == "posted",
            is_reconciled=False,
        ))
    return txs


async def create_transaction(client: AsyncClient, data: TransactionUpsertDTO) -> TransactionDTO:
    household_id = await _get_household_id(client)
    user_id = await _get_user_id(client)
    
    payload = {
        "household_id": household_id,
        "account_id": data.account_id,
        "category_id": data.category_id,
        "created_by_user_id": user_id,
        "amount_cents": data.amount_cents,
        "currency": "USD",
        "posted_at": data.transaction_date.isoformat(),
        "merchant_name": data.payee,
        "description": data.notes,
        "is_income": data.direction == "income",
        "status": "posted" if data.is_cleared else "pending"
    }
    
    res = await client.table("transactions").insert(payload).execute()
    row = res.data[0]
    
    return TransactionDTO(
        id=row["id"],
        account_id=row["account_id"],
        category_id=row["category_id"],
        amount_cents=row["amount_cents"],
        direction="income" if row["is_income"] else "expense",
        transaction_date=_parse_date(row["posted_at"]),
        payee=row["merchant_name"] or "",
        notes=row["description"] or "",
        is_cleared=row["status"] == "posted",
        is_reconciled=False,
    )


async def update_transaction(client: AsyncClient, transaction_id: str, data: TransactionUpsertDTO) -> TransactionDTO:
    payload = {
        "account_id": data.account_id,
        "category_id": data.category_id,
        "amount_cents": data.amount_cents,
        "posted_at": data.transaction_date.isoformat(),
        "merchant_name": data.payee,
        "description": data.notes,
        "is_income": data.direction == "income",
        "status": "posted" if data.is_cleared else "pending"
    }
    
    res = await client.table("transactions").update(payload).eq("id", transaction_id).execute()
    if not res.data:
        raise NotFoundException(f"Transaction '{transaction_id}' was not found")
        
    row = res.data[0]
    return TransactionDTO(
        id=row["id"],
        account_id=row["account_id"],
        category_id=row["category_id"],
        amount_cents=row["amount_cents"],
        direction="income" if row["is_income"] else "expense",
        transaction_date=_parse_date(row["posted_at"]),
        payee=row["merchant_name"] or "",
        notes=row["description"] or "",
        is_cleared=row["status"] == "posted",
        is_reconciled=False,
    )


async def delete_transaction(client: AsyncClient, transaction_id: str) -> None:
    res = await client.table("transactions").delete().eq("id", transaction_id).execute()
    if not res.data:
        raise NotFoundException(f"Transaction '{transaction_id}' was not found")
