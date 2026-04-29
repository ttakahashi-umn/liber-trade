# Implementation Plan

- [x] 1. API: process_id に紐づく案件一覧を返す
- [x] 1.1 repository に案件一覧モデルと取得処理を追加する
  - `process_id` 単位で案件配列を返せる
  - _Requirements: 2.1, 3.1_
- [x] 1.2 案件一覧 API (`GET /api/cases`) を追加する
  - `process_id` がない場合は 400
  - `process_id` 指定時に案件一覧を返す
  - _Requirements: 2.1, 2.2, 3.1_

- [x] 2. UI: 取り込み成功後に案件一覧へ遷移する
- [x] 2.1 取り込み成功時に案件一覧画面へ遷移する
  - 成功時のみ遷移し、失敗時は遷移しない
  - _Requirements: 1.1, 1.2_
- [x] 2.2 案件一覧パネルを実装する
  - 案件名と突合状況を表示する
  - 空状態を表示できる
  - _Requirements: 2.2, 3.2_

- [x] 3. Validation: APIとUIを検証する
- [x] 3.1 バックエンドAPIテストを追加する
  - 案件一覧取得の正常/異常系を確認する
  - _Requirements: 2.1, 2.2, 3.1_
