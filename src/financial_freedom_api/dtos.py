from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class UserDTO:
    id: str
    email: str


@dataclass(slots=True)
class AuthRequestDTO:
    email: str
    password: str


@dataclass(slots=True)
class AuthResponseDTO:
    access_token: str
    refresh_token: str
    user: UserDTO


@dataclass(slots=True)
class AccountDTO:
    id: str
    name: str
    account_type: str
    currency_code: str
    opening_balance_cents: int
    current_balance_cents: int
    is_archived: bool = False


@dataclass(slots=True)
class AccountUpsertDTO:
    name: str
    account_type: str
    currency_code: str = "USD"
    opening_balance_cents: int = 0
    current_balance_cents: int | None = None
    is_archived: bool = False


@dataclass(slots=True)
class CategoryGroupDTO:
    id: str
    name: str
    sort_order: int = 0


@dataclass(slots=True)
class CategoryDTO:
    id: str
    category_group_id: str
    name: str
    kind: str = "expense"


@dataclass(slots=True)
class TransactionDTO:
    id: str
    account_id: str
    category_id: str | None
    amount_cents: int
    direction: str
    transaction_date: datetime
    payee: str
    notes: str
    is_cleared: bool = False
    is_reconciled: bool = False


@dataclass(slots=True)
class TransactionUpsertDTO:
    account_id: str
    category_id: str | None
    amount_cents: int
    direction: str
    transaction_date: datetime
    payee: str
    notes: str = ""
    is_cleared: bool = False
    is_reconciled: bool = False


@dataclass(slots=True)
class BudgetRowDTO:
    category_group: str
    category_name: str
    assigned_cents: int
    spent_cents: int
    remaining_cents: int


@dataclass(slots=True)
class SeedSummaryDTO:
    category_groups_seeded: int
    categories_seeded: int
    example_accounts_seeded: int
    example_transactions_seeded: int


def new_id() -> str:
    return str(uuid4())


DEFAULT_CATEGORY_GROUPS = [
    "Income",
    "Bills",
    "Daily Spending",
    "Savings",
    "Debt",
]

DEFAULT_CATEGORIES = [
    ("Income", "Paycheck", "income"),
    ("Bills", "Rent", "expense"),
    ("Daily Spending", "Groceries", "expense"),
    ("Daily Spending", "Dining Out", "expense"),
    ("Daily Spending", "Gas", "expense"),
    ("Daily Spending", "Shopping", "expense"),
    ("Savings", "Emergency Fund", "savings"),
    ("Debt", "Credit Card Payment", "debt_payment"),
]


def build_default_budget_rows() -> list[BudgetRowDTO]:
    return [
        BudgetRowDTO(
            category_group=group,
            category_name=name,
            assigned_cents=amount,
            spent_cents=spent,
            remaining_cents=amount - spent,
        )
        for group, name, amount, spent in (
            ("Income", "Paycheck", 450000, 0),
            ("Bills", "Rent", 160000, 160000),
            ("Daily Spending", "Groceries", 65000, 23250),
            ("Daily Spending", "Dining Out", 20000, 8600),
            ("Savings", "Emergency Fund", 50000, 0),
            ("Debt", "Credit Card Payment", 35000, 12000),
        )
    ]
