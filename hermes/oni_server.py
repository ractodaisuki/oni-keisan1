#!/usr/bin/env python3
"""Oni Keisan — static server + stats sink (Python stdlib only, no deps).

Serves the game's static files and accepts stage-result POSTs, storing them in a
local SQLite file. Meant to sit behind `tailscale serve` on /oni, so it listens
only on localhost and is reachable only from the tailnet. The morning cron reads
the same SQLite file directly (see oni_keisan_morning_ping.sh).

Replaces the old GitHub Pages + Supabase setup: one box now serves, stores, and
notifies, with zero public exposure and zero external dependencies.

  GET  /oni/            -> public/index.html
  GET  /oni/<file>      -> public/<file>
  POST /oni/sessions    -> INSERT OR IGNORE into oni_sessions (dedup by event_id)

The leading "/oni" prefix is optional in routing, so this works whether or not
`tailscale serve` strips the mount path before proxying.
"""

import json
import mimetypes
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
PUBLIC = BASE / "public"
DB_PATH = BASE / "oni.db"
HOST = "127.0.0.1"
PORT = 8102
MOUNT_PREFIX = "/oni"
MAX_BODY = 64 * 1024  # a single stage result is tiny; cap to reject junk.

# Columns the client is allowed to write (mirrors toRow() in app.js). Anything
# else in the POST body is ignored.
FIELDS = (
    "event_id",
    "session_id",
    "schema_version",
    "app",
    "event_type",
    "played_at",
    "local_date",
    "timezone_offset_minutes",
    "stage",
    "correct_answers",
    "total_questions",
    "accuracy",
    "cleared",
    "reached_back",
    "next_back_unlocked",
    "duration_ms",
    "source",
)

SCHEMA = """
create table if not exists oni_sessions (
    id                      integer primary key autoincrement,
    event_id                text not null unique,
    session_id              text,
    schema_version          integer not null default 1,
    app                     text,
    event_type              text,
    played_at               text not null,
    local_date              text not null,
    timezone_offset_minutes integer,
    stage                   integer not null default 0,
    correct_answers         integer not null default 0,
    total_questions         integer not null default 0,
    accuracy                real,
    cleared                 integer not null default 0,
    reached_back            integer not null default 0,
    next_back_unlocked      integer,
    duration_ms             integer,
    source                  text not null default 'web',
    created_at              text not null default (datetime('now'))
);
create index if not exists oni_sessions_local_date_idx on oni_sessions (local_date);
create index if not exists oni_sessions_played_at_idx on oni_sessions (played_at);
"""


def init_db():
    con = sqlite3.connect(DB_PATH)
    try:
        con.executescript(SCHEMA)
        con.commit()
    finally:
        con.close()


def clean_row(body):
    """Validate/normalise a POST body into a row dict, or raise ValueError."""
    if not isinstance(body, dict):
        raise ValueError("body must be a JSON object")

    event_id = body.get("event_id")
    if not isinstance(event_id, str) or not (1 <= len(event_id) <= 200):
        raise ValueError("event_id required")
    if not body.get("played_at") or not body.get("local_date"):
        raise ValueError("played_at and local_date required")

    def as_int(v, lo, hi, default=0):
        try:
            n = int(v)
        except (TypeError, ValueError):
            return default
        return max(lo, min(hi, n))

    row = {
        "event_id": event_id[:200],
        "session_id": str(body.get("session_id") or "")[:200] or None,
        "schema_version": as_int(body.get("schema_version"), 0, 1000, 1),
        "app": str(body.get("app") or "")[:80] or None,
        "event_type": str(body.get("event_type") or "")[:80] or None,
        "played_at": str(body.get("played_at"))[:64],
        "local_date": str(body.get("local_date"))[:32],
        "timezone_offset_minutes": as_int(body.get("timezone_offset_minutes"), -900, 900, 0),
        "stage": as_int(body.get("stage"), 0, 100),
        "correct_answers": as_int(body.get("correct_answers"), 0, 100000),
        "total_questions": as_int(body.get("total_questions"), 0, 100000),
        "accuracy": None,
        "cleared": 1 if body.get("cleared") else 0,
        "reached_back": as_int(body.get("reached_back"), 0, 100),
        "next_back_unlocked": as_int(body.get("next_back_unlocked"), 0, 100, None)
        if body.get("next_back_unlocked") is not None
        else None,
        "duration_ms": as_int(body.get("duration_ms"), 0, 24 * 3600 * 1000, None)
        if body.get("duration_ms") is not None
        else None,
        "source": str(body.get("source") or "web")[:40],
    }
    # correct can't exceed total; derive accuracy server-side (ignore client value).
    row["correct_answers"] = min(row["correct_answers"], row["total_questions"])
    row["accuracy"] = (
        round(row["correct_answers"] / row["total_questions"], 4)
        if row["total_questions"]
        else 0.0
    )
    return row


def insert_row(row):
    """Return True if a new row was stored, False if it was a duplicate."""
    cols = ", ".join(FIELDS)
    placeholders = ", ".join(f":{f}" for f in FIELDS)
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.execute(
            f"insert or ignore into oni_sessions ({cols}) values ({placeholders})", row
        )
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()


class Handler(BaseHTTPRequestHandler):
    server_version = "OniKeisan/1.0"

    def _route(self):
        path = self.path.split("?", 1)[0]
        if path.startswith(MOUNT_PREFIX):
            path = path[len(MOUNT_PREFIX):] or "/"
        return path

    def _send_json(self, status, obj):
        payload = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self._route().rstrip("/") != "/sessions":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            self._send_json(400, {"error": "bad length"})
            return
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            row = clean_row(body)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json(400, {"error": str(exc)})
            return
        try:
            stored = insert_row(row)
        except sqlite3.Error as exc:
            self._send_json(500, {"error": f"db: {exc}"})
            return
        # Both a fresh insert and a dedup'd retry are "success" for the client,
        # so its pending queue can drain without double counting.
        self._send_json(200, {"status": "stored" if stored else "duplicate"})

    def do_GET(self):
        path = self._route()
        rel = path.lstrip("/") or "index.html"
        target = (PUBLIC / rel).resolve()
        # Path-traversal guard: must stay inside PUBLIC.
        if PUBLIC not in target.parents and target != PUBLIC:
            self.send_error(403)
            return
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):  # quieter journald logs
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    PUBLIC.mkdir(parents=True, exist_ok=True)
    init_db()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    sys.stderr.write(f"oni_server on http://{HOST}:{PORT} (db={DB_PATH})\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
