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


-- =============================================================================
-- WORKOUT FEATURE
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 4. exercises
--    Global library (is_custom = false, created_by = NULL) seeded by the
--    backend.  Users can add their own custom exercises (is_custom = true).
-- ---------------------------------------------------------------------------
create table if not exists public.exercises (
    id           uuid primary key default gen_random_uuid(),
    name         text not null,
    muscle_group text not null check (muscle_group in
                     ('chest','back','shoulders','legs','arms','core','cardio')),
    equipment    text not null check (equipment in
                     ('barbell','dumbbell','machine','bodyweight','cable')),
    difficulty   text not null default 'beginner' check (difficulty in
                     ('beginner','intermediate','advanced')),
    is_custom    boolean not null default false,
    created_by   uuid references public.users (id) on delete cascade
);

-- One global name per exercise (partial index covers only non-custom rows).
create unique index if not exists uq_exercises_global_name
    on public.exercises (lower(name))
    where not is_custom;

create index if not exists idx_exercises_muscle_group
    on public.exercises (muscle_group);

create index if not exists idx_exercises_created_by
    on public.exercises (created_by)
    where is_custom;


-- ---------------------------------------------------------------------------
-- 5. workout_plans
--    AI-generated or user-created weekly templates.
-- ---------------------------------------------------------------------------
create table if not exists public.workout_plans (
    id               uuid primary key default gen_random_uuid(),
    user_id          uuid not null references public.users (id) on delete cascade,
    name             text not null,
    goal             text not null check (goal in ('strength','hypertrophy','endurance')),
    experience_level text not null,
    days_per_week    integer not null check (days_per_week between 1 and 7),
    created_at       timestamptz not null default now()
);

create index if not exists idx_workout_plans_user_id
    on public.workout_plans (user_id);


-- ---------------------------------------------------------------------------
-- 6. workout_plan_exercises
--    Each row is one exercise on one day of a plan.
-- ---------------------------------------------------------------------------
create table if not exists public.workout_plan_exercises (
    id           uuid primary key default gen_random_uuid(),
    plan_id      uuid not null references public.workout_plans (id) on delete cascade,
    exercise_id  uuid not null references public.exercises (id) on delete cascade,
    day_number   integer not null check (day_number between 1 and 7),
    sets         integer not null default 3,
    reps         integer not null default 10,
    rest_seconds integer not null default 60,
    order_in_day integer not null default 1
);

create index if not exists idx_wpe_plan_day
    on public.workout_plan_exercises (plan_id, day_number, order_in_day);


-- ---------------------------------------------------------------------------
-- 7. workout_logs
--    One row per completed session.
-- ---------------------------------------------------------------------------
create table if not exists public.workout_logs (
    id           uuid primary key default gen_random_uuid(),
    user_id      uuid not null references public.users (id) on delete cascade,
    plan_id      uuid references public.workout_plans (id) on delete set null,
    started_at   timestamptz,
    completed_at timestamptz,
    notes        text
);

create index if not exists idx_workout_logs_user_completed
    on public.workout_logs (user_id, completed_at desc);


-- ---------------------------------------------------------------------------
-- 8. workout_log_exercises
--    Per-exercise detail for each session.
--    sets_completed is a JSONB array: [{reps: int, weight_kg: float}, ...]
--    weight_kg = 0 for bodyweight exercises.
-- ---------------------------------------------------------------------------
create table if not exists public.workout_log_exercises (
    id                 uuid primary key default gen_random_uuid(),
    log_id             uuid not null references public.workout_logs (id) on delete cascade,
    exercise_id        uuid not null references public.exercises (id) on delete cascade,
    sets_completed     jsonb not null default '[]',
    order_in_workout   integer not null default 1
);

create index if not exists idx_wle_log_id
    on public.workout_log_exercises (log_id);


-- ---------------------------------------------------------------------------
-- 9. workout_xp
--    One row per user — upserted after every completed session.
-- ---------------------------------------------------------------------------
create table if not exists public.workout_xp (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null references public.users (id) on delete cascade,
    total_xp   integer not null default 0 check (total_xp >= 0),
    rank       text not null default 'Bronze',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (user_id)
);

drop trigger if exists trg_workout_xp_updated_at on public.workout_xp;
create trigger trg_workout_xp_updated_at
    before update on public.workout_xp
    for each row execute function public.set_updated_at();


