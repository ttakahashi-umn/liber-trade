from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


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
    status: ProcessStatus
    normalized_payload: dict[str, Any]
    consistency_result: ConsistencyResult
    unmapped_fields: list[str] = Field(default_factory=list)
