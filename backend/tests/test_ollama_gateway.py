from app.infrastructure.ollama.ollama_ocr_gateway import OllamaOcrGateway


def test_parse_json_from_raw_plain_json() -> None:
    gateway = OllamaOcrGateway()
    parsed = gateway._parse_json_from_response('{"invoice_no":"INV-1","合計":100}', "a.pdf")
    assert parsed["invoice_no"] == "INV-1"


def test_parse_json_from_raw_fenced_json() -> None:
    gateway = OllamaOcrGateway()
    raw = '出力:\n```json\n{"invoice_no":"INV-2","合計":200}\n```'
    parsed = gateway._parse_json_from_response(raw, "b.pdf")
    assert parsed["invoice_no"] == "INV-2"


def test_extract_json_candidate_from_mixed_text() -> None:
    raw = 'text before {"invoice_no":"INV-3","合計":300} text after'
    candidate = OllamaOcrGateway._extract_json_candidate(raw)
    assert candidate == '{"invoice_no":"INV-3","合計":300}'
