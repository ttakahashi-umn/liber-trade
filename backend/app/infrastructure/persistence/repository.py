from __future__ import annotations

from dataclasses import dataclass

from app.domain.models.document_result import DocumentResult


@dataclass
class CaseSummary:
    case_id: str
    case_name: str
    match_status: str


class DocumentResultRepository:
    def __init__(self) -> None:
        self._store: dict[str, DocumentResult] = {}
        self._cases_by_process: dict[str, list[CaseSummary]] = {}

    def save(self, result: DocumentResult) -> None:
        self._store[result.process_id] = result
        self._cases_by_process[result.process_id] = self._build_case_summaries(result)

    def get(self, process_id: str) -> DocumentResult | None:
        return self._store.get(process_id)

    def list_cases(self, process_id: str) -> list[CaseSummary]:
        return self._cases_by_process.get(process_id, [])

    @staticmethod
    def _build_case_summaries(result: DocumentResult) -> list[CaseSummary]:
        if result.status.value == "SUCCESS":
            status = "OK"
        elif result.status.value == "NEEDS_REVIEW":
            status = "要確認"
        else:
            status = "未処理"
        return [
            CaseSummary(
                case_id=f"CASE-{result.process_id[:8]}-1",
                case_name=f"取り込み案件 {result.process_id[:8]}",
                match_status=status,
            )
        ]
