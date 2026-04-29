from __future__ import annotations

import uuid

from app.application.services.document_input_preprocessor import DocumentInputPreprocessor
from app.application.services.json_normalization_service import JsonNormalizationService
from app.application.services.text_correction_service import TextCorrectionService
from app.domain.models.document_result import DocumentResult, ProcessStatus
from app.domain.services.consistency_checker import ConsistencyChecker
from app.infrastructure.ollama.ollama_ocr_gateway import OllamaOcrGateway
from app.infrastructure.persistence.repository import DocumentResultRepository


class ProcessDocumentUseCase:
    def __init__(
        self,
        ocr_gateway: OllamaOcrGateway,
        preprocessor: DocumentInputPreprocessor,
        normalizer: JsonNormalizationService,
        corrector: TextCorrectionService,
        checker: ConsistencyChecker,
        repository: DocumentResultRepository,
    ) -> None:
        self.ocr_gateway = ocr_gateway
        self.preprocessor = preprocessor
        self.normalizer = normalizer
        self.corrector = corrector
        self.checker = checker
        self.repository = repository

    async def execute(self, file_bytes: bytes, filename: str, content_type: str | None = None) -> DocumentResult:
        process_id = str(uuid.uuid4())
        image_bytes, supplemental_text = self.preprocessor.preprocess(file_bytes, filename, content_type)
        extracted = await self.ocr_gateway.extract_text_and_tables(
            image_bytes=image_bytes,
            filename=filename,
            supplemental_text=supplemental_text,
        )
        normalized, unmapped_fields = self.normalizer.normalize(extracted)
        normalized = self.corrector.apply(normalized, supplemental_text)
        consistency_result = self.checker.evaluate(normalized)

        status = ProcessStatus.SUCCESS
        if unmapped_fields or not consistency_result.is_consistent:
            status = ProcessStatus.NEEDS_REVIEW

        result = DocumentResult(
            process_id=process_id,
            status=status,
            normalized_payload=normalized,
            consistency_result=consistency_result,
            unmapped_fields=unmapped_fields,
        )
        self.repository.save(result)
        return result
