from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from app.domain.models.document_result import DocumentType


@dataclass(frozen=True)
class DocumentTypeInference:
    doc_type: DocumentType
    confidence: float
    reasons: list[str]
    rule_set_version: str


@dataclass(frozen=True)
class DocumentTypeRule:
    rule_id: str
    doc_type: DocumentType
    condition_type: Literal["FIELD_EXISTS", "KEYWORD_CONTAINS"]
    condition_key: str
    condition_value: str | None
    score: float
    priority: int


@dataclass(frozen=True)
class DocumentTypeRuleSet:
    version: str
    rules: list[DocumentTypeRule]


class DocumentTypeInferenceService:
    def __init__(self, active_rule_set_provider: Callable[[], DocumentTypeRuleSet | None]) -> None:
        self._active_rule_set_provider = active_rule_set_provider

    def infer(self, normalized_payload: dict, supplemental_text: str, filename: str) -> DocumentTypeInference:
        active_rule_set = self._active_rule_set_provider()
        if active_rule_set is None:
            return DocumentTypeInference(
                doc_type=DocumentType.UNKNOWN,
                confidence=0.0,
                reasons=["activeルールセットが未設定"],
                rule_set_version="none",
            )
        text = f"{supplemental_text} {filename}".lower()
        scores: dict[DocumentType, float] = {}
        reasons_by_type: dict[DocumentType, list[str]] = {}

        for rule in sorted(active_rule_set.rules, key=lambda r: r.priority, reverse=True):
            matched = self._is_match(rule=rule, normalized_payload=normalized_payload, text=text)
            if not matched:
                continue
            scores[rule.doc_type] = scores.get(rule.doc_type, 0.0) + rule.score
            reasons = reasons_by_type.setdefault(rule.doc_type, [])
            reasons.append(f"{rule.condition_type}:{rule.condition_key}:{rule.condition_value or ''} ({rule.rule_id})")

        if not scores:
            return DocumentTypeInference(
                doc_type=DocumentType.UNKNOWN,
                confidence=0.0,
                reasons=["判定根拠が不足"],
                rule_set_version=active_rule_set.version,
            )

        best_doc_type = max(scores.items(), key=lambda item: item[1])[0]
        best_score = min(scores[best_doc_type], 1.0)
        return DocumentTypeInference(
            doc_type=best_doc_type,
            confidence=best_score,
            reasons=reasons_by_type.get(best_doc_type, []),
            rule_set_version=active_rule_set.version,
        )

    @staticmethod
    def _is_match(*, rule: DocumentTypeRule, normalized_payload: dict, text: str) -> bool:
        if rule.condition_type == "FIELD_EXISTS":
            value = normalized_payload.get(rule.condition_key)
            return value is not None and value != ""
        if rule.condition_type == "KEYWORD_CONTAINS" and rule.condition_value:
            return rule.condition_value.lower() in text
        return False
