# Research & Design Decisions

## Summary
- **Feature**: `trade-document-ocr-json`
- **Discovery Scope**: New Feature（greenfield / PoC）
- **Key Findings**:
  - 既存実装コードがないため、steering の方針をそのまま設計境界に落とすのが最短。
  - PoC では OCR 精度最大化よりも、JSON正規化と数値整合チェックの再現性が重要。
  - DDD 4層（controller/application/domain/infrastructure）で責務を固定すると、後続タスク分割が容易。

## Research Log

### プロジェクト現況の確認
- **Context**: 新規 spec の設計にあたり、既存コードの有無と前提を確認する必要があった。
- **Sources Consulted**: `.kiro/steering/product.md`, `.kiro/steering/tech.md`, `.kiro/steering/structure.md`, `.kiro/specs/trade-document-ocr-json/requirements.md`
- **Findings**:
  - 実装コードは未着手で、PoC を迅速に成立させる方針。
  - 技術スタックは React / FastAPI / SQLite / Ollama で固定済み。
  - セキュリティ監査・可観測性は PoC では対象外。
- **Implications**:
  - 設計は実装可能性を重視し、抽象化を最小化する。
  - 境界外を先に定義してスコープ膨張を防ぐ。

### OCRからJSON化までの責務分離
- **Context**: 要件はアップロード、OCR、正規化、整合チェック、結果提示までを含む。
- **Sources Consulted**: `requirements.md`（Requirement 1〜5）, `tech.md`, `structure.md`
- **Findings**:
  - 入出力境界は API（controller）と JSON 契約（application）で分離可能。
  - 計算整合ルールは domain に閉じ込めるとテストしやすい。
  - Ollama 呼び出しは infrastructure adapter として隔離すべき。
- **Implications**:
  - 各層の変更責務が明確になり、タスク並列化が可能になる。
  - 将来的なモデル変更時も domain への影響を最小化できる。

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| DDD Layered | controller/application/domain/infrastructure の4層 | 責務分離が明確、PoCでも保守性を確保 | 初期ファイル数が増える | steering 方針と一致 |
| 単一サービス直結 | 1サービスにOCR/正規化/判定を集約 | 初速が速い | 責務混在で拡張時に破綻しやすい | PoC後半で負債化しやすい |

## Design Decisions

### Decision: DDD 4層を PoC でも適用
- **Context**: 要件が複数責務（OCR、正規化、整合判定）を含むため、境界が必要。
- **Alternatives Considered**:
  1. 単一サービス方式
  2. DDD 4層方式
- **Selected Approach**: DDD 4層方式を採用し、入出力・業務ルール・外部依存を分離する。
- **Rationale**: 最小限の設計規律で、後続の仕様拡張に耐える。
- **Trade-offs**: 初期実装量は増えるが、変更時の影響範囲は小さくなる。
- **Follow-up**: task 生成時に層ごとに独立タスク化する。

### Decision: JSON正規化をアプリケーション責務に固定
- **Context**: 会社ごとの表現差を吸収し、標準キーへ統一する必要がある。
- **Alternatives Considered**:
  1. OCR adapter 側で正規化
  2. application 層で正規化
- **Selected Approach**: application 層でマッピングルールを適用して正規化する。
- **Rationale**: OCR エンジン変更時に正規化ロジックを維持しやすい。
- **Trade-offs**: application の責務が増えるが、外部依存分離の効果が高い。
- **Follow-up**: 正規化不能項目の扱いを一貫したエラー表現に統一する。

### Decision: 数値整合判定を domain で実施
- **Context**: 単価・数量・小計・税・合計の整合判定は業務ルールそのもの。
- **Alternatives Considered**:
  1. DB 保存時に判定
  2. domain service で判定
- **Selected Approach**: domain service で判定し、結果を application が JSON に付与する。
- **Rationale**: 判定ロジックのテスト容易性と再利用性が高い。
- **Trade-offs**: domain model 設計が必要になる。
- **Follow-up**: 境界値（端数、空値、税未記載）テストを優先する。

## Risks & Mitigations
- OCR 抽出欠損で JSON が不完全になる — 欠損項目を明示し、処理失敗ではなく要確認で返す。
- 書類形式差分で正規化不能が増える — 未対応項目を明示してマッピング辞書の改善対象を可視化する。
- 数値表現ゆれ（カンマ、通貨記号、税表示差）で誤判定が発生する — 正規化前処理ルールを明示し、domain テストで固定する。

## References
- `.kiro/steering/product.md` — プロダクト方針
- `.kiro/steering/tech.md` — 技術方針とPoC境界
- `.kiro/steering/structure.md` — レイヤー責務と依存方向
- `.kiro/specs/trade-document-ocr-json/requirements.md` — 要件定義
