# Design Document

## Overview
本機能は、書類取り込み成功後に案件一覧画面へ遷移し、取り込み結果に紐づく案件と突合状況を表示する。
既存の取り込みフローを維持しつつ、次アクションとなる確認作業への導線を短縮する。

### Goals
- 取り込み完了後に案件一覧へ遷移させる
- `process_id` に紐づく案件一覧を返却する API を追加する
- 案件一覧で突合状況を表示する

### Non-Goals
- 検索・絞り込み
- 認証・権限制御

## Boundary Commitments

### This Spec Owns
- 取り込み成功後の遷移制御
- 案件一覧 API とレスポンス
- 案件一覧 UI 表示

### Out of Boundary
- 案件作成ロジックの本格化
- 監査・可観測性

### Allowed Dependencies
- 既存の `DocumentResultRepository`
- 既存の取り込みAPIレスポンス (`process_id`)

### Revalidation Triggers
- 取り込みレスポンスの `process_id` 契約変更
- 案件ステータス定義の変更

## Architecture

### Architecture Pattern & Boundary Map
- backend controller に案件一覧 API を追加
- repository で `process_id` 単位の案件リストを返却
- frontend でアップロード成功後に案件一覧ページへ遷移

## File Structure Plan

### Modified Files
- `backend/app/infrastructure/persistence/repository.py` — 案件一覧保持/取得
- `backend/app/controller/document_ingest_controller.py` — `GET /api/cases` 追加
- `frontend/src/features/document-ingest/api/documentIngestApi.ts` — 案件API追加
- `frontend/src/app/routes.tsx` — 遷移状態追加
- `frontend/src/features/document-ingest/components/UploadForm.tsx` — 成功時遷移トリガ
- `frontend/src/features/document-ingest/components/ResultPanel.tsx` — 既存表示維持
- `frontend/src/features/document-ingest/components/CaseListPanel.tsx` — 新規

## Requirements Traceability

| Requirement | Summary | Components | Interfaces | Flows |
|-------------|---------|------------|------------|-------|
| 1.1 | 成功時遷移 | UploadForm, AppRoutes | ingestDocument | UI flow |
| 1.2 | 失敗時非遷移 | UploadForm | ingestDocument error | UI flow |
| 2.1 | 紐づく案件返却 | document_ingest_controller, repository | GET `/api/cases?process_id=` | API flow |
| 2.2 | 空状態明示 | CaseListPanel | cases response | UI flow |
| 3.1 | 案件の突合状況返却 | repository | case status contract | API flow |
| 3.2 | 案件名+状況表示 | CaseListPanel | case list view model | UI flow |
