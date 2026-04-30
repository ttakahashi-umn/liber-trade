from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    UNKNOWN = "UNKNOWN"
    QUT = "QUT"
    EST = "EST"
    PO = "PO"
    PPL = "PPL"
    INV = "INV"


class ProcessStatus(StrEnum):
    SUCCESS = "SUCCESS"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FAILED = "FAILED"


class Inconsistency(BaseModel):
    field: str
    expected: float | None = None
    actual: float | None = None
    message: str


class ConsistencyResult(BaseModel):
    is_consistent: bool
    inconsistencies: list[Inconsistency] = Field(default_factory=list)


class DocumentResult(BaseModel):
    process_id: str
    chain_id: str
    case_no: str
    document_id: str
    doc_type: DocumentType
    doc_type_confidence: float | None = None
    doc_type_reasons: list[str] = Field(default_factory=list)
    doc_type_rule_set_version: str | None = None
    raw_file_object_key: str | None = None
    rendered_image_object_key: str | None = None
    status: ProcessStatus
    normalized_payload: dict[str, Any]
    consistency_result: ConsistencyResult
    unmapped_fields: list[str] = Field(default_factory=list)


class DocumentSummary(BaseModel):
    document_id: str
    doc_type: DocumentType
    process_id: str
    status: ProcessStatus


class ComparisonItem(BaseModel):
    field_path: str
    base_value: str | None = None
    target_value: str | None = None
    diff_type: str
    is_acceptable: bool
    message: str


class DocumentComparisonResult(BaseModel):
    comparison_id: str
    chain_id: str
    base_document_id: str
    target_document_id: str
    result_status: str
    items: list[ComparisonItem] = Field(default_factory=list)
