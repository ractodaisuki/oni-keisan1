# oni-keisan1
鬼トレの鬼計算をChat-GTPにpyxelで作ってもらいました

GitHub Pages: https://ractodaisuki.github.io/oni-keisan1/
起動リンク: https://ractodaisuki.github.io/oni-keisan1/
Pyxel版: https://ractodaisuki.github.io/oni-keisan1/pyxel.html

## 統計記録 / Supabase 連携

Web版はステージ終了ごとに結果を記録します。

- ブラウザの `localStorage` に当日サマリー・生イベント・最高到達back（`bestStage`）を保存。リロードしても残ります。
- 画面上部に「TODAY 正解/解答数」「BEST TODAY n-BACK」「STREAK 連続日数」を表示。
- `config.js` に Supabase の `supabaseUrl` と `supabaseAnonKey`（publishable / anon キー）が設定されていれば、同じ結果を Supabase の `oni_sessions` テーブルへ INSERT します。送信に失敗してもゲームは止まらず、次回起動時に再送します。

Hermes の朝 cron は Supabase の日次サマリーを読み、Telegram に通知します。

### セットアップ

1. Supabase で `oni-supabase-setup.sql` を SQL Editor に貼って実行（`oni_sessions` テーブル + INSERT専用RLS + 日次サマリーView）。
2. Project Settings → API の `Project URL` と anon / publishable key を `config.js` に設定。**ここに置いてよいのは anon / publishable キーだけ。`service_role` キーはアプリ/リポジトリに絶対に書かない。**
3. Hermes の朝通知は `oni_daily_stats_public` View を publishable key で読みます。より厳密に非公開にしたい場合は、このViewを作らず、Hermes側だけに service_role キーを置いてください。

`config.js` の anon / publishable キーは公開 GitHub Pages に出ても問題ありません（RLS が INSERT のみ許可し、読み取りは日次集計Viewだけに限定するため）。

### Hermes 朝通知

このリポジトリの設定値に合わせて、Hermes 側に `oni_keisan_morning_ping.sh` を置くと、毎朝の cron で以下を通知できます。

- 対象: JSTの今日。まだ今日の記録がなければ昨日。
- 内容: 解いた問題数、正解数、最高到達、最高クリア、現在の連続日数。
- Supabase 側で `oni_daily_stats_public` が未作成の場合は静かに終了します。
