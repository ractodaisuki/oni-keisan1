// Public runtime config for the Oni Calculation web app.
//
// These values are safe to commit and to expose on GitHub Pages:
//  - supabaseUrl is just the project URL.
//  - supabaseAnonKey is the *publishable* (anon) key. Row Level Security on the
//    oni_sessions table only allows INSERT, so a leaked anon key cannot read or
//    modify anyone's data.
//
// NEVER put the service_role key here. That key lives only on the Hermes box.
window.ONI_CONFIG = {
  supabaseUrl: "https://ophekowkwdugfvkmyfom.supabase.co",
  supabaseAnonKey: "sb_publishable_kcHCM_F3FlQyRjdA2nkI8A_ti-4nVSZ",
};
