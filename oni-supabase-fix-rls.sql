-- Oni Keisan — robust RLS repair for Supabase REST inserts.
--
-- Run this in Supabase SQL Editor if RESULT shows:
--   SYNC: queued / HTTP 401 ... new row violates row-level security policy
--
-- This is non-destructive. It does not drop oni_sessions or delete data.
-- It removes ONLY policies attached to public.oni_sessions, then recreates the
-- intended INSERT-only policy for browser/API-key writes.

alter table public.oni_sessions enable row level security;

-- Remove every existing policy on this table, including accidentally-created
-- restrictive policies or differently-named policies from earlier attempts.
do $$
declare
  policy_record record;
begin
  for policy_record in
    select policyname
    from pg_policies
    where schemaname = 'public'
      and tablename = 'oni_sessions'
  loop
    execute format('drop policy if exists %I on public.oni_sessions', policy_record.policyname);
  end loop;
end $$;

-- Supabase REST calls made from the static app use the publishable/anon API key.
-- Keep raw rows private: INSERT is allowed, but no SELECT/UPDATE/DELETE policy is
-- created for the base table.
create policy "oni_sessions_insert_from_browser"
  on public.oni_sessions
  as permissive
  for insert
  to anon, authenticated
  with check (true);

-- Table privileges are separate from RLS policies.
grant usage on schema public to anon, authenticated;
grant insert on public.oni_sessions to anon, authenticated;

-- Refresh PostgREST schema/policy cache quickly.
notify pgrst, 'reload schema';
