from __future__ import annotations

import uuid

from app.domain.models.document_result import (
    ComparisonItem,
    ConsistencyResult,
    DocumentComparisonResult,
    Inconsistency,
)


class ConsistencyChecker:
    def evaluate(self, normalized_json: dict) -> ConsistencyResult:
        inconsistencies: list[Inconsistency] = []

        line_items = normalized_json.get("line_items", [])
        for idx, item in enumerate(line_items):
            unit_price = self._to_float(item.get("unit_price"))
            quantity = self._to_float(item.get("quantity"))
            subtotal = self._to_float(item.get("subtotal"))
            if unit_price is None or quantity is None or subtotal is None:
                continue
            expected = round(unit_price * quantity, 2)
            if round(subtotal, 2) != expected:
                inconsistencies.append(
                    Inconsistency(
                        field=f"line_items[{idx}].subtotal",
                        expected=expected,
                        actual=round(subtotal, 2),
                        message="単価×数量と小計が不一致です",
                    )
                )

        calc_subtotal = sum(self._to_float(item.get("subtotal")) or 0 for item in line_items)
        tax = self._to_float(normalized_json.get("tax"))
        total = self._to_float(normalized_json.get("total"))
        if tax is not None and total is not None:
            expected_total = round(calc_subtotal + tax, 2)
            if round(total, 2) != expected_total:
                inconsistencies.append(
                    Inconsistency(
                        field="total",
                        expected=expected_total,
                        actual=round(total, 2),
                        message="小計+税額と合計が不一致です",
                    )
                )

        return ConsistencyResult(is_consistent=not inconsistencies, inconsistencies=inconsistencies)

    def compare_documents(
        self,
        *,
        chain_id: str,
        base_document_id: str,
        target_document_id: str,
        base_payload: dict,
        target_payload: dict,
        quantity_tolerance_ratio: float = 0.0,
        quantity_rule_id: str | None = None,
    ) -> DocumentComparisonResult:
        items: list[ComparisonItem] = []

        base_items = base_payload.get("line_items", [])
        target_items = target_payload.get("line_items", [])
        max_len = max(len(base_items), len(target_items))
        for idx in range(max_len):
            base_row = base_items[idx] if idx < len(base_items) else None
            target_row = target_items[idx] if idx < len(target_items) else None
            if base_row is None or target_row is None:
                items.append(
                    ComparisonItem(
                        field_path=f"line_items[{idx}]",
                        base_value=str(base_row) if base_row is not None else None,
                        target_value=str(target_row) if target_row is not None else None,
                        diff_type="MISSING",
                        is_acceptable=False,
                        message="行明細の片側が欠落しています",
                    )
                )
                continue

            items.extend(
                self._compare_line_item(
                    idx=idx,
                    base_row=base_row,
                    target_row=target_row,
                    quantity_tolerance_ratio=quantity_tolerance_ratio,
                    quantity_rule_id=quantity_rule_id,
                )
            )

        result_status = "PASS"
        if any(not item.is_acceptable for item in items):
            result_status = "FAIL"
        elif items:
            result_status = "WARN"

        return DocumentComparisonResult(
            comparison_id=str(uuid.uuid4()),
            chain_id=chain_id,
            base_document_id=base_document_id,
            target_document_id=target_document_id,
            result_status=result_status,
            items=items,
        )

    @staticmethod
    def _to_float(value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(str(value).replace(",", ""))
        except ValueError:
            return None

    def _compare_line_item(
        self,
        *,
        idx: int,
        base_row: dict,
        target_row: dict,
        quantity_tolerance_ratio: float,
        quantity_rule_id: str | None,
    ) -> list[ComparisonItem]:
        items: list[ComparisonItem] = []
        base_qty = self._to_float(base_row.get("quantity"))
        target_qty = self._to_float(target_row.get("quantity"))
        if base_qty is not None or target_qty is not None:
            is_ok = self._within_tolerance(base_qty, target_qty, quantity_tolerance_ratio)
            if not is_ok:
                items.append(
                    ComparisonItem(
                        field_path=f"line_items[{idx}].quantity",
                        base_value=str(base_qty) if base_qty is not None else None,
                        target_value=str(target_qty) if target_qty is not None else None,
                        diff_type="OUT_OF_TOLERANCE",
                        is_acceptable=False,
                        message=(
                            "数量差分が許容範囲を超えています"
                            if quantity_rule_id is None
                            else f"数量差分が許容範囲を超えています (rule={quantity_rule_id})"
                        ),
                    )
                )
            elif base_qty != target_qty:
                items.append(
                    ComparisonItem(
                        field_path=f"line_items[{idx}].quantity",
                        base_value=str(base_qty),
                        target_value=str(target_qty),
                        diff_type="OUT_OF_TOLERANCE",
                        is_acceptable=True,
                        message=(
                            "数量差分は許容範囲内です"
                            if quantity_rule_id is None
                            else f"数量差分は許容範囲内です (rule={quantity_rule_id})"
                        ),
                    )
                )

        base_desc = str(base_row.get("description", "")).strip()
        target_desc = str(target_row.get("description", "")).strip()
        if base_desc != target_desc:
            items.append(
                ComparisonItem(
                    field_path=f"line_items[{idx}].description",
                    base_value=base_desc or None,
                    target_value=target_desc or None,
                    diff_type="MISMATCH",
                    is_acceptable=False,
                    message="品目説明が一致しません",
                )
            )
        return items

    @staticmethod
    def _within_tolerance(base_value: float | None, target_value: float | None, tolerance_ratio: float) -> bool:
        if base_value is None or target_value is None:
            return base_value == target_value
        if base_value == 0:
            return target_value == 0
        diff = abs(target_value - base_value) / abs(base_value)
        return diff <= tolerance_ratio