-- =============================================================================
-- RLS — workout tables
-- service_client (service role key) bypasses these for backend writes.
-- =============================================================================

alter table public.exercises            enable row level security;
alter table public.workout_plans        enable row level security;
alter table public.workout_plan_exercises enable row level security;
alter table public.workout_logs         enable row level security;
alter table public.workout_log_exercises enable row level security;
alter table public.workout_xp           enable row level security;


-- --- exercises (global readable by everyone; custom readable only by owner) --

drop policy if exists "exercises: select global or own" on public.exercises;
drop policy if exists "exercises: insert own custom"    on public.exercises;
drop policy if exists "exercises: delete own custom"    on public.exercises;

create policy "exercises: select global or own"
    on public.exercises for select
    using (not is_custom or auth.uid() = created_by);

create policy "exercises: insert own custom"
    on public.exercises for insert
    with check (is_custom and auth.uid() = created_by);

create policy "exercises: delete own custom"
    on public.exercises for delete
    using (is_custom and auth.uid() = created_by);


-- --- workout_plans -----------------------------------------------------------

drop policy if exists "workout_plans: select own" on public.workout_plans;
drop policy if exists "workout_plans: insert own" on public.workout_plans;
drop policy if exists "workout_plans: delete own" on public.workout_plans;

create policy "workout_plans: select own"
    on public.workout_plans for select
    using (auth.uid() = user_id);

create policy "workout_plans: insert own"
    on public.workout_plans for insert
    with check (auth.uid() = user_id);

create policy "workout_plans: delete own"
    on public.workout_plans for delete
    using (auth.uid() = user_id);


-- --- workout_plan_exercises (access via parent plan) -------------------------

drop policy if exists "wpe: select via own plan" on public.workout_plan_exercises;
drop policy if exists "wpe: insert via own plan" on public.workout_plan_exercises;

create policy "wpe: select via own plan"
    on public.workout_plan_exercises for select
    using (exists (
        select 1 from public.workout_plans p
        where p.id = plan_id and p.user_id = auth.uid()
    ));

create policy "wpe: insert via own plan"
    on public.workout_plan_exercises for insert
    with check (exists (
        select 1 from public.workout_plans p
        where p.id = plan_id and p.user_id = auth.uid()
    ));


-- --- workout_logs ------------------------------------------------------------

drop policy if exists "workout_logs: select own" on public.workout_logs;
drop policy if exists "workout_logs: insert own" on public.workout_logs;
drop policy if exists "workout_logs: delete own" on public.workout_logs;

create policy "workout_logs: select own"
    on public.workout_logs for select
    using (auth.uid() = user_id);

create policy "workout_logs: insert own"
    on public.workout_logs for insert
    with check (auth.uid() = user_id);

create policy "workout_logs: delete own"
    on public.workout_logs for delete
    using (auth.uid() = user_id);


-- --- workout_log_exercises (access via parent log) ---------------------------

drop policy if exists "wle: select via own log" on public.workout_log_exercises;
drop policy if exists "wle: insert via own log" on public.workout_log_exercises;

create policy "wle: select via own log"
    on public.workout_log_exercises for select
    using (exists (
        select 1 from public.workout_logs l
        where l.id = log_id and l.user_id = auth.uid()
    ));

create policy "wle: insert via own log"
    on public.workout_log_exercises for insert
    with check (exists (
        select 1 from public.workout_logs l
        where l.id = log_id and l.user_id = auth.uid()
    ));


-- --- workout_xp --------------------------------------------------------------

drop policy if exists "workout_xp: select own" on public.workout_xp;
drop policy if exists "workout_xp: insert own" on public.workout_xp;
drop policy if exists "workout_xp: update own" on public.workout_xp;

create policy "workout_xp: select own"
    on public.workout_xp for select
    using (auth.uid() = user_id);

create policy "workout_xp: insert own"
    on public.workout_xp for insert
    with check (auth.uid() = user_id);

create policy "workout_xp: update own"
    on public.workout_xp for update
    using (auth.uid() = user_id);


