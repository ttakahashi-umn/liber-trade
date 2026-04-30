from app.application.services.json_normalization_service import JsonNormalizationService
from app.domain.services.consistency_checker import ConsistencyChecker


def test_normalization_maps_synonyms() -> None:
    service = JsonNormalizationService()
    normalized, unmapped = service.normalize(
        {
            "invoice_no": "INV-1",
            "line_items": [{"qty": 2, "unitPrice": 100, "小計": 200}],
            "unknown_field": "x",
        }
    )
    assert normalized["invoice_number"] == "INV-1"
    assert normalized["line_items"][0]["quantity"] == 2
    assert normalized["line_items"][0]["unit_price"] == 100
    assert "unknown_field" in unmapped


def test_consistency_checker_detects_mismatch() -> None:
    checker = ConsistencyChecker()
    result = checker.evaluate(
        {
            "line_items": [{"unit_price": 100, "quantity": 2, "subtotal": 250}],
            "tax": 10,
            "total": 260,
        }
    )
    assert result.is_consistent is False
    assert len(result.inconsistencies) >= 1


def test_compare_documents_respects_tolerance() -> None:
    checker = ConsistencyChecker()
    result = checker.compare_documents(
        chain_id="chain-1",
        base_document_id="doc-po",
        target_document_id="doc-inv",
        base_payload={"line_items": [{"description": "Item A", "quantity": 100}]},
        target_payload={"line_items": [{"description": "Item A", "quantity": 105}]},
        quantity_tolerance_ratio=0.1,
    )
    assert result.result_status == "WARN"
    assert len(result.items) == 1
    assert result.items[0].is_acceptable is True


def test_compare_documents_fails_without_tolerance() -> None:
    checker = ConsistencyChecker()
    result = checker.compare_documents(
        chain_id="chain-1",
        base_document_id="doc-po",
        target_document_id="doc-inv",
        base_payload={"line_items": [{"description": "Item A", "quantity": 100}]},
        target_payload={"line_items": [{"description": "Item A", "quantity": 105}]},
        quantity_tolerance_ratio=0.0,
        quantity_rule_id="rule-po-inv-qty-v1",
    )
    assert result.result_status == "FAIL"
    assert len(result.items) == 1
    assert result.items[0].is_acceptable is False
