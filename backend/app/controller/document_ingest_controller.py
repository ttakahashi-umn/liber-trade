from __future__ import annotations

import logging
import json
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.application.services.document_input_preprocessor import DocumentInputPreprocessor
from app.application.services.json_normalization_service import JsonNormalizationService
from app.application.services.text_correction_service import TextCorrectionService
from app.application.usecases.process_document_usecase import ProcessDocumentUseCase
from app.domain.models.document_result import (
    DocumentComparisonResult,
    DocumentResult,
    DocumentType,
)
from app.domain.services.consistency_checker import ConsistencyChecker
from app.domain.services.comparison_rule_resolver import ComparisonRuleResolver
from app.domain.services.document_type_inference_service import DocumentTypeInferenceService
from app.infrastructure.minio.minio_storage_gateway import MinioStorageGateway
from app.infrastructure.ollama.ollama_ocr_gateway import OllamaOcrGateway
from app.infrastructure.persistence.repository import DocumentResultRepository, DocumentTypeInferenceLog

router = APIRouter(prefix="/api/documents", tags=["documents"])
cases_router = APIRouter(prefix="/api/cases", tags=["cases"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)

_repository = DocumentResultRepository()
_rule_resolver = ComparisonRuleResolver()
_usecase = ProcessDocumentUseCase(
    ocr_gateway=OllamaOcrGateway(),
    preprocessor=DocumentInputPreprocessor(),
    normalizer=JsonNormalizationService(),
    corrector=TextCorrectionService(),
    checker=ConsistencyChecker(),
    doc_type_inference_service=DocumentTypeInferenceService(
        active_rule_set_provider=_repository.get_active_doc_type_rule_set
    ),
    storage_gateway=MinioStorageGateway(),
    repository=_repository,
)


class IngestResponse(BaseModel):
    process_id: str
    chain_id: str
    case_no: str
    document_id: str
    doc_type: str
    doc_type_confidence: float | None
    doc_type_reasons: list[str]
    doc_type_rule_set_version: str | None
    raw_file_object_key: str | None
    rendered_image_object_key: str | None
    raw_file_url: str | None
    rendered_image_url: str | None
    status: str
    normalized_payload: dict
    consistency_result: dict
    warnings: list[str]


class CaseSummaryResponse(BaseModel):
    case_id: str
    case_name: str
    match_status: str


class DocumentSummaryResponse(BaseModel):
    document_id: str
    doc_type: str
    process_id: str
    status: str


class CompareDocumentsRequest(BaseModel):
    base_document_id: str
    target_document_id: str
    quantity_tolerance_ratio: float | None = None
    rule_set_version: str | None = None


class CompareDocumentsResponse(BaseModel):
    comparison_id: str
    chain_id: str
    base_document_id: str
    target_document_id: str
    result_status: str
    items: list[dict]


class DocumentTypeRulePayload(BaseModel):
    rule_id: str
    doc_type: DocumentType
    condition_type: Literal["FIELD_EXISTS", "KEYWORD_CONTAINS"]
    condition_key: str
    condition_value: str | None = None
    score: float
    priority: int


class DocumentTypeRuleSetPayload(BaseModel):
    version: str
    rules: list[DocumentTypeRulePayload]


class ManualDocTypeUpdateRequest(BaseModel):
    doc_type: DocumentType


class DocTypeInferenceLogResponse(BaseModel):
    evaluation_id: str
    process_id: str
    document_id: str
    rule_set_version: str
    predicted_doc_type: str
    confidence: float
    reasons: list[str]
    final_doc_type: str
    is_overridden: bool


class DocTypeMetricsResponse(BaseModel):
    total: float
    unknown_rate: float
    override_rate: float


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    case_no: str | None = Form(None),
    doc_type: DocumentType | None = Form(None),
) -> IngestResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイル名がありません")
    allowed_content_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if not file.content_type:
        raise HTTPException(status_code=400, detail="content_type が必要です")
    if not file.content_type.startswith("image/") and file.content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail="画像/PDF/Excel/Word のみ受け付けます")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="空ファイルは処理できません")

    try:
        result = await _usecase.execute(
            content,
            file.filename,
            file.content_type,
            case_no=case_no,
            doc_type=doc_type,
        )
    except ValueError as exc:
        logger.warning("Ingest validation failed: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected ingest failure for filename=%s content_type=%s", file.filename, file.content_type)
        raise HTTPException(status_code=500, detail="処理に失敗しました") from exc
    response = _to_response(result)
    logger.info("Ingest result: %s", json.dumps(response.model_dump(), ensure_ascii=False))
    return response


