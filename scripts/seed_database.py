from __future__ import annotations

import argparse
import os
from pathlib import Path
import textwrap

from dotenv import load_dotenv
import psycopg


DEFAULT_GROUPS = [
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

DEFAULT_SQL_OUTPUT_PATH = Path("scripts/seed_database.generated.sql")


def load_env() -> None:
    load_dotenv(".env")
    load_dotenv("env")


def get_database_url() -> str | None:
    load_env()
    return os.getenv("DATABASE_URL")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the Financial Freedom database either directly or by generating SQL."
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "database", "sql"),
        default="auto",
        help="`database` uses DATABASE_URL, `sql` writes an idempotent SQL seed file, `auto` picks database when available.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_SQL_OUTPUT_PATH,
        help=f"Where to write generated SQL when using --mode sql. Default: {DEFAULT_SQL_OUTPUT_PATH}",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print generated SQL to stdout instead of writing a file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_url = get_database_url()

    if args.mode == "database":
        if not database_url:
            raise RuntimeError("DATABASE_URL is required when using --mode database.")
        seed_via_database(database_url)
        return

    if args.mode == "sql":
        write_sql(args.output, to_stdout=args.stdout)
        return

    if database_url:
        seed_via_database(database_url)
        return

    write_sql(args.output, to_stdout=args.stdout)
    print(
        "DATABASE_URL was not set, so an idempotent SQL seed file was generated instead.\n"
        "Run it in the Supabase SQL Editor or include it in a migration."
    )


