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


with target_household as (
  select id
  from app.households
  order by created_at asc
  limit 1
)
insert into app.category_groups (household_id, name, sort_order, is_system)
select h.id, 'Income', 0, true
from target_household h
on conflict (household_id, name)
do update set sort_order = excluded.sort_order;
with target_household as (
  select id
  from app.households
  order by created_at asc
  limit 1
)
insert into app.category_groups (household_id, name, sort_order, is_system)
select h.id, 'Bills', 1, true
from target_household h
on conflict (household_id, name)
do update set sort_order = excluded.sort_order;
with target_household as (
  select id
  from app.households
  order by created_at asc
  limit 1
)
insert into app.category_groups (household_id, name, sort_order, is_system)
select h.id, 'Daily Spending', 2, true
from target_household h
on conflict (household_id, name)
do update set sort_order = excluded.sort_order;
with target_household as (
  select id
  from app.households
  order by created_at asc
  limit 1
)
insert into app.category_groups (household_id, name, sort_order, is_system)
select h.id, 'Savings', 3, true
from target_household h
on conflict (household_id, name)
do update set sort_order = excluded.sort_order;
with target_household as (
  select id
  from app.households
  order by created_at asc
  limit 1
)
insert into app.category_groups (household_id, name, sort_order, is_system)
select h.id, 'Debt', 4, true
from target_household h
on conflict (household_id, name)
do update set sort_order = excluded.sort_order;


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
  'Paycheck',
  'income'::app.category_kind,
  0,
  true
from target_household h
join app.category_groups cg
  on cg.household_id = h.id
 and cg.name = 'Income'
on conflict (household_id, name)
do update set
  category_group_id = excluded.category_group_id,
  kind = excluded.kind,
  sort_order = excluded.sort_order;
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
  'Rent',
  'expense'::app.category_kind,
  1,
  true
from target_household h
join app.category_groups cg
  on cg.household_id = h.id
 and cg.name = 'Bills'
on conflict (household_id, name)
do update set
  category_group_id = excluded.category_group_id,
  kind = excluded.kind,
  sort_order = excluded.sort_order;
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
  'Groceries',
  'expense'::app.category_kind,
  2,
  true
from target_household h
join app.category_groups cg
  on cg.household_id = h.id
 and cg.name = 'Daily Spending'
on conflict (household_id, name)
do update set
  category_group_id = excluded.category_group_id,
  kind = excluded.kind,
  sort_order = excluded.sort_order;
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
  'Dining Out',
  'expense'::app.category_kind,
  3,
  true
from target_household h
join app.category_groups cg
  on cg.household_id = h.id
 and cg.name = 'Daily Spending'
on conflict (household_id, name)
do update set
  category_group_id = excluded.category_group_id,
  kind = excluded.kind,
  sort_order = excluded.sort_order;
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
  'Gas',
  'expense'::app.category_kind,
  4,
  true
from target_household h
join app.category_groups cg
  on cg.household_id = h.id
 and cg.name = 'Daily Spending'
on conflict (household_id, name)
do update set
  category_group_id = excluded.category_group_id,
  kind = excluded.kind,
  sort_order = excluded.sort_order;
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
  'Shopping',
  'expense'::app.category_kind,
  5,
  true
from target_household h
join app.category_groups cg
  on cg.household_id = h.id
 and cg.name = 'Daily Spending'
on conflict (household_id, name)
do update set
  category_group_id = excluded.category_group_id,
  kind = excluded.kind,
  sort_order = excluded.sort_order;
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
  'Emergency Fund',
  'savings'::app.category_kind,
  6,
  true
from target_household h
join app.category_groups cg
  on cg.household_id = h.id
 and cg.name = 'Savings'
on conflict (household_id, name)
do update set
  category_group_id = excluded.category_group_id,
  kind = excluded.kind,
  sort_order = excluded.sort_order;
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
  'Credit Card Payment',
  'debt_payment'::app.category_kind,
  7,
  true
from target_household h
join app.category_groups cg
  on cg.household_id = h.id
 and cg.name = 'Debt'
on conflict (household_id, name)
do update set
  category_group_id = excluded.category_group_id,
  kind = excluded.kind,
  sort_order = excluded.sort_order;

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
