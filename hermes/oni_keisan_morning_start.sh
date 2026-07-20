#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import datetime as dt

# Served by oni_server.py behind tailscale serve /oni (tailnet only).
APP_URL = "https://hermes-vps.tailb21a4e.ts.net/oni/"
JST = dt.timezone(dt.timedelta(hours=9))
today = dt.datetime.now(JST).date()

quotes = [
    ("今日もがんばろう。小さく始めれば、それで勝ちだから。", None),
    ("継続は力なり。1回分の積み重ね、ちゃんと未来の自分が回収するわよ。", None),
    ("天才とは、1%のひらめきと99%の努力である。", "トーマス・エジソン"),
    ("困難の中に、機会がある。", "アルベルト・アインシュタイン"),
    ("成功は最終ではなく、失敗は致命的ではない。大切なのは続ける勇気である。", "ウィンストン・チャーチル"),
    ("千里の道も一歩から。今日はその一歩だけでいいの。", None),
    ("為せば成る。……って言うでしょ。まずは1ステージ、やってみなさい。", None),
    ("昨日より1問でも粘れたら、それはちゃんと前進よ。", None),
    ("脳みそ、起こす時間。べ、別に応援してるわけじゃないけど。", None),
    ("努力する人は希望を語り、怠ける人は不満を語る。", "井上靖"),
]
quote, author = quotes[today.toordinal() % len(quotes)]

print("おはよ。朝の脳トレの時間よ。")
print("")
if author:
    print(f"今日のひと言: 「{quote}」— {author}")
else:
    print(f"今日のひと言: {quote}")
print("")
print("鬼計算アプリ:")
print(APP_URL)
print("")
print("9:30に結果も見に行くから、ちょっとだけでも記録残しておきなさい。しょうがないなぁ、見守っててあげる。")
PY