-- =============================================================================
-- HABIT TRACKER FEATURE
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 10. habits
--     One row per habit. Archived habits are hidden from the UI but kept for
--     historical completion data. frequency is 'daily' or 'weekly'.
--     target_per_week controls how many days per week a weekly habit targets.
--     Daily habits always target 7; this column is most meaningful for weekly.
-- ---------------------------------------------------------------------------
create table if not exists public.habits (
    id              uuid primary key default gen_random_uuid(),
    user_id         uuid not null references public.users (id) on delete cascade,
    name            text not null,
    description     text,
    frequency       text not null default 'daily'
                        check (frequency in ('daily', 'weekly')),
    target_per_week integer not null default 7
                        check (target_per_week >= 1 and target_per_week <= 7),
    archived        boolean not null default false,
    created_at      timestamptz not null default now()
);

create index if not exists idx_habits_user_active
    on public.habits (user_id)
    where not archived;


-- ---------------------------------------------------------------------------
-- 11. habit_completions
--     One row per (habit, calendar day). The unique constraint prevents
--     double-completing the same habit on the same day.
-- ---------------------------------------------------------------------------
create table if not exists public.habit_completions (
    id           uuid primary key default gen_random_uuid(),
    habit_id     uuid not null references public.habits (id) on delete cascade,
    user_id      uuid not null references public.users (id) on delete cascade,
    completed_at date not null default current_date,
    notes        text,
    created_at   timestamptz not null default now(),

    unique (habit_id, completed_at)
);

create index if not exists idx_habit_completions_user_date
    on public.habit_completions (user_id, completed_at desc);

create index if not exists idx_habit_completions_habit_date
    on public.habit_completions (habit_id, completed_at desc);


-- ---------------------------------------------------------------------------
-- 12. habit_xp
--     One row per user — upserted after every completion.
-- ---------------------------------------------------------------------------
create table if not exists public.habit_xp (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null references public.users (id) on delete cascade,
    total_xp   integer not null default 0 check (total_xp >= 0),
    rank       text not null default 'Bronze',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (user_id)
);

drop trigger if exists trg_habit_xp_updated_at on public.habit_xp;
create trigger trg_habit_xp_updated_at
    before update on public.habit_xp
    for each row execute function public.set_updated_at();


-- =============================================================================
-- RLS — habit tables
-- =============================================================================

alter table public.habits             enable row level security;
alter table public.habit_completions  enable row level security;
alter table public.habit_xp           enable row level security;


-- --- habits ------------------------------------------------------------------

drop policy if exists "habits: select own"  on public.habits;
drop policy if exists "habits: insert own"  on public.habits;
drop policy if exists "habits: update own"  on public.habits;
drop policy if exists "habits: delete own"  on public.habits;

create policy "habits: select own"
    on public.habits for select
    using (auth.uid() = user_id);

create policy "habits: insert own"
    on public.habits for insert
    with check (auth.uid() = user_id);

create policy "habits: update own"
    on public.habits for update
    using (auth.uid() = user_id);

create policy "habits: delete own"
    on public.habits for delete
    using (auth.uid() = user_id);


-- --- habit_completions -------------------------------------------------------

drop policy if exists "habit_completions: select own"  on public.habit_completions;
drop policy if exists "habit_completions: insert own"  on public.habit_completions;
drop policy if exists "habit_completions: delete own"  on public.habit_completions;

create policy "habit_completions: select own"
    on public.habit_completions for select
    using (auth.uid() = user_id);

create policy "habit_completions: insert own"
    on public.habit_completions for insert
    with check (auth.uid() = user_id);

create policy "habit_completions: delete own"
    on public.habit_completions for delete
    using (auth.uid() = user_id);


-- --- habit_xp ----------------------------------------------------------------

drop policy if exists "habit_xp: select own"  on public.habit_xp;
drop policy if exists "habit_xp: insert own"  on public.habit_xp;
drop policy if exists "habit_xp: update own"  on public.habit_xp;

create policy "habit_xp: select own"
    on public.habit_xp for select
    using (auth.uid() = user_id);

create policy "habit_xp: insert own"
    on public.habit_xp for insert
    with check (auth.uid() = user_id);

create policy "habit_xp: update own"
    on public.habit_xp for update
    using (auth.uid() = user_id);


