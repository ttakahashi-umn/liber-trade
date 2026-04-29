# Requirements Document

## Introduction
本仕様は、書類取り込み直後に紐づく案件一覧へ遷移し、突合状況を一覧で確認できる機能を追加する。
対象利用者は営業事務および貿易実務担当であり、取り込み後の追跡性を高めることを目的とする。

## Boundary Context (Optional)
- **In scope**: 取り込み直後の案件一覧遷移、案件一覧表示、突合状況の可視化
- **Out of scope**: 高度な検索/絞り込み機能、権限制御、監査ログ設計
- **Adjacent expectations**: 取り込み処理側が `process_id` を返却できること

## Requirements

### Requirement 1: 取り込み直後の案件一覧遷移
**Objective:** As a 営業事務または貿易実務担当, I want 書類取り込み完了後に案件一覧へ自動遷移したい, so that 次の確認作業へ迷わず進める

#### Acceptance Criteria
1. When 書類取り込みAPIが成功したとき, the Document UI shall 案件一覧画面へ遷移する
2. If 取り込みに失敗したとき, the Document UI shall 案件一覧へ遷移せずエラーを表示する

### Requirement 2: 紐づく案件一覧の表示
**Objective:** As a 営業事務または貿易実務担当, I want 取り込み書類に紐づく案件を一覧で見たい, so that 現在の処理状況を俯瞰できる

#### Acceptance Criteria
1. When 利用者が案件一覧画面を表示したとき, the Case List Service shall `process_id` に紐づく案件一覧を返す
2. If 紐づく案件が存在しないとき, the Case List Service shall 空状態であることを明示する

### Requirement 3: 突合状況の可視化
**Objective:** As a 貿易実務担当, I want 各案件の突合状況を確認したい, so that 要確認案件を素早く把握できる

#### Acceptance Criteria
1. The Case List Service shall 各案件に突合状況（例: OK / 要確認 / 未処理）を含めて返す
2. When 案件一覧が表示されるとき, the Document UI shall 案件名と突合状況を同時に表示する
