# liber-trade

貿易書類の取り込み（画像）から OCR 抽出、JSON 正規化、数値整合チェックまでを行う PoC プロジェクトです。  
取り込み後は、紐づく案件一覧と突合状況を確認できます。

## セットアップ（Docker Compose）

### 前提

- Docker
- Docker Compose

### 起動

```bash
docker compose up --build
```

### Ollama 接続設定（.env）

プロジェクトルートに `.env` を作成し、以下を設定してください。

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2-vision
```

- サンプル: `backend/.env.example`
- Docker Compose では上記環境変数を `backend` サービスへ渡します。

### Ollama モデルの事前取得

`OLLAMA_MODEL=llama3.2-vision` を使う場合は、ホスト側で事前にモデルを取得してください。

```bash
ollama pull llama3.2-vision
```

モデル未取得のまま実行すると、`POST /api/documents/ingest` で 500 エラーになる場合があります。

### 停止

```bash
docker compose down
```

### ログ確認

```bash
docker compose logs -f
```

## アクセス先

- フロントエンド: `http://localhost:5173`
- バックエンド: `http://localhost:8000`
- ヘルスチェック: `http://localhost:8000/health`

## 主な API

- `POST /api/documents/ingest`
  - 画像ファイルをアップロードして取り込み処理を実行
- `GET /api/documents/{process_id}`
  - 取り込み結果（正規化JSON・整合判定）を取得
- `GET /api/cases?process_id={process_id}`
  - 取り込み結果に紐づく案件一覧（突合状況つき）を取得

## 補足

- フロントエンドからの `/api` リクエストは、Vite のプロキシ経由でバックエンドコンテナへ転送されます。
- PoC 版のため、検索・高度なフィルタ、認証/認可、監査機能は現時点では対象外です。