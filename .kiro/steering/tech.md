# 技術スタック

## アーキテクチャ

本プロジェクトは、PoC 検証を目的とした **DDD 準拠のレイヤードアーキテクチャ** を採用します。
上位方針は spec-first で進めつつ、実装は最小構成で素早く検証できることを優先します。

## 主要技術

- **フロントエンド**: React（最新安定版）
- **バックエンド**: FastAPI（最新安定版）
- **言語/ランタイム**: Python 3.14（指定）
- **データベース**: SQLite（PoC 用）
- **LLM/OCR**: 外部 Ollama + `llama3.2-vision`

## 主要ライブラリ

- **フロントエンド**
  - 状態管理: Zustand（現時点での採用方針）
  - API クライアント: OpenAPI からスタブ生成可能な fetch ベースのクライアント
  - フォーム/バリデーション: React Hook Form + Zod
- **バックエンド**
  - ORM/SQL: SQLAlchemy + Alembic
  - スキーマ: Pydantic v2

## 開発標準

### 型安全性

- フロントは TypeScript 前提で型安全を維持。
- バックエンドは Pydantic v2 を境界 DTO として利用し、層間の入出力を明確化。

### コード品質

- UI 設計（コンポーネント分割・命名規則・ディレクトリ規約）は一般的な推奨パターンに従う。
- バックエンドは `controller / application / domain / infrastructure` の責務分離を維持。
- HTTP 例外は共通ハンドリングし、エラーコード体系を持つ。
- 非同期処理（`async`）は積極的に活用する。

### テスト

- フロント: Vitest + Testing Library
- バック: pytest + httpx
- API 契約テスト: 実施する
- AI 回帰評価（固定サンプル）: 実施する

## 開発環境

### 必須ツール

- Cursor IDE
- Node.js（最新安定版）
- Python 3.14
- Ollama（同一ネットワーク上の外部ホスト）

### 共通コマンド
```bash
# ワークフローひな形の初期化/再生成
npx cc-sdd@latest --cursor-skills --lang ja --overwrite force -y

# Kiro ワークフロー
/kiro-discovery "<idea>"
/kiro-spec-init "<feature>"

# フロントエンド
npm run dev
npm run test
npm run lint
npm run format

# バックエンド
uv run fastapi dev app/main.py
uv run pytest
uv run alembic upgrade head
```

## 主要な技術判断

- 目的は本格運用ではなく、ビジネスモデル検証のための仮組み PoC とする。
- バージョン方針は原則「最新安定版」を採用する（Python は 3.14 固定）。
- DB は SQLite 前提で PoC を進め、PostgreSQL への移行は現時点で想定しない。
- マイグレーションは Alembic で運用する。
- Ollama 接続は「同一ネットワーク・認証なし・タイムアウトなし・再試行なし」とする。
- プロンプトはテンプレート化し、バージョン管理する。

## 保留事項 / 対象外（PoC）

- AI/OCR パイプライン詳細（画像前処理、出力スキーマ、信頼度設計、HITL 介入基準）は今後検討。
- セキュリティ/監査は PoC では実施しない。
- 秘密情報管理（`.env`、鍵運用）、監査ログ設計、個人情報マスキングは今後検討。
- 可観測性（ログ形式、メトリクス、リトライ/アラート）は今後検討。

---
_依存関係の網羅ではなく、標準とパターンを記述する_
