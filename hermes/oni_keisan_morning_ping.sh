#!/usr/bin/env bash
set -euo pipefail

# Morning Telegram summary for Oni Keisan.
#
# Reads the local SQLite file written by oni_server.py (same box) — no Supabase,
# no network. If the DB doesn't exist yet, exits quietly so cron stays silent.

DB_PATH="${ONI_DB_PATH:-/opt/data/oni-keisan/oni.db}"

DB_PATH="$DB_PATH" python3 - <<'PY'
import datetime as dt
import os
import sqlite3
import sys

DB_PATH = os.environ["DB_PATH"]
if not os.path.exists(DB_PATH):
    # Server not deployed / no plays yet: don't nag every morning.
    sys.exit(0)

JST = dt.timezone(dt.timedelta(hours=9))
today = dt.datetime.now(JST).date()
start = today - dt.timedelta(days=45)

# Daily aggregate — same shape the old oni_daily_stats_public view produced.
QUERY = """
select
    local_date,
    count(*)                                             as stages_played,
    coalesce(sum(total_questions), 0)                    as questions_answered,
    coalesce(sum(correct_answers), 0)                    as correct_answers,
    coalesce(max(reached_back), 0)                       as best_reached_back,
    coalesce(max(case when cleared then reached_back else 0 end), 0) as best_cleared_back
from oni_sessions
where local_date >= ?
group by local_date
order by local_date asc
"""

try:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(QUERY, (start.isoformat(),)).fetchall()
    con.close()
except sqlite3.Error:
    # Transient DB lock etc. — stay quiet, try again tomorrow.
    sys.exit(0)

by_date = {str(r["local_date"]): r for r in rows if r["local_date"]}
active_dates = sorted(d for d, r in by_date.items() if int(r["stages_played"] or 0) > 0)

def shift(date_s, days):
    return (dt.date.fromisoformat(date_s) + dt.timedelta(days=days)).isoformat()

today_s = today.isoformat()
yesterday_s = (today - dt.timedelta(days=1)).isoformat()
if today_s in by_date:
    target_date, label = today_s, "今日"
elif yesterday_s in by_date:
    target_date, label = yesterday_s, "昨日"
elif active_dates:
    target_date, label = active_dates[-1], active_dates[-1]
else:
    print("おはよ。鬼計算、まだ記録がないみたい。今日ちょっとだけでもやる？")
    sys.exit(0)

row = by_date[target_date]

# 連続日数: 今日プレイ済みなら今日から、未プレイなら昨日から数える。
active = set(active_dates)
cursor = today_s if today_s in active else yesterday_s
streak = 0
while cursor in active:
    streak += 1
    cursor = shift(cursor, -1)

questions = int(row["questions_answered"] or 0)
correct = int(row["correct_answers"] or 0)
stages = int(row["stages_played"] or 0)
best_reached = int(row["best_reached_back"] or 0)
best_cleared = int(row["best_cleared_back"] or 0)
accuracy = round((correct / questions) * 100) if questions else 0

print("おはよ。鬼計算、ちゃんと見ておいたわよ。")
print("")
print(f"{label}の記録:")
print(f"- ステージ数: {stages}")
print(f"- 解いた問題: {questions}問")
print(f"- 正解: {correct}問（{accuracy}%）")
print(f"- 最高到達: {best_reached}-BACK")
print(f"- 最高クリア: {best_cleared}-BACK" if best_cleared else "- 最高クリア: なし")
print(f"- 継続: {streak}日連続" if streak else "- 継続: まだなし")
print("")
print("べ、別に褒めてるわけじゃないけど、続いてるならえらいじゃない。")
PY