def seed_via_database(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select id
                from app.households
                order by created_at asc
                limit 1
                """
            )
            household_row = cursor.fetchone()
            if household_row is None:
                raise RuntimeError(
                    "No household found. Create a user/profile first so the schema trigger can create a default household."
                )

            household_id = household_row[0]

            cursor.execute(
                """
                select id
                from app.profiles
                order by created_at asc
                limit 1
                """
            )
            profile_row = cursor.fetchone()
            if profile_row is None:
                raise RuntimeError("No profile found. Seed at least one auth user before running this script.")

            profile_id = profile_row[0]

            group_ids: dict[str, str] = {}
            for sort_order, name in enumerate(DEFAULT_GROUPS):
                cursor.execute(
                    """
                    insert into app.category_groups (household_id, name, sort_order, is_system)
                    values (%s, %s, %s, true)
                    on conflict (household_id, name)
                    do update set sort_order = excluded.sort_order
                    returning id
                    """,
                    (household_id, name, sort_order),
                )
                group_ids[name] = cursor.fetchone()[0]

            for sort_order, (group_name, category_name, kind) in enumerate(DEFAULT_CATEGORIES):
                cursor.execute(
                    """
                    insert into app.categories (
                        household_id,
                        category_group_id,
                        name,
                        kind,
                        sort_order,
                        is_system
                    )
                    values (%s, %s, %s, %s::app.category_kind, %s, true)
                    on conflict (household_id, name)
                    do update set
                        category_group_id = excluded.category_group_id,
                        kind = excluded.kind,
                        sort_order = excluded.sort_order
                    """,
                    (household_id, group_ids[group_name], category_name, kind, sort_order),
                )

            cursor.execute(
                """
                select id
                from app.accounts
                where household_id = %s and name = %s
                limit 1
                """,
                (household_id, "Example Checking"),
            )
            existing_account = cursor.fetchone()
            if existing_account is None:
                cursor.execute(
                    """
                    insert into app.accounts (
                        household_id,
                        created_by_user_id,
                        name,
                        kind,
                        status,
                        currency,
                        opening_balance_cents,
                        current_balance_cents,
                        include_in_budget,
                        include_in_net_worth
                    )
                    values (%s, %s, %s, 'checking', 'active', 'USD', %s, %s, true, true)
                    """,
                    (household_id, profile_id, "Example Checking", 250000, 250000),
                )

            cursor.execute(
                """
                select id
                from app.accounts
                where household_id = %s and name = %s
                limit 1
                """,
                (household_id, "Example Checking"),
            )
            account_row = cursor.fetchone()
            if account_row is not None:
                account_id = account_row[0]

                cursor.execute(
                    """
                    select id
                    from app.categories
                    where household_id = %s and name = %s
                    limit 1
                    """,
                    (household_id, "Paycheck"),
                )
                paycheck_row = cursor.fetchone()

                cursor.execute(
                    """
                    select id
                    from app.categories
                    where household_id = %s and name = %s
                    limit 1
                    """,
                    (household_id, "Groceries"),
                )
                groceries_row = cursor.fetchone()

                paycheck_exists = False
                if paycheck_row:
                    cursor.execute(
                        """
                        select 1
                        from app.transactions
                        where account_id = %s and merchant_name = %s and amount_cents = %s
                        limit 1
                        """,
                        (account_id, "Employer", 450000),
                    )
                    paycheck_exists = cursor.fetchone() is not None

                if paycheck_row and not paycheck_exists:
                    cursor.execute(
                        """
                        insert into app.transactions (
                            household_id,
                            account_id,
                            category_id,
                            amount_cents,
                            currency,
                            posted_at,
                            merchant_name,
                            description,
                            memo,
                            is_income,
                            created_by_user_id
                        )
                        values (%s, %s, %s, %s, 'USD', timezone('utc', now()) - interval '7 days', %s, %s, %s, true, %s)
                        """,
                        (household_id, account_id, paycheck_row[0], 450000, "Employer", "Seed paycheck", "Monthly income", profile_id),
                    )

                groceries_exists = False
                if groceries_row:
                    cursor.execute(
                        """
                        select 1
                        from app.transactions
                        where account_id = %s and merchant_name = %s and amount_cents = %s
                        limit 1
                        """,
                        (account_id, "Corner Market", 4825),
                    )
                    groceries_exists = cursor.fetchone() is not None

                if groceries_row and not groceries_exists:
                    cursor.execute(
                        """
                        insert into app.transactions (
                            household_id,
                            account_id,
                            category_id,
                            amount_cents,
                            currency,
                            posted_at,
                            merchant_name,
                            description,
                            memo,
                            is_income,
                            created_by_user_id
                        )
                        values (%s, %s, %s, %s, 'USD', timezone('utc', now()) - interval '2 days', %s, %s, %s, false, %s)
                        """,
                        (household_id, account_id, groceries_row[0], 4825, "Corner Market", "Seed groceries", "Weekly groceries", profile_id),
                    )

            connection.commit()

    print(f"Seed complete using DATABASE_URL from {Path.cwd()}.")


def render_sql() -> str:
    group_inserts = []
    for sort_order, name in enumerate(DEFAULT_GROUPS):
        group_inserts.append(
            f"""
with target_household as (
  select id
  from app.households
  order by created_at asc
  limit 1
)
insert into app.category_groups (household_id, name, sort_order, is_system)
select h.id, '{sql_escape(name)}', {sort_order}, true
from target_household h
on conflict (household_id, name)
do update set sort_order = excluded.sort_order;"""
        )

    category_inserts = []
    for sort_order, (group_name, category_name, kind) in enumerate(DEFAULT_CATEGORIES):
        category_inserts.append(
            f"""
with target_household as (
  select id
  from app.households
  order by created_at asc
  limit 1
)
insert into app.categories (
  household_id,
  category_group_id,
  name,
  kind,
  sort_order,
  is_system
)
select
  h.id,
  cg.id,
  '{sql_escape(category_name)}',
  '{sql_escape(kind)}'::app.category_kind,
  {sort_order},
  true
from target_household h
join app.category_groups cg
  on cg.household_id = h.id
 and cg.name = '{sql_escape(group_name)}'
on conflict (household_id, name)
do update set
  category_group_id = excluded.category_group_id,
  kind = excluded.kind,
  sort_order = excluded.sort_order;"""
        )

    return textwrap.dedent(
        f"""
        -- Financial Freedom seed data
        -- Safe to run multiple times.
        -- Intended for Supabase SQL Editor or a migration file.

        begin;

        do $$
        begin
          if not exists (select 1 from app.households) then
            raise exception 'No rows found in app.households. Create a user first so the auth trigger creates a household.';
          end if;

          if not exists (select 1 from app.profiles) then
            raise exception 'No rows found in app.profiles. Create a user first so the auth trigger creates a profile.';
          end if;
        end $$;

        {''.join(group_inserts)}

        {''.join(category_inserts)}

        with target_household as (
          select id
          from app.households
          order by created_at asc
          limit 1
        ),
        target_profile as (
          select id
          from app.profiles
          order by created_at asc
          limit 1
        )
        insert into app.accounts (
          household_id,
          created_by_user_id,
          name,
          kind,
          status,
          currency,
          opening_balance_cents,
          current_balance_cents,
          include_in_budget,
          include_in_net_worth
        )
        select
          h.id,
          p.id,
          'Example Checking',
          'checking'::app.account_kind,
          'active'::app.account_status,
          'USD',
          250000,
          250000,
          true,
          true
        from target_household h
        cross join target_profile p
        where not exists (
          select 1
          from app.accounts a
          where a.household_id = h.id
            and a.name = 'Example Checking'
        );

        with target_household as (
          select id
          from app.households
          order by created_at asc
          limit 1
        ),
        target_profile as (
          select id
          from app.profiles
          order by created_at asc
          limit 1
        ),
        target_account as (
          select a.id, a.household_id
          from app.accounts a
          join target_household h on h.id = a.household_id
          where a.name = 'Example Checking'
          limit 1
        ),
        target_category as (
          select c.id
          from app.categories c
          join target_household h on h.id = c.household_id
          where c.name = 'Paycheck'
          limit 1
        )
        insert into app.transactions (
          household_id,
          account_id,
          category_id,
          amount_cents,
          currency,
          posted_at,
          merchant_name,
          description,
          memo,
          is_income,
          created_by_user_id
        )
        select
          a.household_id,
          a.id,
          c.id,
          450000,
          'USD',
          timezone('utc', now()) - interval '7 days',
          'Employer',
          'Seed paycheck',
          'Monthly income',
          true,
          p.id
        from target_account a
        cross join target_category c
        cross join target_profile p
        where not exists (
          select 1
          from app.transactions t
          where t.account_id = a.id
            and t.merchant_name = 'Employer'
            and t.amount_cents = 450000
        );

        with target_household as (
          select id
          from app.households
          order by created_at asc
          limit 1
        ),
        target_profile as (
          select id
          from app.profiles
          order by created_at asc
          limit 1
        ),
        target_account as (
          select a.id, a.household_id
          from app.accounts a
          join target_household h on h.id = a.household_id
          where a.name = 'Example Checking'
          limit 1
        ),
        target_category as (
          select c.id
          from app.categories c
          join target_household h on h.id = c.household_id
          where c.name = 'Groceries'
          limit 1
        )
        insert into app.transactions (
          household_id,
          account_id,
          category_id,
          amount_cents,
          currency,
          posted_at,
          merchant_name,
          description,
          memo,
          is_income,
          created_by_user_id
        )
        select
          a.household_id,
          a.id,
          c.id,
          4825,
          'USD',
          timezone('utc', now()) - interval '2 days',
          'Corner Market',
          'Seed groceries',
          'Weekly groceries',
          false,
          p.id
        from target_account a
        cross join target_category c
        cross join target_profile p
        where not exists (
          select 1
          from app.transactions t
          where t.account_id = a.id
            and t.merchant_name = 'Corner Market'
            and t.amount_cents = 4825
        );

        commit;
        """
    ).strip() + "\n"


def write_sql(output_path: Path, *, to_stdout: bool) -> None:
    sql = render_sql()
    if to_stdout:
        print(sql)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sql, encoding="utf-8")
    print(f"Wrote idempotent SQL seed file to {output_path}.")


def sql_escape(value: str) -> str:
    return value.replace("'", "''")


if __name__ == "__main__":
    main()