-- =============================================================================
-- Starter exercise library (47 exercises across all muscle groups)
-- Guarded by DO block — safe to re-run.
-- =============================================================================
do $$
begin
  if not exists (select 1 from public.exercises where not is_custom limit 1) then
    insert into public.exercises (name, muscle_group, equipment, difficulty, is_custom) values
      -- CHEST
      ('Barbell Bench Press',       'chest',     'barbell',    'intermediate', false),
      ('Dumbbell Bench Press',      'chest',     'dumbbell',   'beginner',     false),
      ('Incline Barbell Press',     'chest',     'barbell',    'intermediate', false),
      ('Incline Dumbbell Press',    'chest',     'dumbbell',   'intermediate', false),
      ('Decline Bench Press',       'chest',     'barbell',    'intermediate', false),
      ('Chest Fly',                 'chest',     'dumbbell',   'beginner',     false),
      ('Cable Crossover',           'chest',     'cable',      'intermediate', false),
      ('Push-Up',                   'chest',     'bodyweight', 'beginner',     false),
      -- BACK
      ('Barbell Deadlift',          'back',      'barbell',    'advanced',     false),
      ('Pull-Up',                   'back',      'bodyweight', 'intermediate', false),
      ('Barbell Row',               'back',      'barbell',    'intermediate', false),
      ('Dumbbell Row',              'back',      'dumbbell',   'beginner',     false),
      ('Lat Pulldown',              'back',      'machine',    'beginner',     false),
      ('Seated Cable Row',          'back',      'cable',      'beginner',     false),
      ('Face Pull',                 'back',      'cable',      'beginner',     false),
      ('Chest-Supported Row',       'back',      'dumbbell',   'beginner',     false),
      -- SHOULDERS
      ('Overhead Press',            'shoulders', 'barbell',    'intermediate', false),
      ('Dumbbell Shoulder Press',   'shoulders', 'dumbbell',   'beginner',     false),
      ('Lateral Raise',             'shoulders', 'dumbbell',   'beginner',     false),
      ('Front Raise',               'shoulders', 'dumbbell',   'beginner',     false),
      ('Arnold Press',              'shoulders', 'dumbbell',   'intermediate', false),
      ('Cable Lateral Raise',       'shoulders', 'cable',      'beginner',     false),
      -- LEGS
      ('Barbell Squat',             'legs',      'barbell',    'intermediate', false),
      ('Romanian Deadlift',         'legs',      'barbell',    'intermediate', false),
      ('Leg Press',                 'legs',      'machine',    'beginner',     false),
      ('Leg Curl',                  'legs',      'machine',    'beginner',     false),
      ('Leg Extension',             'legs',      'machine',    'beginner',     false),
      ('Dumbbell Lunge',            'legs',      'dumbbell',   'beginner',     false),
      ('Bulgarian Split Squat',     'legs',      'dumbbell',   'intermediate', false),
      ('Hip Thrust',                'legs',      'barbell',    'intermediate', false),
      ('Calf Raise',                'legs',      'machine',    'beginner',     false),
      ('Goblet Squat',              'legs',      'dumbbell',   'beginner',     false),
      -- ARMS
      ('Barbell Curl',              'arms',      'barbell',    'beginner',     false),
      ('Dumbbell Curl',             'arms',      'dumbbell',   'beginner',     false),
      ('Hammer Curl',               'arms',      'dumbbell',   'beginner',     false),
      ('Preacher Curl',             'arms',      'machine',    'beginner',     false),
      ('Tricep Pushdown',           'arms',      'cable',      'beginner',     false),
      ('Skull Crusher',             'arms',      'barbell',    'intermediate', false),
      ('Overhead Tricep Extension', 'arms',      'dumbbell',   'beginner',     false),
      ('Diamond Push-Up',           'arms',      'bodyweight', 'intermediate', false),
      -- CORE
      ('Plank',                     'core',      'bodyweight', 'beginner',     false),
      ('Crunch',                    'core',      'bodyweight', 'beginner',     false),
      ('Ab Wheel Rollout',          'core',      'bodyweight', 'intermediate', false),
      ('Hanging Leg Raise',         'core',      'bodyweight', 'intermediate', false),
      ('Cable Crunch',              'core',      'cable',      'beginner',     false),
      -- CARDIO
      ('Treadmill Run',             'cardio',    'machine',    'beginner',     false),
      ('Rowing Machine',            'cardio',    'machine',    'beginner',     false),
      ('Stationary Bike',           'cardio',    'machine',    'beginner',     false),
      ('Jump Rope',                 'cardio',    'bodyweight', 'beginner',     false),
      ('Burpees',                   'cardio',    'bodyweight', 'intermediate', false);
  end if;
end $$;
