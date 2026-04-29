from __future__ import annotations

import re


class TextCorrectionService:
    INVOICE_PATTERNS = [
        re.compile(r"(?:invoice[_\s-]*no|請求番号)\s*[:：]?\s*([A-Za-z0-9\-_]+)", re.IGNORECASE),
    ]
    DATE_PATTERNS = [
        re.compile(r"(?:invoice[_\s-]*date|請求日)\s*[:：]?\s*([0-9]{4}[/-][0-9]{1,2}[/-][0-9]{1,2})", re.IGNORECASE),
    ]
    CURRENCY_PATTERNS = [
        re.compile(r"(?:currency|通貨)\s*[:：]?\s*([A-Za-z]{3}|JPY|USD|EUR)", re.IGNORECASE),
    ]
    VENDOR_PATTERNS = [
        re.compile(r"(?:vendor[_\s-]*code|取引先コード)\s*[:：]?\s*([A-Za-z0-9\-_]+)", re.IGNORECASE),
    ]
    TOTAL_PATTERNS = [
        ("total", re.compile(r"(?:total|合計)\s*[:：]?\s*([0-9][0-9,\.]*)", re.IGNORECASE)),
        ("tax", re.compile(r"(?:tax|税額)\s*[:：]?\s*([0-9][0-9,\.]*)", re.IGNORECASE)),
    ]

    def apply(self, normalized_payload: dict, supplemental_text: str) -> dict:
        if not supplemental_text:
            return normalized_payload

        corrected = dict(normalized_payload)

        if not corrected.get("invoice_number"):
            for pattern in self.INVOICE_PATTERNS:
                match = pattern.search(supplemental_text)
                if match:
                    corrected["invoice_number"] = match.group(1)
                    break
        if not corrected.get("invoice_date"):
            for pattern in self.DATE_PATTERNS:
                match = pattern.search(supplemental_text)
                if match:
                    corrected["invoice_date"] = match.group(1).replace("/", "-")
                    break
        if not corrected.get("currency"):
            for pattern in self.CURRENCY_PATTERNS:
                match = pattern.search(supplemental_text)
                if match:
                    corrected["currency"] = match.group(1).upper()
                    break
        if not corrected.get("vendor_code"):
            for pattern in self.VENDOR_PATTERNS:
                match = pattern.search(supplemental_text)
                if match:
                    corrected["vendor_code"] = match.group(1)
                    break

        for key, pattern in self.TOTAL_PATTERNS:
            if corrected.get(key) is not None:
                continue
            match = pattern.search(supplemental_text)
            if match:
                raw = match.group(1).replace(",", "")
                try:
                    corrected[key] = float(raw)
                except ValueError:
                    pass

        return corrected
