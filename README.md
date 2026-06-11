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

Hermes の朝 cron がこの `oni_sessions` を service_role キーで読み、Telegram に通知します。

### セットアップ

1. Supabase で `oni-supabase-setup.sql` を SQL Editor に貼って実行（`oni_sessions` テーブル + INSERT専用RLS）。
2. Project Settings → API の `Project URL` と anon (publishable) key を `config.js` に設定。**ここに置いてよいのは anon キーだけ。`service_role` キーはアプリ/リポジトリに絶対に書かない。**
3. service_role キーは Hermes 側にのみ置く。

`config.js` の anon キーは公開 GitHub Pages に出ても問題ありません（RLS が INSERT のみ許可するため読み取り・改ざん不可）。
