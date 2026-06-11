-- Oni Keisan — Supabase schema that the web app writes to.
--
-- This is the table/column layout app.js POSTs into (see toRow() in app.js).
-- If the oni-supabase-setup.sql you already ran differs, reconcile column
-- names with this file, otherwise the anon INSERT will be rejected.
--
-- Security model:
--   * The web app uses the ANON (publishable) key and may only INSERT.
--   * Hermes uses the SERVICE_ROLE key (bypasses RLS) to SELECT for the
--     morning summary. Keep service_role off the app/repo.
--
-- NOTE: this DROPS and recreates oni_sessions so the columns match the app
-- exactly. Safe while the table is empty (it has no real plays yet). If you
-- ever have data you want to keep, back it up before running this.

drop table if exists public.oni_sessions cascade;

create table public.oni_sessions (
  id                      bigint generated always as identity primary key,
  event_id                text not null unique,
  session_id              text,
  schema_version          integer not null default 1,
  app                     text not null,
  event_type              text not null,
  played_at               timestamptz not null,
  local_date              date not null,
  timezone_offset_minutes integer,
  stage                   integer not null,
  correct_answers         integer not null,
  total_questions         integer not null,
  accuracy                numeric,
  cleared                 boolean not null default false,
  reached_back            integer not null,
  next_back_unlocked      integer,
  duration_ms             bigint,
  source                  text not null default 'web',
  created_at              timestamptz not null default now()
);

create index if not exists oni_sessions_local_date_idx on public.oni_sessions (local_date);

-- Row Level Security: anon can INSERT only; no SELECT/UPDATE/DELETE for anon.
alter table public.oni_sessions enable row level security;

drop policy if exists "anon can insert sessions" on public.oni_sessions;
create policy "anon can insert sessions"
  on public.oni_sessions
  for insert
  to anon
  with check (true);
