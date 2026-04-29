# プロジェクト構造

## 構成方針

プロジェクトは **プロジェクトメモリ + 仕様 + 実装** を軸に運用します。
実装フェーズでは、バックエンドを DDD 準拠レイヤー、フロントエンドを機能単位で分割し、PoC でも責務分離を維持します。

## ディレクトリパターン

### ステアリングメモリ
**場所**: `.kiro/steering/`  
**目的**: プロダクト方針・技術標準・構造原則など、プロジェクト全体の永続ガイダンスを保持する。  
**例**: `product.md` で事業方向と中核能力の方向性を定義する。

### 機能仕様
**場所**: `.kiro/specs/`  
**目的**: 要件・設計・タスク・検証メモなど、機能単位の仕様成果物を管理する。  
**例**: 機能フォルダに承認済み要件を置いてから設計とタスクへ進む。

### 実装コード（予定）
**場所**: `frontend/`, `backend/`  
**目的**: 実行コードをフロント/バックで分離し、それぞれの規約を明確化する。  
**例**: `backend` は DDD レイヤー、`frontend` は画面・機能単位で構成する。

### バックエンド層構造（DDD）
**場所**: `backend/src/`  
**目的**: `controller / application / domain / infrastructure` の4層で責務を分離する。  
**例**: HTTP 入出力は `controller`、ユースケースは `application`、業務ルールは `domain`、DB/Ollama 接続は `infrastructure`。

### フロントエンド機能構造
**場所**: `frontend/src/`  
**目的**: UI・状態管理・API 呼び出しを機能単位でまとめ、変更影響を局所化する。  
**例**: `features/<feature>/` 配下に `components`, `hooks`, `api`, `schema` を配置する。

## 命名規約

- **ファイル**: フロントは `kebab-case.ts(x)`、バックは `snake_case.py` を基本とする。
- **コンポーネント**: React コンポーネントは `PascalCase`。
- **関数/メソッド**: フロントは `camelCase`、バックは `snake_case`。
- **ドメイン用語**: 貿易業務の用語を優先し、汎用名より業務意味が伝わる命名を採用する。

## インポート方針

```typescript
// フロント: 機能内は相対 import、機能外参照は alias import を優先
import { DocumentTable } from "@/features/documents/components/document-table";
import { useMatchResult } from "../hooks/use-match-result";
```

**パスエイリアス**:
- `@/`: `frontend/src/` を指す。

```python
# バック: 層の依存方向を固定（controller -> application -> domain）
from app.application.usecases.create_case import CreateCaseUseCase
```

## コード構成原則

- 仕様で確定した要件を起点に実装し、PoC でも層の責務を崩さない。
- バックエンドは `domain` を中心に依存方向を内側へ向ける（外側層が内側層を利用）。
- フロントエンドは機能単位で閉じ、共通化は重複が明確になってから行う。
- DB（SQLite）や外部 AI（Ollama）へのアクセスは `infrastructure` に閉じ込める。
- 新規ファイルが既存パターンに従う限り steering は更新しない。新しい設計パターン導入時のみ更新する。

---
_ファイルツリーの列挙ではなく、再利用可能な構成パターンを記述する_
