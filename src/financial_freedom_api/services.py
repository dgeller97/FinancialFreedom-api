from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from .dtos import (
    AccountDTO,
    AccountUpsertDTO,
    AuthRequestDTO,
    AuthResponseDTO,
    CategoryDTO,
    CategoryGroupDTO,
    DEFAULT_CATEGORIES,
    DEFAULT_CATEGORY_GROUPS,
    TransactionDTO,
    TransactionUpsertDTO,
    UserDTO,
    new_id,
)


class ExampleStore:
    """Simple in-memory service layer for the first UI slice."""

    def __init__(self) -> None:
        self.demo_user = UserDTO(id="user-demo", email="demo@financialfreedom.dev")
        self.tokens: dict[str, UserDTO] = {}

        self.category_groups = [
            CategoryGroupDTO(id=f"group-{index + 1}", name=name, sort_order=index)
            for index, name in enumerate(DEFAULT_CATEGORY_GROUPS)
        ]
        group_lookup = {group.name: group.id for group in self.category_groups}
        self.categories = [
            CategoryDTO(
                id=f"category-{index + 1}",
                category_group_id=group_lookup[group_name],
                name=name,
                kind=kind,
            )
            for index, (group_name, name, kind) in enumerate(DEFAULT_CATEGORIES)
        ]
        self.accounts = [
            AccountDTO(
                id="account-1",
                name="Everyday Checking",
                account_type="checking",
                currency_code="USD",
                opening_balance_cents=250000,
                current_balance_cents=320450,
            ),
            AccountDTO(
                id="account-2",
                name="Cash Wallet",
                account_type="cash",
                currency_code="USD",
                opening_balance_cents=8000,
                current_balance_cents=4200,
            ),
        ]
        now = datetime.now(timezone.utc)
        self.transactions = [
            TransactionDTO(
                id="transaction-1",
                account_id="account-1",
                category_id="category-1",
                amount_cents=450000,
                direction="income",
                transaction_date=now - timedelta(days=7),
                payee="Employer",
                notes="Monthly paycheck",
                is_cleared=True,
            ),
            TransactionDTO(
                id="transaction-2",
                account_id="account-1",
                category_id="category-3",
                amount_cents=4825,
                direction="expense",
                transaction_date=now - timedelta(days=2),
                payee="Corner Market",
                notes="Weekly groceries",
                is_cleared=True,
            ),
            TransactionDTO(
                id="transaction-3",
                account_id="account-2",
                category_id="category-4",
                amount_cents=1800,
                direction="expense",
                transaction_date=now - timedelta(days=1),
                payee="Neighborhood Cafe",
                notes="Lunch",
            ),
        ]
        self._recalculate_balances()

    def signup(self, data: AuthRequestDTO) -> AuthResponseDTO:
        self.demo_user = UserDTO(id=self.demo_user.id, email=data.email)
        return self._issue_tokens(self.demo_user)

    def login(self, data: AuthRequestDTO) -> AuthResponseDTO:
        user = UserDTO(id=self.demo_user.id, email=data.email)
        return self._issue_tokens(user)

    def logout(self, token: str | None) -> None:
        if token:
            self.tokens.pop(token, None)

    def current_user(self, token: str | None) -> UserDTO:
        if token and token in self.tokens:
            return self.tokens[token]
        return self.demo_user

    def list_accounts(self) -> list[AccountDTO]:
        return deepcopy(self.accounts)

    def create_account(self, data: AccountUpsertDTO) -> AccountDTO:
        account = AccountDTO(
            id=new_id(),
            name=data.name,
            account_type=data.account_type,
            currency_code=data.currency_code,
            opening_balance_cents=data.opening_balance_cents,
            current_balance_cents=data.current_balance_cents
            if data.current_balance_cents is not None
            else data.opening_balance_cents,
            is_archived=data.is_archived,
        )
        self.accounts.append(account)
        return deepcopy(account)

    def update_account(self, account_id: str, data: AccountUpsertDTO) -> AccountDTO:
        for index, account in enumerate(self.accounts):
            if account.id == account_id:
                updated = replace(
                    account,
                    name=data.name,
                    account_type=data.account_type,
                    currency_code=data.currency_code,
                    opening_balance_cents=data.opening_balance_cents,
                    current_balance_cents=data.current_balance_cents
                    if data.current_balance_cents is not None
                    else account.current_balance_cents,
                    is_archived=data.is_archived,
                )
                self.accounts[index] = updated
                return deepcopy(updated)
        raise KeyError(account_id)

    def archive_account(self, account_id: str) -> None:
        for index, account in enumerate(self.accounts):
            if account.id == account_id:
                self.accounts[index] = replace(account, is_archived=True)
                return
        raise KeyError(account_id)

    def list_category_groups(self) -> list[CategoryGroupDTO]:
        return deepcopy(self.category_groups)

    def list_categories(self) -> list[CategoryDTO]:
        return deepcopy(self.categories)

    def list_transactions(self) -> list[TransactionDTO]:
        return sorted(deepcopy(self.transactions), key=lambda item: item.transaction_date, reverse=True)

    def create_transaction(self, data: TransactionUpsertDTO) -> TransactionDTO:
        transaction = TransactionDTO(
            id=new_id(),
            account_id=data.account_id,
            category_id=data.category_id,
            amount_cents=data.amount_cents,
            direction=data.direction,
            transaction_date=data.transaction_date,
            payee=data.payee,
            notes=data.notes,
            is_cleared=data.is_cleared,
            is_reconciled=data.is_reconciled,
        )
        self.transactions.append(transaction)
        self._recalculate_balances()
        return deepcopy(transaction)

    def update_transaction(self, transaction_id: str, data: TransactionUpsertDTO) -> TransactionDTO:
        for index, transaction in enumerate(self.transactions):
            if transaction.id == transaction_id:
                updated = TransactionDTO(
                    id=transaction.id,
                    account_id=data.account_id,
                    category_id=data.category_id,
                    amount_cents=data.amount_cents,
                    direction=data.direction,
                    transaction_date=data.transaction_date,
                    payee=data.payee,
                    notes=data.notes,
                    is_cleared=data.is_cleared,
                    is_reconciled=data.is_reconciled,
                )
                self.transactions[index] = updated
                self._recalculate_balances()
                return deepcopy(updated)
        raise KeyError(transaction_id)

    def delete_transaction(self, transaction_id: str) -> None:
        before = len(self.transactions)
        self.transactions = [item for item in self.transactions if item.id != transaction_id]
        if len(self.transactions) == before:
            raise KeyError(transaction_id)
        self._recalculate_balances()

    def _issue_tokens(self, user: UserDTO) -> AuthResponseDTO:
        access_token = f"demo-access-{new_id()}"
        refresh_token = f"demo-refresh-{new_id()}"
        self.tokens[access_token] = user
        return AuthResponseDTO(access_token=access_token, refresh_token=refresh_token, user=user)

    def _recalculate_balances(self) -> None:
        updated_accounts: list[AccountDTO] = []
        for account in self.accounts:
            balance = account.opening_balance_cents
            for transaction in self.transactions:
                if transaction.account_id != account.id:
                    continue
                if transaction.direction == "income":
                    balance += transaction.amount_cents
                else:
                    balance -= transaction.amount_cents
            updated_accounts.append(replace(account, current_balance_cents=balance))
        self.accounts = updated_accounts


store = ExampleStore()
