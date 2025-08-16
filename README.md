## JSON Echo Server

### 概要 (Overview)

**日本語**

JSON Echo Server は、最初のパス要素に応じて固定レスポンスを返すシンプルなモックサーバです。  
拡張子に応じて Content-Type が自動判定されます（`.json` / `.html` / `.txt` / その他）。  
ローカル開発やCIテストで外部APIの代わりに利用できます。

**English**

JSON Echo Server is a simple mock server that returns fixed responses based on the first path segment.  
Content-Type is automatically set based on the file extension (`.json`, `.html`, `.txt`, or others).  
It is useful for local development and CI tests as a drop-in replacement for external APIs.

* `http://localhost:4000/json1/...` → returns `fixtures/json1.json`
* `http://localhost:4000/html1/...` → returns `fixtures/html1.html`
* `http://localhost:4000/txt1/...` → returns `fixtures/txt1.txt`
* `http://localhost:4000/404/...` → returns HTTP status 404

---

### 使い方 (Usage)

**日本語**

1. `fixtures/` ディレクトリにレスポンスファイルを配置します
2. コンテナを起動します
3. リクエストを送信して確認します

**English**

1. Place response files into the `fixtures/` directory
2. Start the container
3. Send requests to verify responses

```bash
docker run -d -p 4000:4000 \
  -v $(pwd)/fixtures:/app/fixtures:ro \
  ghcr.io/kazuya-awano/json-echo:latest

# Examples
curl http://localhost:4000/json1/v1/chat/completions
curl http://localhost:4000/html1/anything
curl http://localhost:4000/404/test
```

---

### ヘルスチェック (Healthcheck)

* `GET /healthz` → Returns `{"ok":true}`

---

### 環境変数 (Environment Variables)

| 変数名 (Variable)   | 既定値 (Default) | 日本語説明 (Description JP)                    | English Description                                           |
| ---------------- | ------------- | ----------------------------------------- | ------------------------------------------------------------- |
| `PORT`           | `4000`        | サーバーのポート番号                                | Port number for the server                                    |
| `CORS_ORIGIN`    | `*`           | 許可するCORSのオリジン (カンマ区切り対応)                   | Allowed CORS origins (comma-separated)                        |
| `LATENCY_MS`     | `0`           | 疑似レイテンシ (ミリ秒)。指定すると全レスポンスに遅延を挿入            | Artificial response latency (ms). Adds delay to all responses |
| `RESP_HEADERS_*` | なし (None)     | 任意のレスポンスヘッダを追加。例：`RESP_HEADERS_X-Env=dev` | Add custom response headers. e.g. `RESP_HEADERS_X-Env=dev`    |
