from __future__ import annotations

import logging
import json

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.application.services.document_input_preprocessor import DocumentInputPreprocessor
from app.application.services.json_normalization_service import JsonNormalizationService
from app.application.services.text_correction_service import TextCorrectionService
from app.application.usecases.process_document_usecase import ProcessDocumentUseCase
from app.domain.models.document_result import DocumentResult
from app.domain.services.consistency_checker import ConsistencyChecker
from app.infrastructure.ollama.ollama_ocr_gateway import OllamaOcrGateway
from app.infrastructure.persistence.repository import DocumentResultRepository

router = APIRouter(prefix="/api/documents", tags=["documents"])
cases_router = APIRouter(prefix="/api/cases", tags=["cases"])
logger = logging.getLogger(__name__)

_repository = DocumentResultRepository()
_usecase = ProcessDocumentUseCase(
    ocr_gateway=OllamaOcrGateway(),
    preprocessor=DocumentInputPreprocessor(),
    normalizer=JsonNormalizationService(),
    corrector=TextCorrectionService(),
    checker=ConsistencyChecker(),
    repository=_repository,
)


class IngestResponse(BaseModel):
    process_id: str
    status: str
    normalized_payload: dict
    consistency_result: dict
    warnings: list[str]


class CaseSummaryResponse(BaseModel):
    case_id: str
    case_name: str
    match_status: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)) -> IngestResponse:
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
        result = await _usecase.execute(content, file.filename, file.content_type)
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


def _to_response(result: DocumentResult) -> IngestResponse:
    return IngestResponse(
        process_id=result.process_id,
        status=result.status.value,
        normalized_payload=result.normalized_payload,
        consistency_result=result.consistency_result.model_dump(),
        warnings=result.unmapped_fields,
    )
