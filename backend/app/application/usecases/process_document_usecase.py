from __future__ import annotations

import uuid

from app.application.services.document_input_preprocessor import DocumentInputPreprocessor
from app.application.services.json_normalization_service import JsonNormalizationService
from app.application.services.text_correction_service import TextCorrectionService
from app.domain.models.document_result import DocumentResult, DocumentType, ProcessStatus
from app.domain.services.consistency_checker import ConsistencyChecker
from app.domain.services.document_type_inference_service import DocumentTypeInferenceService
from app.infrastructure.minio.minio_storage_gateway import MinioStorageGateway
from app.infrastructure.ollama.ollama_ocr_gateway import OllamaOcrGateway
from app.infrastructure.persistence.repository import DocumentResultRepository, DocumentTypeInferenceLog


class ProcessDocumentUseCase:
    def __init__(
        self,
        ocr_gateway: OllamaOcrGateway,
        preprocessor: DocumentInputPreprocessor,
        normalizer: JsonNormalizationService,
        corrector: TextCorrectionService,
        checker: ConsistencyChecker,
        doc_type_inference_service: DocumentTypeInferenceService,
        storage_gateway: MinioStorageGateway,
        repository: DocumentResultRepository,
    ) -> None:
        self.ocr_gateway = ocr_gateway
        self.preprocessor = preprocessor
        self.normalizer = normalizer
        self.corrector = corrector
        self.checker = checker
        self.doc_type_inference_service = doc_type_inference_service
        self.storage_gateway = storage_gateway
        self.repository = repository

    async def execute(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str | None = None,
        *,
        case_no: str | None = None,
        doc_type: DocumentType | None = None,
    ) -> DocumentResult:
        process_id = str(uuid.uuid4())
        effective_case_no = case_no.strip() if case_no else f"CASE-{process_id[:8]}"
        existing_chain_id = self.repository.get_chain_id_by_case_no(effective_case_no)
        chain_id = existing_chain_id or str(uuid.uuid4())
        document_id = str(uuid.uuid4())
        image_bytes, supplemental_text = self.preprocessor.preprocess(file_bytes, filename, content_type)
        raw_object_key = f"{chain_id}/{document_id}/raw/{filename}"
        rendered_object_key = f"{chain_id}/{document_id}/rendered/{document_id}.png"
        raw_file_object_key = self.storage_gateway.upload_raw(
            object_key=raw_object_key,
            content=file_bytes,
            content_type=content_type or "application/octet-stream",
        )
        rendered_image_object_key = self.storage_gateway.upload_rendered(
            object_key=rendered_object_key,
            content=image_bytes,
        )
        extracted = await self.ocr_gateway.extract_text_and_tables(
            image_bytes=image_bytes,
            filename=filename,
            supplemental_text=supplemental_text,
        )
        normalized, unmapped_fields = self.normalizer.normalize(extracted)
        normalized = self.corrector.apply(normalized, supplemental_text)
        consistency_result = self.checker.evaluate(normalized)
        inference = self.doc_type_inference_service.infer(normalized, supplemental_text, filename)
        effective_doc_type = doc_type if doc_type is not None else inference.doc_type

        status = ProcessStatus.SUCCESS
        if unmapped_fields or not consistency_result.is_consistent or effective_doc_type == DocumentType.UNKNOWN:
            status = ProcessStatus.NEEDS_REVIEW
        if effective_doc_type == DocumentType.UNKNOWN:
            unmapped_fields = [*unmapped_fields, "doc_type:UNKNOWN"]

        result = DocumentResult(
            process_id=process_id,
            chain_id=chain_id,
            case_no=effective_case_no,
            document_id=document_id,
            doc_type=effective_doc_type,
            doc_type_confidence=None if doc_type is not None else inference.confidence,
            doc_type_reasons=[] if doc_type is not None else inference.reasons,
            doc_type_rule_set_version=None if doc_type is not None else inference.rule_set_version,
            raw_file_object_key=raw_file_object_key,
            rendered_image_object_key=rendered_image_object_key,
            status=status,
            normalized_payload=normalized,
            consistency_result=consistency_result,
            unmapped_fields=unmapped_fields,
        )
        self.repository.save(result)
        self.repository.save_doc_type_inference_log(
            DocumentTypeInferenceLog(
                evaluation_id=str(uuid.uuid4()),
                process_id=process_id,
                document_id=document_id,
                rule_set_version=inference.rule_set_version,
                predicted_doc_type=inference.doc_type,
                confidence=inference.confidence,
                reasons=inference.reasons,
                final_doc_type=effective_doc_type,
                is_overridden=doc_type is not None and doc_type != inference.doc_type,
            )
        )
        return result
