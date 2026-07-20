# oni-keisan1

鬼トレの鬼計算をChat-GPTにpyxelで作ってもらいました。

## 構成 / Architecture

Web版は **Hermes VPS 上でセルフホスト**しています（Tailscale の tailnet 内のみ）。
以前の GitHub Pages + Supabase 構成は撤去しました。1つの箱が配信・保存・通知を
すべて担い、公開インターネットには一切露出しません。

- **アプリURL:** `https://hermes-vps.tailb21a4e.ts.net/oni/`（`tailscale serve` が
  TLS終端して `oni_server.py` へproxy。tailnet内からのみ到達可能）
- **サーバー:** `hermes/oni_server.py` — Python標準ライブラリのみ（依存ゼロ）。静的配信 +
  `POST …/sessions` を受けて SQLite に記録。`127.0.0.1:8102` でlisten、systemd
  `oni-keisan.service` で常駐。
- **DB:** SQLite（`oni_sessions` テーブル、`event_id` UNIQUE で重複排除）。
- **同期:** ステージ終了ごとに `app.js` が同じオリジンの `sessions` へ POST。ブラウザの
  `localStorage` にも当日サマリー・最高到達backを保存し、送信失敗時はキューして次回再送。
  同一オリジンなので CORS も API キーも不要（`config.js` は `statsEndpoint` のみ）。

## 通知 / Notifications

Hermes の agent が以下のスクリプトを定時実行し、Telegram に通知します。いずれも
ローカルの SQLite を直接読みます（Supabaseなし）。

- `hermes/oni_keisan_morning_start.sh` — 朝の脳トレ促し（名言 + アプリURL）
- `hermes/oni_keisan_morning_ping.sh` — 当日サマリー（解答数・正解・最高到達・連続日数）
- `hermes/oni_keisan_result_ping.sh` — 9:30 の結果チェック

## デプロイ / Deploy

`hermes/` 配下が Hermes 上の配置物です。

1. `oni_server.py` を `/opt/data/oni-keisan/` に、静的ファイル（`index.html`,
   `app.js`, `config.js`, `styles.css`, `pyxel.html`）を `/opt/data/oni-keisan/public/` に置く。
2. `oni-keisan.service` を `/etc/systemd/system/` に入れて `systemctl enable --now oni-keisan`。
3. `tailscale serve --bg --set-path /oni http://127.0.0.1:8102`。
4. 通知スクリプト3本を `/opt/data/scripts/` に配置。

## Pyxel版

`pyxel.html`（別バリアント）。
