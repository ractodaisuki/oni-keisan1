-- Fix browser INSERT failures with Supabase publishable keys.
-- Run this in Supabase SQL Editor after oni-supabase-setup.sql if RESULT shows:
--   SYNC: queued / HTTP 401 ... new row violates row-level security policy
--
-- This is non-destructive. It does not drop oni_sessions or delete data.

alter table public.oni_sessions enable row level security;

drop policy if exists "anon can insert sessions" on public.oni_sessions;
drop policy if exists "public can insert sessions" on public.oni_sessions;

create policy "public can insert sessions"
  on public.oni_sessions
  for insert
  to public
  with check (true);

grant insert on public.oni_sessions to anon;
grant insert on public.oni_sessions to authenticated;
