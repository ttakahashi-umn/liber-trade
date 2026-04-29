from __future__ import annotations


class JsonNormalizationService:
    FIELD_ALIASES = {
        "invoice_no": "invoice_number",
        "invoiceNumber": "invoice_number",
        "請求番号": "invoice_number",
        "qty": "quantity",
        "数量": "quantity",
        "unitPrice": "unit_price",
        "単価": "unit_price",
        "小計": "subtotal",
        "税額": "tax",
        "合計": "total",
    }

    def normalize(self, extracted_payload: dict) -> tuple[dict, list[str]]:
        normalized: dict = {"line_items": []}
        unmapped_fields: list[str] = []

        for key, value in extracted_payload.items():
            canonical = self.FIELD_ALIASES.get(key, key)
            if canonical not in {
                "invoice_number",
                "tax",
                "total",
                "line_items",
                "quantity",
                "unit_price",
                "subtotal",
            }:
                unmapped_fields.append(key)
                continue

            if canonical == "line_items" and isinstance(value, list):
                normalized["line_items"] = [self._normalize_line_item(item) for item in value]
            else:
                normalized[canonical] = value

        return normalized, unmapped_fields

    def _normalize_line_item(self, item: dict) -> dict:
        mapped: dict = {}
        for key, value in item.items():
            canonical = self.FIELD_ALIASES.get(key, key)
            if canonical in {"quantity", "unit_price", "subtotal", "description"}:
                mapped[canonical] = value
        return mapped
