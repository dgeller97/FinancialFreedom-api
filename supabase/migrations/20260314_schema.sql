-- Budgeting app starter schema for Supabase
-- Save as: supabase/migrations/20260313_budgeting_app_starter.sql
-- Run in Supabase SQL Editor or via supabase db push

begin;

create extension if not exists pgcrypto;
create extension if not exists citext;

create schema if not exists app;

-- -----------------------------------------------------------------------------
-- Enums
-- -----------------------------------------------------------------------------
do $$ begin
  create type app.membership_role as enum ('owner', 'admin', 'member', 'viewer');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.account_kind as enum (
    'checking',
    'savings',
    'cash',
    'credit_card',
    'line_of_credit',
    'loan',
    'investment',
    'mortgage',
    'other_asset',
    'other_liability'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.account_status as enum ('active', 'archived');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.category_kind as enum ('expense', 'income', 'transfer', 'debt_payment', 'savings');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.goal_type as enum ('target_balance', 'target_by_date', 'monthly_contribution', 'debt_payoff');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.goal_status as enum ('active', 'completed', 'paused', 'archived');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.recurrence_frequency as enum ('weekly', 'biweekly', 'monthly', 'quarterly', 'yearly');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.recurring_kind as enum ('bill', 'income', 'subscription', 'transfer', 'savings');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.transaction_source as enum ('manual', 'bank_sync', 'csv_import', 'system');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.transaction_status as enum ('pending', 'posted', 'deleted');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.notification_type as enum ('overspend', 'bill_due', 'goal_due', 'sync_error', 'insight', 'trial_ending', 'subscription_issue');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.notification_status as enum ('unread', 'read', 'archived');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.provider_name as enum ('plaid', 'teller', 'mx', 'manual');
exception when duplicate_object then null; end $$;

do $$ begin
  create type app.app_subscription_status as enum ('trialing', 'active', 'past_due', 'canceled', 'incomplete', 'expired');
exception when duplicate_object then null; end $$;

-- -----------------------------------------------------------------------------
-- Utility functions
-- -----------------------------------------------------------------------------
create or replace function app.current_user_id()
returns uuid
language sql
stable
as $$
  select auth.uid()
$$;

create or replace function app.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;


-- -----------------------------------------------------------------------------
-- Profile + household / collaboration
-- -----------------------------------------------------------------------------
create table if not exists app.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email citext,
  display_name text,
  base_currency char(3) not null default 'USD',
  timezone text not null default 'UTC',
  avatar_url text,
  onboarding_completed boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.households (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid not null references app.profiles(id) on delete cascade,
  name text not null,
  base_currency char(3) not null default 'USD',
  timezone text not null default 'UTC',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.household_members (
  household_id uuid not null references app.households(id) on delete cascade,
  user_id uuid not null references app.profiles(id) on delete cascade,
  role app.membership_role not null default 'member',
  invited_by_user_id uuid references app.profiles(id) on delete set null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  primary key (household_id, user_id)
);

create table if not exists app.household_invites (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  email citext not null,
  role app.membership_role not null default 'member',
  invited_by_user_id uuid not null references app.profiles(id) on delete cascade,
  token uuid not null default gen_random_uuid() unique,
  accepted_at timestamptz,
  expires_at timestamptz not null,
  created_at timestamptz not null default timezone('utc', now()),
  unique (household_id, email)
);

-- -----------------------------------------------------------------------------
-- Billing for your app subscription
-- -----------------------------------------------------------------------------
create table if not exists app.billing_customers (
  user_id uuid primary key references app.profiles(id) on delete cascade,
  provider text not null default 'stripe',
  provider_customer_id text not null unique,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.billing_products (
  id uuid primary key default gen_random_uuid(),
  provider text not null default 'stripe',
  provider_product_id text not null unique,
  name text not null,
  description text,
  active boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.billing_prices (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references app.billing_products(id) on delete cascade,
  provider text not null default 'stripe',
  provider_price_id text not null unique,
  amount_cents integer not null check (amount_cents >= 0),
  currency char(3) not null,
  interval_count integer not null default 1 check (interval_count > 0),
  interval_unit text not null check (interval_unit in ('day', 'week', 'month', 'year')),
  active boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.user_app_subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references app.profiles(id) on delete cascade,
  billing_customer_user_id uuid references app.billing_customers(user_id) on delete set null,
  billing_price_id uuid references app.billing_prices(id) on delete set null,
  provider text not null default 'stripe',
  provider_subscription_id text unique,
  status app.app_subscription_status not null default 'trialing',
  trial_ends_at timestamptz,
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  canceled_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

-- -----------------------------------------------------------------------------
-- Financial institutions / linked accounts / accounts
-- -----------------------------------------------------------------------------
create table if not exists app.financial_institutions (
  id uuid primary key default gen_random_uuid(),
  provider app.provider_name not null,
  provider_institution_id text not null,
  name text not null,
  logo_url text,
  primary_color text,
  url text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (provider, provider_institution_id)
);

create table if not exists app.linked_items (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  provider app.provider_name not null,
  institution_id uuid references app.financial_institutions(id) on delete set null,
  created_by_user_id uuid not null references app.profiles(id) on delete cascade,
  provider_item_id text,
  provider_access_token_encrypted text,
  provider_refresh_token_encrypted text,
  last_sync_at timestamptz,
  last_successful_sync_at timestamptz,
  last_error_code text,
  last_error_message text,
  status text not null default 'active' check (status in ('active', 'reauth_required', 'error', 'disconnected')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (provider, provider_item_id)
);

create table if not exists app.accounts (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  linked_item_id uuid references app.linked_items(id) on delete set null,
  created_by_user_id uuid not null references app.profiles(id) on delete cascade,
  name text not null,
  official_name text,
  kind app.account_kind not null,
  status app.account_status not null default 'active',
  provider_account_id text,
  mask text,
  currency char(3) not null,
  include_in_budget boolean not null default true,
  include_in_net_worth boolean not null default true,
  interest_rate_bps integer check (interest_rate_bps between 0 and 100000),
  credit_limit_cents bigint,
  opening_balance_cents bigint not null default 0,
  current_balance_cents bigint not null default 0,
  available_balance_cents bigint,
  last_reconciled_at timestamptz,
  notes text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (linked_item_id, provider_account_id)
);

create table if not exists app.account_balance_history (
  id uuid primary key default gen_random_uuid(),
  account_id uuid not null references app.accounts(id) on delete cascade,
  as_of_date date not null,
  current_balance_cents bigint not null,
  available_balance_cents bigint,
  created_at timestamptz not null default timezone('utc', now()),
  unique (account_id, as_of_date)
);

-- -----------------------------------------------------------------------------
-- Categories and budget periods
-- -----------------------------------------------------------------------------
create table if not exists app.category_groups (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  name text not null,
  sort_order integer not null default 0,
  is_system boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (household_id, name)
);

create table if not exists app.categories (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  category_group_id uuid references app.category_groups(id) on delete set null,
  name text not null,
  kind app.category_kind not null default 'expense',
  parent_category_id uuid references app.categories(id) on delete set null,
  sort_order integer not null default 0,
  icon text,
  color text,
  is_hidden boolean not null default false,
  is_system boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (household_id, name)
);

create table if not exists app.category_targets (
  id uuid primary key default gen_random_uuid(),
  category_id uuid not null references app.categories(id) on delete cascade,
  target_type text not null check (target_type in ('monthly', 'weekly', 'by_date', 'minimum_balance', 'custom')),
  target_cents bigint,
  target_date date,
  rollover_enabled boolean not null default true,
  notes text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.budget_periods (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  period_start date not null,
  period_end date not null,
  label text,
  ready_to_assign_cents bigint not null default 0,
  assigned_total_cents bigint not null default 0,
  activity_total_cents bigint not null default 0,
  available_total_cents bigint not null default 0,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (period_end >= period_start),
  unique (household_id, period_start)
);

create table if not exists app.budget_category_assignments (
  id uuid primary key default gen_random_uuid(),
  budget_period_id uuid not null references app.budget_periods(id) on delete cascade,
  category_id uuid not null references app.categories(id) on delete cascade,
  assigned_cents bigint not null default 0,
  activity_cents bigint not null default 0,
  available_cents bigint not null default 0,
  rollover_from_prev_cents bigint not null default 0,
  notes text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (budget_period_id, category_id)
);

-- -----------------------------------------------------------------------------
-- Transactions
-- -----------------------------------------------------------------------------
create table if not exists app.transactions (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  account_id uuid not null references app.accounts(id) on delete cascade,
  transfer_account_id uuid references app.accounts(id) on delete set null,
  category_id uuid references app.categories(id) on delete set null,
  source app.transaction_source not null default 'manual',
  status app.transaction_status not null default 'posted',
  provider_transaction_id text,
  amount_cents bigint not null,
  currency char(3) not null,
  authorized_at timestamptz,
  posted_at timestamptz not null,
  merchant_name text,
  description text,
  memo text,
  is_transfer boolean not null default false,
  is_income boolean not null default false,
  is_subscription_candidate boolean not null default false,
  needs_review boolean not null default false,
  metadata jsonb not null default '{}'::jsonb,
  created_by_user_id uuid references app.profiles(id) on delete set null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (account_id, provider_transaction_id)
);

create table if not exists app.transaction_splits (
  id uuid primary key default gen_random_uuid(),
  transaction_id uuid not null references app.transactions(id) on delete cascade,
  category_id uuid references app.categories(id) on delete set null,
  amount_cents bigint not null,
  memo text,
  sort_order integer not null default 0,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.transaction_attachments (
  id uuid primary key default gen_random_uuid(),
  transaction_id uuid not null references app.transactions(id) on delete cascade,
  storage_bucket text not null,
  storage_path text not null,
  uploaded_by_user_id uuid not null references app.profiles(id) on delete cascade,
  created_at timestamptz not null default timezone('utc', now()),
  unique (storage_bucket, storage_path)
);

create table if not exists app.transaction_categorizations (
  id uuid primary key default gen_random_uuid(),
  transaction_id uuid not null references app.transactions(id) on delete cascade,
  suggested_category_id uuid references app.categories(id) on delete set null,
  confidence numeric(5,4) check (confidence between 0 and 1),
  model_name text,
  rationale text,
  accepted boolean,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.transaction_rules (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  name text not null,
  match_json jsonb not null,
  actions_json jsonb not null,
  is_active boolean not null default true,
  created_by_user_id uuid not null references app.profiles(id) on delete cascade,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

-- -----------------------------------------------------------------------------
-- Goals, bills, subscriptions, reminders, insights
-- -----------------------------------------------------------------------------
create table if not exists app.goals (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  category_id uuid references app.categories(id) on delete set null,
  account_id uuid references app.accounts(id) on delete set null,
  linked_account_id uuid references app.accounts(id) on delete set null,
  name text not null,
  goal_type app.goal_type not null,
  status app.goal_status not null default 'active',
  target_cents bigint,
  current_saved_cents bigint not null default 0,
  target_date date,
  monthly_contribution_cents bigint,
  priority smallint not null default 3 check (priority between 1 and 5),
  notes text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.recurring_plans (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  account_id uuid references app.accounts(id) on delete set null,
  category_id uuid references app.categories(id) on delete set null,
  name text not null,
  kind app.recurring_kind not null,
  amount_cents bigint not null,
  currency char(3) not null,
  frequency app.recurrence_frequency not null,
  interval_count integer not null default 1 check (interval_count > 0),
  next_due_date date not null,
  merchant_name text,
  auto_create_transaction boolean not null default false,
  is_active boolean not null default true,
  reminder_days_before integer not null default 3 check (reminder_days_before >= 0),
  notes text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.subscription_insights (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  recurring_plan_id uuid references app.recurring_plans(id) on delete cascade,
  merchant_name text not null,
  monthly_cost_cents bigint not null default 0,
  annual_cost_cents bigint not null default 0,
  last_charge_at timestamptz,
  potential_duplicate boolean not null default false,
  price_increase_detected boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (household_id, merchant_name)
);

create table if not exists app.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references app.profiles(id) on delete cascade,
  household_id uuid references app.households(id) on delete cascade,
  type app.notification_type not null,
  status app.notification_status not null default 'unread',
  title text not null,
  body text,
  data jsonb not null default '{}'::jsonb,
  sent_at timestamptz,
  read_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.user_notification_preferences (
  user_id uuid primary key references app.profiles(id) on delete cascade,
  email_enabled boolean not null default true,
  push_enabled boolean not null default true,
  overspend_enabled boolean not null default true,
  bill_due_enabled boolean not null default true,
  goal_due_enabled boolean not null default true,
  weekly_summary_enabled boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.cashflow_forecasts (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  account_id uuid references app.accounts(id) on delete cascade,
  forecast_date date not null,
  projected_balance_cents bigint not null,
  assumptions jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  unique (household_id, account_id, forecast_date)
);

create table if not exists app.monthly_insights (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  budget_period_id uuid references app.budget_periods(id) on delete cascade,
  insight_type text not null,
  title text not null,
  body text,
  metric_value numeric,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

-- -----------------------------------------------------------------------------
-- Import/sync/audit
-- -----------------------------------------------------------------------------
create table if not exists app.import_jobs (
  id uuid primary key default gen_random_uuid(),
  household_id uuid not null references app.households(id) on delete cascade,
  started_by_user_id uuid not null references app.profiles(id) on delete cascade,
  job_type text not null check (job_type in ('csv_import', 'bank_sync', 'backfill', 'webhook_replay')),
  source_name text,
  status text not null check (status in ('queued', 'running', 'succeeded', 'failed')),
  started_at timestamptz,
  completed_at timestamptz,
  records_seen integer not null default 0,
  records_created integer not null default 0,
  records_updated integer not null default 0,
  error_message text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists app.audit_log (
  id uuid primary key default gen_random_uuid(),
  household_id uuid references app.households(id) on delete cascade,
  actor_user_id uuid references app.profiles(id) on delete set null,
  entity_table text not null,
  entity_id uuid,
  action text not null,
  old_data jsonb,
  new_data jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

-- -----------------------------------------------------------------------------
-- Helpful views
-- -----------------------------------------------------------------------------
create or replace view app.v_account_net_worth as
select
  a.household_id,
  a.id as account_id,
  a.name,
  a.kind,
  a.currency,
  a.current_balance_cents,
  case
    when a.kind in ('credit_card', 'line_of_credit', 'loan', 'mortgage', 'other_liability') then -abs(a.current_balance_cents)
    else a.current_balance_cents
  end as net_worth_contribution_cents
from app.accounts a
where a.include_in_net_worth = true
  and a.status = 'active';

create or replace view app.v_budget_spending_by_category as
select
  t.household_id,
  date_trunc('month', t.posted_at)::date as period_month,
  coalesce(ts.category_id, t.category_id) as category_id,
  sum(coalesce(ts.amount_cents, t.amount_cents)) as amount_cents
from app.transactions t
left join app.transaction_splits ts on ts.transaction_id = t.id
where t.status = 'posted'
group by 1, 2, 3;

-- -----------------------------------------------------------------------------
-- Trigger: create app profile + default household when auth user is created
-- -----------------------------------------------------------------------------
create or replace function app.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public, auth, app
as $$
declare
  v_household_id uuid;
begin
  insert into app.profiles (id, email, display_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'display_name', split_part(coalesce(new.email, ''), '@', 1))
  )
  on conflict (id) do update
  set email = excluded.email,
      display_name = coalesce(app.profiles.display_name, excluded.display_name),
      updated_at = timezone('utc', now());

  insert into app.households (owner_user_id, name, base_currency, timezone)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'household_name', 'My Budget'),
    'USD',
    'UTC'
  )
  returning id into v_household_id;

  insert into app.household_members (household_id, user_id, role)
  values (v_household_id, new.id, 'owner')
  on conflict do nothing;

  insert into app.user_notification_preferences (user_id)
  values (new.id)
  on conflict do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure app.handle_new_auth_user();

-- -----------------------------------------------------------------------------
-- Timestamps
-- -----------------------------------------------------------------------------
do $$
declare
  r record;
begin
  for r in
    select table_schema, table_name
    from information_schema.columns
    where table_schema = 'app'
      and column_name = 'updated_at'
  loop
    execute format('drop trigger if exists trg_touch_%I on %I.%I', r.table_name, r.table_schema, r.table_name);
    execute format(
      'create trigger trg_touch_%I before update on %I.%I for each row execute procedure app.touch_updated_at()',
      r.table_name, r.table_schema, r.table_name
    );
  end loop;
end $$;

-- -----------------------------------------------------------------------------
-- Utility functions cont'd
-- -----------------------------------------------------------------------------

create or replace function app.user_is_household_member(p_household_id uuid)
returns boolean
language sql
security definer
set search_path = public, app
stable
as $$
  select exists (
    select 1
    from app.household_members hm
    where hm.household_id = p_household_id
      and hm.user_id = auth.uid()
  )
$$;

create or replace function app.user_has_household_role(
  p_household_id uuid,
  p_roles app.membership_role[]
)
returns boolean
language sql
security definer
set search_path = public, app
stable
as $$
  select exists (
    select 1
    from app.household_members hm
    where hm.household_id = p_household_id
      and hm.user_id = auth.uid()
      and hm.role = any (p_roles)
  )
$$;



-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------
create index if not exists idx_profiles_email on app.profiles(email);
create index if not exists idx_households_owner on app.households(owner_user_id);
create index if not exists idx_household_members_user on app.household_members(user_id);
create index if not exists idx_accounts_household on app.accounts(household_id);
create index if not exists idx_accounts_kind on app.accounts(kind);
create index if not exists idx_account_balance_history_account_date on app.account_balance_history(account_id, as_of_date desc);
create index if not exists idx_categories_household on app.categories(household_id);
create index if not exists idx_budget_periods_household_start on app.budget_periods(household_id, period_start desc);
create index if not exists idx_budget_assignments_period on app.budget_category_assignments(budget_period_id);
create index if not exists idx_transactions_household_posted_at on app.transactions(household_id, posted_at desc);
create index if not exists idx_transactions_account_posted_at on app.transactions(account_id, posted_at desc);
create index if not exists idx_transactions_category on app.transactions(category_id);
create index if not exists idx_transactions_provider_txn on app.transactions(provider_transaction_id);
create index if not exists idx_transactions_metadata_gin on app.transactions using gin(metadata);
create index if not exists idx_transaction_rules_household on app.transaction_rules(household_id) where is_active = true;
create index if not exists idx_goals_household on app.goals(household_id);
create index if not exists idx_recurring_plans_household_due on app.recurring_plans(household_id, next_due_date);
create index if not exists idx_notifications_user_status on app.notifications(user_id, status, created_at desc);
create index if not exists idx_import_jobs_household on app.import_jobs(household_id, created_at desc);
create index if not exists idx_audit_log_household on app.audit_log(household_id, created_at desc);

-- -----------------------------------------------------------------------------
-- Enable RLS
-- -----------------------------------------------------------------------------
alter table app.profiles enable row level security;
alter table app.households enable row level security;
alter table app.household_members enable row level security;
alter table app.household_invites enable row level security;
alter table app.billing_customers enable row level security;
alter table app.billing_products enable row level security;
alter table app.billing_prices enable row level security;
alter table app.user_app_subscriptions enable row level security;
alter table app.financial_institutions enable row level security;
alter table app.linked_items enable row level security;
alter table app.accounts enable row level security;
alter table app.account_balance_history enable row level security;
alter table app.category_groups enable row level security;
alter table app.categories enable row level security;
alter table app.category_targets enable row level security;
alter table app.budget_periods enable row level security;
alter table app.budget_category_assignments enable row level security;
alter table app.transactions enable row level security;
alter table app.transaction_splits enable row level security;
alter table app.transaction_attachments enable row level security;
alter table app.transaction_categorizations enable row level security;
alter table app.transaction_rules enable row level security;
alter table app.goals enable row level security;
alter table app.recurring_plans enable row level security;
alter table app.subscription_insights enable row level security;
alter table app.notifications enable row level security;
alter table app.user_notification_preferences enable row level security;
alter table app.cashflow_forecasts enable row level security;
alter table app.monthly_insights enable row level security;
alter table app.import_jobs enable row level security;
alter table app.audit_log enable row level security;

-- -----------------------------------------------------------------------------
-- RLS Policies
-- -----------------------------------------------------------------------------
-- Profiles
create policy "profiles_select_self" on app.profiles
  for select using ((select auth.uid()) = id);
create policy "profiles_insert_self" on app.profiles
  for insert with check ((select auth.uid()) = id);
create policy "profiles_update_self" on app.profiles
  for update using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

-- Households
create policy "households_select_member" on app.households
  for select using (app.user_is_household_member(id));
create policy "households_insert_owner" on app.households
  for insert with check ((select auth.uid()) = owner_user_id);
create policy "households_update_admin" on app.households
  for update using (app.user_has_household_role(id, array['owner','admin']::app.membership_role[]))
  with check (app.user_has_household_role(id, array['owner','admin']::app.membership_role[]));
create policy "households_delete_owner" on app.households
  for delete using (app.user_has_household_role(id, array['owner']::app.membership_role[]));

-- Household members / invites
create policy "household_members_select_member" on app.household_members
  for select using (app.user_is_household_member(household_id));
create policy "household_members_insert_admin" on app.household_members
  for insert with check (app.user_has_household_role(household_id, array['owner','admin']::app.membership_role[]));
create policy "household_members_update_admin" on app.household_members
  for update using (app.user_has_household_role(household_id, array['owner','admin']::app.membership_role[]))
  with check (app.user_has_household_role(household_id, array['owner','admin']::app.membership_role[]));
create policy "household_members_delete_owner_admin" on app.household_members
  for delete using (app.user_has_household_role(household_id, array['owner','admin']::app.membership_role[]));

create policy "household_invites_select_member" on app.household_invites
  for select using (app.user_is_household_member(household_id));
create policy "household_invites_modify_admin" on app.household_invites
  for all using (app.user_has_household_role(household_id, array['owner','admin']::app.membership_role[]))
  with check (app.user_has_household_role(household_id, array['owner','admin']::app.membership_role[]));

-- Billing
create policy "billing_customers_owner" on app.billing_customers
  for all using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
create policy "user_subscriptions_owner" on app.user_app_subscriptions
  for all using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
create policy "billing_products_read_authenticated" on app.billing_products
  for select to authenticated using (true);
create policy "billing_prices_read_authenticated" on app.billing_prices
  for select to authenticated using (true);

-- Shared household tables
create policy "institutions_read_authenticated" on app.financial_institutions
  for select to authenticated using (true);

create policy "linked_items_household_member" on app.linked_items
  for select using (app.user_is_household_member(household_id));
create policy "linked_items_household_admin" on app.linked_items
  for all using (app.user_has_household_role(household_id, array['owner','admin']::app.membership_role[]))
  with check (app.user_has_household_role(household_id, array['owner','admin']::app.membership_role[]));

create policy "accounts_household_member_select" on app.accounts
  for select using (app.user_is_household_member(household_id));
create policy "accounts_household_member_modify" on app.accounts
  for all using (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "account_balance_history_select_member" on app.account_balance_history
  for select using (
    exists (
      select 1 from app.accounts a
      where a.id = account_balance_history.account_id
        and app.user_is_household_member(a.household_id)
    )
  );
create policy "account_balance_history_modify_member" on app.account_balance_history
  for all using (
    exists (
      select 1 from app.accounts a
      where a.id = account_balance_history.account_id
        and app.user_has_household_role(a.household_id, array['owner','admin','member']::app.membership_role[])
    )
  )
  with check (
    exists (
      select 1 from app.accounts a
      where a.id = account_balance_history.account_id
        and app.user_has_household_role(a.household_id, array['owner','admin','member']::app.membership_role[])
    )
  );

create policy "category_groups_member" on app.category_groups
  for all using (app.user_is_household_member(household_id))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "categories_member" on app.categories
  for all using (app.user_is_household_member(household_id))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "category_targets_member" on app.category_targets
  for all using (
    exists (
      select 1 from app.categories c
      where c.id = category_targets.category_id
        and app.user_is_household_member(c.household_id)
    )
  )
  with check (
    exists (
      select 1 from app.categories c
      where c.id = category_targets.category_id
        and app.user_has_household_role(c.household_id, array['owner','admin','member']::app.membership_role[])
    )
  );

create policy "budget_periods_member" on app.budget_periods
  for all using (app.user_is_household_member(household_id))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "budget_assignments_member" on app.budget_category_assignments
  for all using (
    exists (
      select 1 from app.budget_periods bp
      where bp.id = budget_category_assignments.budget_period_id
        and app.user_is_household_member(bp.household_id)
    )
  )
  with check (
    exists (
      select 1 from app.budget_periods bp
      where bp.id = budget_category_assignments.budget_period_id
        and app.user_has_household_role(bp.household_id, array['owner','admin','member']::app.membership_role[])
    )
  );

create policy "transactions_member" on app.transactions
  for all using (app.user_is_household_member(household_id))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "transaction_splits_member" on app.transaction_splits
  for all using (
    exists (
      select 1 from app.transactions t
      where t.id = transaction_splits.transaction_id
        and app.user_is_household_member(t.household_id)
    )
  )
  with check (
    exists (
      select 1 from app.transactions t
      where t.id = transaction_splits.transaction_id
        and app.user_has_household_role(t.household_id, array['owner','admin','member']::app.membership_role[])
    )
  );

create policy "transaction_attachments_member" on app.transaction_attachments
  for all using (
    exists (
      select 1 from app.transactions t
      where t.id = transaction_attachments.transaction_id
        and app.user_is_household_member(t.household_id)
    )
  )
  with check (
    exists (
      select 1 from app.transactions t
      where t.id = transaction_attachments.transaction_id
        and app.user_has_household_role(t.household_id, array['owner','admin','member']::app.membership_role[])
    )
  );

create policy "transaction_categorizations_member" on app.transaction_categorizations
  for all using (
    exists (
      select 1 from app.transactions t
      where t.id = transaction_categorizations.transaction_id
        and app.user_is_household_member(t.household_id)
    )
  )
  with check (
    exists (
      select 1 from app.transactions t
      where t.id = transaction_categorizations.transaction_id
        and app.user_has_household_role(t.household_id, array['owner','admin','member']::app.membership_role[])
    )
  );

create policy "transaction_rules_member" on app.transaction_rules
  for all using (app.user_is_household_member(household_id))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "goals_member" on app.goals
  for all using (app.user_is_household_member(household_id))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "recurring_plans_member" on app.recurring_plans
  for all using (app.user_is_household_member(household_id))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "subscription_insights_member" on app.subscription_insights
  for all using (app.user_is_household_member(household_id))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "cashflow_forecasts_member" on app.cashflow_forecasts
  for all using (app.user_is_household_member(household_id))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "monthly_insights_member" on app.monthly_insights
  for all using (app.user_is_household_member(household_id))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "import_jobs_member" on app.import_jobs
  for all using (app.user_is_household_member(household_id))
  with check (app.user_has_household_role(household_id, array['owner','admin','member']::app.membership_role[]));

create policy "audit_log_member_read" on app.audit_log
  for select using (household_id is not null and app.user_is_household_member(household_id));

-- Notifications
create policy "notifications_owner" on app.notifications
  for all using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
create policy "notification_prefs_owner" on app.user_notification_preferences
  for all using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

-- -----------------------------------------------------------------------------
-- Grants
-- -----------------------------------------------------------------------------
grant usage on schema app to authenticated;
grant select, insert, update, delete on all tables in schema app to authenticated;
grant select on all tables in schema app to authenticated;
grant usage, select on all sequences in schema app to authenticated;

commit;
