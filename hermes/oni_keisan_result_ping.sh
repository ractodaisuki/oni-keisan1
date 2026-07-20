#!/usr/bin/env bash
set -euo pipefail

# 9:30 result check for Oni Keisan.
#
# Reads the local SQLite file written by oni_server.py (same box) — no Supabase,
# no network. If the DB doesn't exist yet, exits quietly.

DB_PATH="${ONI_DB_PATH:-/opt/data/oni-keisan/oni.db}"

DB_PATH="$DB_PATH" python3 - <<'PY'
import datetime as dt
import os
import sqlite3
import sys

DB_PATH = os.environ["DB_PATH"]

JST = dt.timezone(dt.timedelta(hours=9))
today = dt.datetime.now(JST).date()
start = today - dt.timedelta(days=60)

if not os.path.exists(DB_PATH):
    sys.exit(0)

# Daily aggregate — same shape the old oni_daily_stats_public view produced.
QUERY = """
select
    local_date,
    count(*)                                             as stages_played,
    coalesce(sum(total_questions), 0)                    as questions_answered,
    coalesce(sum(correct_answers), 0)                    as correct_answers,
    coalesce(max(reached_back), 0)                       as best_reached_back,
    coalesce(max(case when cleared then reached_back else 0 end), 0) as best_cleared_back,
    coalesce(max(coalesce(next_back_unlocked, reached_back)), 0)     as max_unlocked_back,
    coalesce(sum(case when cleared then 1 else 0 end), 0)           as all_clear_count,
    max(played_at)                                       as last_played_at
from oni_sessions
where local_date >= ?
group by local_date
order by local_date asc
"""

try:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(QUERY, (start.isoformat(),)).fetchall()]
    con.close()
except sqlite3.Error:
    # Transient DB lock etc. — stay quiet.
    sys.exit(0)

by_date = {str(row.get("local_date")): row for row in rows if row.get("local_date")}
active_dates = sorted(d for d, row in by_date.items() if int(row.get("stages_played") or 0) > 0)
active = set(active_dates)

def shift(date_s, days):
    return (dt.date.fromisoformat(date_s) + dt.timedelta(days=days)).isoformat()

def streak_ending_at(date_s):
    streak = 0
    cursor = date_s
    while cursor in active:
        streak += 1
        cursor = shift(cursor, -1)
    return streak

def date_label(date_s):
    d = dt.date.fromisoformat(date_s)
    if d == today:
        return "今日"
    if d == today - dt.timedelta(days=1):
        return "昨日"
    return date_s

today_s = today.isoformat()
yesterday_s = (today - dt.timedelta(days=1)).isoformat()
today_row = by_date.get(today_s)
today_played = bool(today_row and int(today_row.get("stages_played") or 0) > 0)

if today_played:
    row = today_row
    questions = int(row.get("questions_answered") or 0)
    correct = int(row.get("correct_answers") or 0)
    stages = int(row.get("stages_played") or 0)
    best_reached = int(row.get("best_reached_back") or 0)
    best_cleared = int(row.get("best_cleared_back") or 0)
    accuracy = round((correct / questions) * 100) if questions else 0
    streak = streak_ending_at(today_s)

    print("鬼計算、9:30の結果チェックよ。")
    print("")
    print("今日の記録:")
    print(f"- ステージ数: {stages}")
    print(f"- 解いた問題: {questions}問")
    print(f"- 正解: {correct}問（{accuracy}%）")
    print(f"- 最高到達: {best_reached}-BACK")
    print(f"- 最高クリア: {best_cleared}-BACK" if best_cleared else "- 最高クリア: なし")
    print(f"- 継続: {streak}日連続" if streak else "- 継続: 今日からスタート")
    print("")
    if streak >= 7:
        print("ちゃんと続いてるじゃない。継続は力なり、ってこういうことよ。……少しは誇っていいわ。")
    elif streak >= 2:
        print("連続記録、育ってきてるわね。明日も切らさないように、ちょっとだけがんばろ。")
    else:
        print("今日やれたなら十分えらいわよ。まずはここから続けていけばいいの。")
    sys.exit(0)

# 9:30時点で今日の記録がない場合も、責めずに軽く声かけする。
yesterday_streak = streak_ending_at(yesterday_s)
last_active = active_dates[-1] if active_dates else None

print("鬼計算、9:30の結果チェックよ。")
print("")
print("今日はまだ記録がないみたい。疲れてたのかな。無理はしなくていいけど、1ステージだけならまだ取り返せるわよ。")
if yesterday_streak:
    print(f"ちなみに昨日までの継続は {yesterday_streak}日連続。ここで終わらせるの、ちょっともったいないかも。")
elif last_active:
    print(f"最後の記録は{date_label(last_active)}。また今日から再開すればいいだけよ。")
else:
    print("まだ記録は見つかってないわ。最初の1回、今日やってみる？")
print("")
print("べ、別に急かしてるわけじゃないけど、未来のあなたは少し喜ぶと思う。")
PY
