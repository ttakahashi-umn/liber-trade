import pytest
from fastapi.testclient import TestClient

from app.infrastructure.ollama.ollama_ocr_gateway import OllamaOcrGateway
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_ocr_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _mock_extract(_: OllamaOcrGateway, image_bytes: bytes, filename: str, supplemental_text: str = "") -> dict:
        return {
            "invoice_no": f"MOCK-{filename}",
            "line_items": [{"description": "Item A", "unitPrice": 100, "qty": 2, "小計": 200}],
            "税額": 20,
            "合計": 220,
        }

    monkeypatch.setattr(OllamaOcrGateway, "extract_text_and_tables", _mock_extract)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_and_get_result() -> None:
    files = {"file": ("sample.png", b"fake-image-bytes", "image/png")}
    response = client.post("/api/documents/ingest", files=files)
    assert response.status_code == 200
    body = response.json()
    assert "process_id" in body
    assert body["status"] in {"SUCCESS", "NEEDS_REVIEW", "FAILED"}
    process_id = body["process_id"]

    fetched = client.get(f"/api/documents/{process_id}")
    assert fetched.status_code == 200
    fetched_body = fetched.json()
    assert fetched_body["process_id"] == process_id
    assert "consistency_result" in fetched_body

    cases = client.get(f"/api/cases?process_id={process_id}")
    assert cases.status_code == 200
    case_body = cases.json()
    assert isinstance(case_body, list)
    assert len(case_body) == 1
    assert "case_name" in case_body[0]
    assert "match_status" in case_body[0]


def test_ingest_rejects_non_image() -> None:
    files = {"file": ("sample.txt", b"hello", "text/plain")}
    response = client.post("/api/documents/ingest", files=files)
    assert response.status_code == 400


def test_cases_requires_process_id() -> None:
    response = client.get("/api/cases")
    assert response.status_code == 422
