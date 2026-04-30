from __future__ import annotations

from dataclasses import dataclass

from app.domain.models.document_result import DocumentType


@dataclass(frozen=True)
class QuantityToleranceRule:
    rule_set_version: str
    base_doc_type: DocumentType
    target_doc_type: DocumentType
    tolerance_ratio: float
    rule_id: str


class ComparisonRuleResolver:
    """
    将来は comparison_rule_sets / comparison_rules テーブルから解決する。
    いまはインメモリの既定ルールで API 挙動を固定する。
    """

    def __init__(self) -> None:
        self._quantity_rules: list[QuantityToleranceRule] = [
            QuantityToleranceRule("v1", DocumentType.QUT, DocumentType.PO, 0.0, "rule-qut-po-qty-v1"),
            QuantityToleranceRule("v1", DocumentType.EST, DocumentType.PO, 0.0, "rule-est-po-qty-v1"),
            QuantityToleranceRule("v1", DocumentType.PO, DocumentType.PPL, 0.05, "rule-po-ppl-qty-v1"),
            QuantityToleranceRule("v1", DocumentType.PPL, DocumentType.INV, 0.05, "rule-ppl-inv-qty-v1"),
            QuantityToleranceRule("v1", DocumentType.PO, DocumentType.INV, 0.1, "rule-po-inv-qty-v1"),
        ]

    def resolve_quantity_tolerance(
        self,
        *,
        base_doc_type: DocumentType,
        target_doc_type: DocumentType,
        rule_set_version: str | None,
        override_tolerance_ratio: float | None,
    ) -> tuple[float, str | None]:
        if override_tolerance_ratio is not None:
            return override_tolerance_ratio, None

        if rule_set_version:
            for rule in self._quantity_rules:
                if (
                    rule.rule_set_version == rule_set_version
                    and rule.base_doc_type == base_doc_type
                    and rule.target_doc_type == target_doc_type
                ):
                    return rule.tolerance_ratio, rule.rule_id
            return 0.0, None

        for rule in self._quantity_rules:
            if rule.base_doc_type == base_doc_type and rule.target_doc_type == target_doc_type:
                return rule.tolerance_ratio, rule.rule_id
        return 0.0, None
