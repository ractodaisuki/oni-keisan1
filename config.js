// Public runtime config for the Oni Calculation web app.
//
// The app is now served by oni_server.py on Hermes, behind `tailscale serve` at
// /oni, reachable only from the tailnet. Stage results are POSTed to the same
// origin, so there is no Supabase project, no API keys, and no CORS.
//
// statsEndpoint is resolved relative to the page URL (…/oni/ -> …/oni/sessions),
// so it keeps working regardless of the mount path.
window.ONI_CONFIG = {
  statsEndpoint: "sessions",
};
