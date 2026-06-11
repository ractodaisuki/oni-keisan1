#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import datetime as dt
import json
import sys
import urllib.parse
import urllib.request
import urllib.error

SUPABASE_URL = "https://ophekowkwdugfvkmyfom.supabase.co"
SUPABASE_KEY = "sb_publishable_kcHCM_F3FlQyRjdA2nkI8A_ti-4nVSZ"
VIEW = "oni_daily_stats_public"

JST = dt.timezone(dt.timedelta(hours=9))
today = dt.datetime.now(JST).date()
start = today - dt.timedelta(days=45)

params = urllib.parse.urlencode({
    "select": "local_date,stages_played,questions_answered,correct_answers,best_reached_back,best_cleared_back,max_unlocked_back,all_clear_count,last_played_at",
    "local_date": f"gte.{start.isoformat()}",
    "order": "local_date.asc",
})
url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{VIEW}?{params}"
req = urllib.request.Request(url, headers={
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Accept": "application/json",
})

try:
    with urllib.request.urlopen(req, timeout=20) as res:
        rows = json.loads(res.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    # SQL未適用（Viewなし）などはcronで毎日エラー通知しない。
    if e.code in (404, 401, 403):
        sys.exit(0)
    raise
except Exception:
    # 一時的なネットワーク不調は静かにする（翌朝また試す）。
    sys.exit(0)

if not isinstance(rows, list):
    sys.exit(0)

by_date = {str(row.get("local_date")): row for row in rows if row.get("local_date")}
active_dates = sorted(d for d, row in by_date.items() if int(row.get("stages_played") or 0) > 0)

def shift(date_s, days):
    return (dt.date.fromisoformat(date_s) + dt.timedelta(days=days)).isoformat()

# 今日の記録があれば今日、なければ昨日、それもなければ最後の記録。
today_s = today.isoformat()
yesterday_s = (today - dt.timedelta(days=1)).isoformat()
if today_s in by_date:
    target_date = today_s
    label = "今日"
elif yesterday_s in by_date:
    target_date = yesterday_s
    label = "昨日"
elif active_dates:
    target_date = active_dates[-1]
    label = target_date
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

questions = int(row.get("questions_answered") or 0)
correct = int(row.get("correct_answers") or 0)
stages = int(row.get("stages_played") or 0)
best_reached = int(row.get("best_reached_back") or 0)
best_cleared = int(row.get("best_cleared_back") or 0)
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
