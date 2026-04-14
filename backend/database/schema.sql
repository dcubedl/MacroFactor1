-- =============================================================================
-- LifeRanked — Supabase Database Schema
-- Run this in the Supabase SQL editor (Dashboard → SQL Editor → New query).
-- Safe to re-run: all statements use IF NOT EXISTS / OR REPLACE guards.
-- =============================================================================


-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
create extension if not exists "pgcrypto";   -- gen_random_uuid()


-- ---------------------------------------------------------------------------
-- 1. users
--    Mirrors auth.users so the app can store profile data alongside auth.
--    id is a foreign key into Supabase's managed auth schema.
-- ---------------------------------------------------------------------------
create table if not exists public.users (
    id          uuid primary key references auth.users (id) on delete cascade,
    username    text unique,
    email       text unique not null,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

-- Keep updated_at current automatically
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_users_updated_at on public.users;
create trigger trg_users_updated_at
    before update on public.users
    for each row execute function public.set_updated_at();


-- ---------------------------------------------------------------------------
-- 2. food_scans
--    One row per photo scan. Macros come directly from Gemini; score and
--    rank are computed by the Python scoring service before insert.
-- ---------------------------------------------------------------------------
create table if not exists public.food_scans (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references public.users (id) on delete cascade,
    food_name   text not null,
    calories    numeric(7, 2),
    protein_g   numeric(6, 2),
    carbs_g     numeric(6, 2),
    fat_g       numeric(6, 2),
    fiber_g     numeric(6, 2),
    score       integer not null check (score >= 0 and score <= 100),
    rank        text not null,
    health_tip  text,
    image_url   text,                    -- optional: if you store the image in Supabase Storage
    created_at  timestamptz not null default now()
);

-- Indexes used by get_user_scans (filters on user_id, sorts by created_at)
create index if not exists idx_food_scans_user_id
    on public.food_scans (user_id);

create index if not exists idx_food_scans_user_created
    on public.food_scans (user_id, created_at desc);


-- ---------------------------------------------------------------------------
-- 3. daily_scores
--    Aggregated per-user per-day summary. Updated by the backend each time a
--    new scan is saved (upsert on user_id + date).
-- ---------------------------------------------------------------------------
create table if not exists public.daily_scores (
    id            uuid primary key default gen_random_uuid(),
    user_id       uuid not null references public.users (id) on delete cascade,
    date          date not null,
    average_score numeric(5, 2) not null check (average_score >= 0 and average_score <= 100),
    total_meals   integer not null default 0 check (total_meals >= 0),
    rank          text not null,
    created_at    timestamptz not null default now(),

    -- One summary row per user per day
    unique (user_id, date)
);

create index if not exists idx_daily_scores_user_date
    on public.daily_scores (user_id, date desc);


-- =============================================================================
-- Row Level Security
-- Each user can only read and write their own rows.
-- The Python backend uses the service role key (bypasses RLS) for writes;
-- these policies cover direct client access and the anon key read path.
-- =============================================================================

alter table public.users        enable row level security;
alter table public.food_scans   enable row level security;
alter table public.daily_scores enable row level security;


-- --- users -------------------------------------------------------------------

drop policy if exists "users: select own row"  on public.users;
drop policy if exists "users: insert own row"  on public.users;
drop policy if exists "users: update own row"  on public.users;
drop policy if exists "users: delete own row"  on public.users;

create policy "users: select own row"
    on public.users for select
    using (auth.uid() = id);

create policy "users: insert own row"
    on public.users for insert
    with check (auth.uid() = id);

create policy "users: update own row"
    on public.users for update
    using (auth.uid() = id);

create policy "users: delete own row"
    on public.users for delete
    using (auth.uid() = id);


-- --- food_scans --------------------------------------------------------------

drop policy if exists "food_scans: select own rows"  on public.food_scans;
drop policy if exists "food_scans: insert own rows"  on public.food_scans;
drop policy if exists "food_scans: delete own rows"  on public.food_scans;

create policy "food_scans: select own rows"
    on public.food_scans for select
    using (auth.uid() = user_id);

create policy "food_scans: insert own rows"
    on public.food_scans for insert
    with check (auth.uid() = user_id);

-- Updates are intentionally omitted — scan results are immutable once saved.

create policy "food_scans: delete own rows"
    on public.food_scans for delete
    using (auth.uid() = user_id);


-- --- daily_scores ------------------------------------------------------------

drop policy if exists "daily_scores: select own rows"  on public.daily_scores;
drop policy if exists "daily_scores: insert own rows"  on public.daily_scores;
drop policy if exists "daily_scores: update own rows"  on public.daily_scores;
drop policy if exists "daily_scores: delete own rows"  on public.daily_scores;

create policy "daily_scores: select own rows"
    on public.daily_scores for select
    using (auth.uid() = user_id);

create policy "daily_scores: insert own rows"
    on public.daily_scores for insert
    with check (auth.uid() = user_id);

create policy "daily_scores: update own rows"
    on public.daily_scores for update
    using (auth.uid() = user_id);

create policy "daily_scores: delete own rows"
    on public.daily_scores for delete
    using (auth.uid() = user_id);
