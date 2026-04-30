from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import json
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.models.document_result import ConsistencyResult, DocumentComparisonResult, DocumentResult, DocumentType, DocumentSummary, ProcessStatus
from app.domain.services.document_type_inference_service import DocumentTypeRule, DocumentTypeRuleSet
from app.infrastructure.persistence.db_settings import get_database_url, get_sqlite_db_path_from_url
from app.infrastructure.persistence.orm_models import (
    DocumentComparisonItemORM,
    DocumentComparisonORM,
    DocumentProcessORM,
    DocumentTypeInferenceLogORM,
    DocumentTypeRuleORM,
    DocumentTypeRuleSetORM,
    TradeChainORM,
    TradeDocumentORM,
)
from app.infrastructure.persistence.sqlalchemy_session import create_engine_and_sessionmaker


@dataclass
class CaseSummary:
    case_id: str
    case_name: str
    match_status: str


@dataclass
class DocumentTypeInferenceLog:
    evaluation_id: str
    process_id: str
    document_id: str
    rule_set_version: str
    predicted_doc_type: DocumentType
    confidence: float
    reasons: list[str]
    final_doc_type: DocumentType
    is_overridden: bool


class DocumentResultRepository:
    def __init__(self) -> None:
        self._db_path = self._resolve_db_path()
        self._engine, self._session_factory = create_engine_and_sessionmaker()
        self._initialize_db()
        self._seed_default_doc_type_rules()

    def save(self, result: DocumentResult) -> None:
        with self._session_scope() as session:
            process = session.get(DocumentProcessORM, result.process_id)
            if process is None:
                process = DocumentProcessORM(
                    process_id=result.process_id,
                    status=result.status.value,
                    normalized_payload_json=json.dumps(result.normalized_payload, ensure_ascii=False),
                    consistency_result_json=json.dumps(result.consistency_result.model_dump(), ensure_ascii=False),
                )
                session.add(process)
            else:
                process.status = result.status.value
                process.normalized_payload_json = json.dumps(result.normalized_payload, ensure_ascii=False)
                process.consistency_result_json = json.dumps(result.consistency_result.model_dump(), ensure_ascii=False)

            if session.get(TradeChainORM, result.chain_id) is None:
                session.add(TradeChainORM(chain_id=result.chain_id, case_no=result.case_no))

            payload_json = json.dumps(self._load_doc_payload(result), ensure_ascii=False)
            document = session.get(TradeDocumentORM, result.document_id)
            if document is None:
                session.add(
                    TradeDocumentORM(
                        document_id=result.document_id,
                        chain_id=result.chain_id,
                        doc_type=result.doc_type.value,
                        doc_no=result.case_no,
                        source_process_id=result.process_id,
                        normalized_payload_json=payload_json,
                    )
                )
            else:
                document.doc_type = result.doc_type.value
                document.doc_no = result.case_no
                document.source_process_id = result.process_id
                document.normalized_payload_json = payload_json

    def get(self, process_id: str) -> DocumentResult | None:
        with self._session_scope() as session:
            row = (
                session.query(TradeDocumentORM, TradeChainORM, DocumentProcessORM)
                .join(TradeChainORM, TradeChainORM.chain_id == TradeDocumentORM.chain_id)
                .join(DocumentProcessORM, DocumentProcessORM.process_id == TradeDocumentORM.source_process_id)
                .filter(DocumentProcessORM.process_id == process_id)
                .first()
            )
            if row is None:
                return None
            return self._to_result(row[0], row[1], row[2])

    def list_cases(self, process_id: str) -> list[CaseSummary]:
        result = self.get(process_id)
        if result is None:
            return []
        return self._build_case_summaries(result)

    def list_documents(self, chain_id: str) -> list[DocumentSummary]:
        with self._session_scope() as session:
            rows = (
                session.query(TradeDocumentORM, DocumentProcessORM)
                .outerjoin(DocumentProcessORM, DocumentProcessORM.process_id == TradeDocumentORM.source_process_id)
                .filter(TradeDocumentORM.chain_id == chain_id)
                .order_by(TradeDocumentORM.created_at.asc())
                .all()
            )
            return [
                DocumentSummary(
                    document_id=doc.document_id,
                    doc_type=DocumentType(doc.doc_type),
                    process_id=doc.source_process_id or "",
                    status=ProcessStatus(proc.status if proc else ProcessStatus.NEEDS_REVIEW.value),
                )
                for doc, proc in rows
            ]

    def get_by_document_id(self, document_id: str) -> DocumentResult | None:
        with self._session_scope() as session:
            row = (
                session.query(TradeDocumentORM, TradeChainORM, DocumentProcessORM)
                .join(TradeChainORM, TradeChainORM.chain_id == TradeDocumentORM.chain_id)
                .outerjoin(DocumentProcessORM, DocumentProcessORM.process_id == TradeDocumentORM.source_process_id)
                .filter(TradeDocumentORM.document_id == document_id)
                .first()
            )
            if row is None:
                return None
            return self._to_result(row[0], row[1], row[2])

    def save_comparison(self, comparison: DocumentComparisonResult) -> None:
        with self._session_scope() as session:
            comparison_row = session.get(DocumentComparisonORM, comparison.comparison_id)
            if comparison_row is None:
                session.add(
                    DocumentComparisonORM(
                        comparison_id=comparison.comparison_id,
                        chain_id=comparison.chain_id,
                        base_document_id=comparison.base_document_id,
                        target_document_id=comparison.target_document_id,
                        result_status=comparison.result_status,
                        summary_json=json.dumps({"count": len(comparison.items)}, ensure_ascii=False),
                    )
                )
                session.flush()
            else:
                comparison_row.result_status = comparison.result_status
                comparison_row.summary_json = json.dumps({"count": len(comparison.items)}, ensure_ascii=False)

            session.execute(
                delete(DocumentComparisonItemORM).where(DocumentComparisonItemORM.comparison_id == comparison.comparison_id)
            )
            for item in comparison.items:
                session.add(
                    DocumentComparisonItemORM(
                        item_id=f"{comparison.comparison_id}:{item.field_path}",
                        comparison_id=comparison.comparison_id,
                        field_path=item.field_path,
                        base_value=item.base_value,
                        target_value=item.target_value,
                        diff_type=item.diff_type,
                        is_acceptable=1 if item.is_acceptable else 0,
                        message=item.message,
                    )
                )

    def get_chain_id_by_case_no(self, case_no: str) -> str | None:
        with self._session_scope() as session:
            chain = session.execute(select(TradeChainORM).where(TradeChainORM.case_no == case_no)).scalar_one_or_none()
            return chain.chain_id if chain else None

    def list_doc_type_rule_sets(self) -> list[DocumentTypeRuleSet]:
        with self._session_scope() as session:
            sets = session.execute(select(DocumentTypeRuleSetORM).order_by(DocumentTypeRuleSetORM.created_at.asc())).scalars().all()
            result: list[DocumentTypeRuleSet] = []
            for rule_set in sets:
                rules = (
                    session.execute(
                        select(DocumentTypeRuleORM)
                        .where(DocumentTypeRuleORM.rule_set_id == rule_set.rule_set_id)
                        .order_by(DocumentTypeRuleORM.priority.desc())
                    )
                    .scalars()
                    .all()
                )
                result.append(DocumentTypeRuleSet(version=rule_set.version, rules=[self._to_rule(rule) for rule in rules]))
            return result

    def get_active_doc_type_rule_set(self) -> DocumentTypeRuleSet | None:
        with self._session_scope() as session:
            active = session.execute(
                select(DocumentTypeRuleSetORM).where(DocumentTypeRuleSetORM.is_active == 1).limit(1)
            ).scalar_one_or_none()
            if active is None:
                return None
            rules = (
                session.execute(
                    select(DocumentTypeRuleORM)
                    .where(DocumentTypeRuleORM.rule_set_id == active.rule_set_id)
                    .order_by(DocumentTypeRuleORM.priority.desc())
                )
                .scalars()
                .all()
            )
            if not rules:
                return None
            return DocumentTypeRuleSet(version=active.version, rules=[self._to_rule(rule) for rule in rules])

    def create_doc_type_rule_set(self, version: str, rules: list[DocumentTypeRule]) -> DocumentTypeRuleSet:
        with self._session_scope() as session:
            exists = session.execute(select(DocumentTypeRuleSetORM).where(DocumentTypeRuleSetORM.version == version)).scalar_one_or_none()
            if exists:
                raise ValueError("同じversionのルールセットが既に存在します")
            rule_set_id = f"dtrs-{version}"
            session.add(DocumentTypeRuleSetORM(rule_set_id=rule_set_id, version=version, description=f"doc type rules {version}", is_active=0))
            session.flush()
            for rule in rules:
                session.add(
                    DocumentTypeRuleORM(
                        rule_id=rule.rule_id,
                        rule_set_id=rule_set_id,
                        doc_type=rule.doc_type.value,
                        condition_type=rule.condition_type,
                        condition_key=rule.condition_key,
                        condition_value=rule.condition_value,
                        score=rule.score,
                        priority=rule.priority,
                    )
                )
        return DocumentTypeRuleSet(version=version, rules=rules)

    def activate_doc_type_rule_set(self, version: str) -> DocumentTypeRuleSet:
        with self._session_scope() as session:
            target = session.execute(select(DocumentTypeRuleSetORM).where(DocumentTypeRuleSetORM.version == version)).scalar_one_or_none()
            if target is None:
                raise ValueError("指定されたルールセットが存在しません")
            for rule_set in session.execute(select(DocumentTypeRuleSetORM)).scalars().all():
                rule_set.is_active = 1 if rule_set.version == version else 0
        active = self.get_active_doc_type_rule_set()
        if active is None:
            raise ValueError("指定されたルールセットが存在しません")
        return active

    def save_doc_type_inference_log(self, log: DocumentTypeInferenceLog) -> None:
        with self._session_scope() as session:
            if session.get(DocumentTypeInferenceLogORM, log.evaluation_id) is None:
                session.add(
                    DocumentTypeInferenceLogORM(
                        evaluation_id=log.evaluation_id,
                        process_id=log.process_id,
                        document_id=log.document_id,
                        rule_set_version=log.rule_set_version,
                        predicted_doc_type=log.predicted_doc_type.value,
                        confidence=log.confidence,
                        reasons_json=json.dumps(log.reasons, ensure_ascii=False),
                        final_doc_type=log.final_doc_type.value,
                        is_overridden=1 if log.is_overridden else 0,
                    )
                )

    def list_doc_type_inference_logs(self, limit: int = 100) -> list[DocumentTypeInferenceLog]:
        with self._session_scope() as session:
            rows = (
                session.execute(
                    select(DocumentTypeInferenceLogORM)
                    .order_by(DocumentTypeInferenceLogORM.created_at.desc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
            return [
                DocumentTypeInferenceLog(
                    evaluation_id=row.evaluation_id,
                    process_id=row.process_id,
                    document_id=row.document_id,
                    rule_set_version=row.rule_set_version,
                    predicted_doc_type=DocumentType(row.predicted_doc_type),
                    confidence=float(row.confidence),
                    reasons=json.loads(row.reasons_json),
                    final_doc_type=DocumentType(row.final_doc_type),
                    is_overridden=bool(row.is_overridden),
                )
                for row in rows
            ]

    def update_document_doc_type(self, document_id: str, doc_type: DocumentType) -> DocumentResult | None:
        current = self.get_by_document_id(document_id)
        if current is None:
            return None
        with self._session_scope() as session:
            document = session.get(TradeDocumentORM, document_id)
            if document is None:
                return None
            document.doc_type = doc_type.value
            payload = self._load_doc_payload(current)
            payload["manual_override"] = True
            document.normalized_payload_json = json.dumps(payload, ensure_ascii=False)
            if current.process_id:
                process = session.get(DocumentProcessORM, current.process_id)
                if process:
                    process.status = ProcessStatus.NEEDS_REVIEW.value
        return self.get_by_document_id(document_id)

    def get_doc_type_metrics(self) -> dict[str, float]:
        logs = self.list_doc_type_inference_logs(limit=100000)
        total = len(logs)
        if total == 0:
            return {"total": 0, "unknown_rate": 0.0, "override_rate": 0.0}
        unknown_count = sum(1 for log in logs if log.predicted_doc_type == DocumentType.UNKNOWN)
        override_count = sum(1 for log in logs if log.is_overridden)
        return {"total": float(total), "unknown_rate": unknown_count / total, "override_rate": override_count / total}

    def reset_all_data(self) -> None:
        with self._session_scope() as session:
            session.execute(delete(DocumentTypeInferenceLogORM))
            session.execute(delete(DocumentComparisonItemORM))
            session.execute(delete(DocumentComparisonORM))
            session.execute(delete(TradeDocumentORM))
            session.execute(delete(TradeChainORM))
            session.execute(delete(DocumentProcessORM))
            session.execute(delete(DocumentTypeRuleORM))
            session.execute(delete(DocumentTypeRuleSetORM))
        self._seed_default_doc_type_rules()

    def _seed_default_doc_type_rules(self) -> None:
        if self.get_active_doc_type_rule_set() is not None:
            return
        rules = [
            DocumentTypeRule("dtr-inv-1", DocumentType.INV, "FIELD_EXISTS", "invoice_number", None, 0.35, 100),
            DocumentTypeRule("dtr-inv-2", DocumentType.INV, "FIELD_EXISTS", "tax", None, 0.30, 100),
            DocumentTypeRule("dtr-inv-3", DocumentType.INV, "FIELD_EXISTS", "total", None, 0.30, 100),
            DocumentTypeRule("dtr-ppl-1", DocumentType.PPL, "KEYWORD_CONTAINS", "text", "packing list", 0.7, 80),
            DocumentTypeRule("dtr-ppl-2", DocumentType.PPL, "KEYWORD_CONTAINS", "text", "shipping marks", 0.6, 80),
            DocumentTypeRule("dtr-qut-1", DocumentType.QUT, "KEYWORD_CONTAINS", "text", "quotation", 0.7, 70),
            DocumentTypeRule("dtr-est-1", DocumentType.EST, "KEYWORD_CONTAINS", "text", "estimate", 0.7, 70),
            DocumentTypeRule("dtr-po-1", DocumentType.PO, "KEYWORD_CONTAINS", "text", "purchase order", 0.7, 70),
        ]
        self.create_doc_type_rule_set(version="v1", rules=rules)
        self.activate_doc_type_rule_set("v1")

    def _initialize_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        migration_path = Path(__file__).with_name("migrations") / "0001_initial.sql"
        schema_sql = migration_path.read_text(encoding="utf-8")
        with self._engine.begin() as conn:
            raw = conn.connection.driver_connection
            raw.executescript(schema_sql)
            DocumentTypeInferenceLogORM.__table__.create(bind=conn, checkfirst=True)

    @staticmethod
    def _resolve_db_path() -> Path:
        return get_sqlite_db_path_from_url(get_database_url())

    def _to_result(
        self,
        document: TradeDocumentORM,
        chain: TradeChainORM,
        process: DocumentProcessORM | None,
    ) -> DocumentResult:
        payload = json.loads(document.normalized_payload_json or "{}")
        wrapped_payload = payload.get("normalized_payload", payload)
        consistency_raw = (
            process.consistency_result_json
            if process and process.consistency_result_json
            else json.dumps({"is_consistent": True, "inconsistencies": []})
        )
        consistency = ConsistencyResult(**json.loads(consistency_raw))
        return DocumentResult(
            process_id=process.process_id if process else "",
            chain_id=chain.chain_id,
            case_no=chain.case_no,
            document_id=document.document_id,
            doc_type=DocumentType(document.doc_type),
            doc_type_confidence=payload.get("doc_type_confidence"),
            doc_type_reasons=payload.get("doc_type_reasons", []),
            doc_type_rule_set_version=payload.get("doc_type_rule_set_version"),
            raw_file_object_key=payload.get("raw_file_object_key"),
            rendered_image_object_key=payload.get("rendered_image_object_key"),
            status=ProcessStatus(process.status if process else ProcessStatus.NEEDS_REVIEW.value),
            normalized_payload=wrapped_payload,
            consistency_result=consistency,
            unmapped_fields=payload.get("warnings", []),
        )

    @staticmethod
    def _to_rule(row: DocumentTypeRuleORM) -> DocumentTypeRule:
        return DocumentTypeRule(
            rule_id=row.rule_id,
            doc_type=DocumentType(row.doc_type),
            condition_type=row.condition_type,
            condition_key=row.condition_key,
            condition_value=row.condition_value,
            score=float(row.score),
            priority=int(row.priority),
        )

    @staticmethod
    def _build_case_summaries(result: DocumentResult) -> list[CaseSummary]:
        if result.status.value == "SUCCESS":
            status = "OK"
        elif result.status.value == "NEEDS_REVIEW":
            status = "要確認"
        else:
            status = "未処理"
        return [CaseSummary(case_id=result.chain_id, case_name=f"案件 {result.case_no}", match_status=status)]

    @staticmethod
    def _load_doc_payload(result: DocumentResult) -> dict:
        return {
            "normalized_payload": result.normalized_payload,
            "doc_type_confidence": result.doc_type_confidence,
            "doc_type_reasons": result.doc_type_reasons,
            "doc_type_rule_set_version": result.doc_type_rule_set_version,
            "raw_file_object_key": result.raw_file_object_key,
            "rendered_image_object_key": result.rendered_image_object_key,
            "warnings": result.unmapped_fields,
            "status": result.status.value,
            "consistency_result": result.consistency_result.model_dump(),
        }

    @contextmanager
    def _session_scope(self):
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