@router.get("/{process_id}", response_model=IngestResponse)
async def get_document_result(process_id: str) -> IngestResponse:
    result = _repository.get(process_id)
    if result is None:
        raise HTTPException(status_code=404, detail="処理結果が見つかりません")
    return _to_response(result)


@router.patch("/{document_id}/doc-type", response_model=IngestResponse)
async def override_document_type(document_id: str, request: ManualDocTypeUpdateRequest) -> IngestResponse:
    updated = _repository.update_document_doc_type(document_id, request.doc_type)
    if updated is None:
        raise HTTPException(status_code=404, detail="書類が見つかりません")
    return _to_response(updated)


@cases_router.get("", response_model=list[CaseSummaryResponse])
async def list_cases(process_id: str = Query(...)) -> list[CaseSummaryResponse]:
    cases = _repository.list_cases(process_id)
    return [
        CaseSummaryResponse(
            case_id=case.case_id,
            case_name=case.case_name,
            match_status=case.match_status,
        )
        for case in cases
    ]


@cases_router.get("/{chain_id}/documents", response_model=list[DocumentSummaryResponse])
async def list_documents(chain_id: str) -> list[DocumentSummaryResponse]:
    docs = _repository.list_documents(chain_id)
    return [
        DocumentSummaryResponse(
            document_id=doc.document_id,
            doc_type=doc.doc_type.value,
            process_id=doc.process_id,
            status=doc.status.value,
        )
        for doc in docs
    ]


@cases_router.post("/{chain_id}/comparisons", response_model=CompareDocumentsResponse)
async def compare_documents(chain_id: str, request: CompareDocumentsRequest) -> CompareDocumentsResponse:
    base_result = _repository.get_by_document_id(request.base_document_id)
    target_result = _repository.get_by_document_id(request.target_document_id)
    if base_result is None or target_result is None:
        raise HTTPException(status_code=404, detail="比較対象書類が見つかりません")
    if base_result.chain_id != chain_id or target_result.chain_id != chain_id:
        raise HTTPException(status_code=422, detail="同一案件内の書類のみ比較できます")

    tolerance_ratio, quantity_rule_id = _rule_resolver.resolve_quantity_tolerance(
        base_doc_type=base_result.doc_type,
        target_doc_type=target_result.doc_type,
        rule_set_version=request.rule_set_version,
        override_tolerance_ratio=request.quantity_tolerance_ratio,
    )

    comparison = ConsistencyChecker().compare_documents(
        chain_id=chain_id,
        base_document_id=request.base_document_id,
        target_document_id=request.target_document_id,
        base_payload=base_result.normalized_payload,
        target_payload=target_result.normalized_payload,
        quantity_tolerance_ratio=tolerance_ratio,
        quantity_rule_id=quantity_rule_id,
    )
    _repository.save_comparison(comparison)
    return _to_compare_response(comparison)


@admin_router.get("/document-type-rule-sets", response_model=list[DocumentTypeRuleSetPayload])
async def list_doc_type_rule_sets() -> list[DocumentTypeRuleSetPayload]:
    return [_to_rule_set_payload(rs) for rs in _repository.list_doc_type_rule_sets()]


