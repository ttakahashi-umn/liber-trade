from __future__ import annotations

from app.domain.models.document_result import ConsistencyResult, Inconsistency


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

    @staticmethod
    def _to_float(value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(str(value).replace(",", ""))
        except ValueError:
            return None