@admin_router.post("/document-type-rule-sets", response_model=DocumentTypeRuleSetPayload)
async def create_doc_type_rule_set(request: DocumentTypeRuleSetPayload) -> DocumentTypeRuleSetPayload:
    from app.domain.services.document_type_inference_service import DocumentTypeRule

    try:
        created = _repository.create_doc_type_rule_set(
            version=request.version,
            rules=[
                DocumentTypeRule(
                    rule_id=rule.rule_id,
                    doc_type=rule.doc_type,
                    condition_type=rule.condition_type,
                    condition_key=rule.condition_key,
                    condition_value=rule.condition_value,
                    score=rule.score,
                    priority=rule.priority,
                )
                for rule in request.rules
            ],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _to_rule_set_payload(created)


@admin_router.post("/document-type-rule-sets/{version}/activate", response_model=DocumentTypeRuleSetPayload)
async def activate_doc_type_rule_set(version: str) -> DocumentTypeRuleSetPayload:
    try:
        active = _repository.activate_doc_type_rule_set(version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_rule_set_payload(active)


@admin_router.get("/document-type-inference-logs", response_model=list[DocTypeInferenceLogResponse])
async def list_doc_type_inference_logs(limit: int = Query(100, ge=1, le=1000)) -> list[DocTypeInferenceLogResponse]:
    return [_to_log_response(log) for log in _repository.list_doc_type_inference_logs(limit)]


@admin_router.get("/document-type-metrics", response_model=DocTypeMetricsResponse)
async def get_doc_type_metrics() -> DocTypeMetricsResponse:
    metrics = _repository.get_doc_type_metrics()
    return DocTypeMetricsResponse(**metrics)


def _to_response(result: DocumentResult) -> IngestResponse:
    raw_file_url = _build_presigned_url(result.raw_file_object_key)
    rendered_image_url = _build_presigned_url(result.rendered_image_object_key)
    return IngestResponse(
        process_id=result.process_id,
        chain_id=result.chain_id,
        case_no=result.case_no,
        document_id=result.document_id,
        doc_type=result.doc_type.value,
        doc_type_confidence=result.doc_type_confidence,
        doc_type_reasons=result.doc_type_reasons,
        doc_type_rule_set_version=result.doc_type_rule_set_version,
        raw_file_object_key=result.raw_file_object_key,
        rendered_image_object_key=result.rendered_image_object_key,
        raw_file_url=raw_file_url,
        rendered_image_url=rendered_image_url,
        status=result.status.value,
        normalized_payload=result.normalized_payload,
        consistency_result=result.consistency_result.model_dump(),
        warnings=result.unmapped_fields,
    )


def _build_presigned_url(object_key: str | None) -> str | None:
    if object_key is None:
        return None
    try:
        return MinioStorageGateway().presigned_get_url(object_key)
    except Exception:
        logger.warning("Failed to build presigned URL for object_key=%s", object_key)
        return None


def _to_compare_response(comparison: DocumentComparisonResult) -> CompareDocumentsResponse:
    return CompareDocumentsResponse(
        comparison_id=comparison.comparison_id,
        chain_id=comparison.chain_id,
        base_document_id=comparison.base_document_id,
        target_document_id=comparison.target_document_id,
        result_status=comparison.result_status,
        items=[item.model_dump() for item in comparison.items],
    )


def _to_rule_set_payload(rule_set) -> DocumentTypeRuleSetPayload:
    return DocumentTypeRuleSetPayload(
        version=rule_set.version,
        rules=[
            DocumentTypeRulePayload(
                rule_id=rule.rule_id,
                doc_type=rule.doc_type,
                condition_type=rule.condition_type,
                condition_key=rule.condition_key,
                condition_value=rule.condition_value,
                score=rule.score,
                priority=rule.priority,
            )
            for rule in rule_set.rules
        ],
    )


def _to_log_response(log: DocumentTypeInferenceLog) -> DocTypeInferenceLogResponse:
    return DocTypeInferenceLogResponse(
        evaluation_id=log.evaluation_id,
        process_id=log.process_id,
        document_id=log.document_id,
        rule_set_version=log.rule_set_version,
        predicted_doc_type=log.predicted_doc_type.value,
        confidence=log.confidence,
        reasons=log.reasons,
        final_doc_type=log.final_doc_type.value,
        is_overridden=log.is_overridden,
    )
