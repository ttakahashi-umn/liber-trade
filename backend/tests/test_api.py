import pytest
from fastapi.testclient import TestClient

from app.infrastructure.ollama.ollama_ocr_gateway import OllamaOcrGateway
from app.controller.document_ingest_controller import _repository
from app.infrastructure.minio.minio_storage_gateway import MinioStorageGateway
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_ocr_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    _repository.reset_all_data()

    async def _mock_extract(_: OllamaOcrGateway, image_bytes: bytes, filename: str, supplemental_text: str = "") -> dict:
        if "unknown" in filename.lower():
            return {"line_items": [{"description": "Item A", "qty": 1}]}
        qty = 2
        if "inv" in filename.lower():
            qty = 2.1
        return {
            "invoice_no": f"MOCK-{filename}",
            "line_items": [{"description": "Item A", "unitPrice": 100, "qty": qty, "小計": qty * 100}],
            "税額": 20,
            "合計": qty * 100 + 20,
        }

    monkeypatch.setattr(OllamaOcrGateway, "extract_text_and_tables", _mock_extract)

    def _mock_upload_raw(self: MinioStorageGateway, object_key: str, content: bytes, content_type: str) -> str:
        return f"trade-raw/{object_key}"

    def _mock_upload_rendered(self: MinioStorageGateway, object_key: str, content: bytes, content_type: str = "image/png") -> str:
        return f"trade-rendered/{object_key}"

    def _mock_presigned_get_url(self: MinioStorageGateway, object_ref: str, expires_seconds: int = 3600) -> str:
        return f"http://minio.local/{object_ref}?exp={expires_seconds}"

    monkeypatch.setattr(MinioStorageGateway, "upload_raw", _mock_upload_raw)
    monkeypatch.setattr(MinioStorageGateway, "upload_rendered", _mock_upload_rendered)
    monkeypatch.setattr(MinioStorageGateway, "presigned_get_url", _mock_presigned_get_url)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_and_get_result() -> None:
    files = {"file": ("sample_po.png", b"fake-image-bytes", "image/png")}
    response = client.post(
        "/api/documents/ingest",
        files=files,
        data={"case_no": "CASE-001", "doc_type": "PO"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "process_id" in body
    assert body["case_no"] == "CASE-001"
    assert body["doc_type"] == "PO"
    assert "chain_id" in body
    assert "document_id" in body
    assert body["status"] in {"SUCCESS", "NEEDS_REVIEW", "FAILED"}
    assert body["raw_file_object_key"] is not None
    assert body["rendered_image_object_key"] is not None
    assert body["raw_file_url"] is not None
    assert body["rendered_image_url"] is not None
    process_id = body["process_id"]
    chain_id = body["chain_id"]

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

    documents = client.get(f"/api/cases/{chain_id}/documents")
    assert documents.status_code == 200
    documents_body = documents.json()
    assert len(documents_body) == 1
    assert documents_body[0]["doc_type"] == "PO"


def test_ingest_infers_doc_type_when_omitted() -> None:
    files = {"file": ("sample_inv.png", b"fake-image-bytes", "image/png")}
    response = client.post("/api/documents/ingest", files=files, data={"case_no": "CASE-003"})
    assert response.status_code == 200
    body = response.json()
    assert body["doc_type"] == "INV"
    assert body["doc_type_confidence"] is not None
    assert len(body["doc_type_reasons"]) >= 1
    assert body["doc_type_rule_set_version"] == "v1"


def test_ingest_unknown_doc_type_marks_needs_review() -> None:
    files = {"file": ("sample_unknown.png", b"fake-image-bytes", "image/png")}
    response = client.post("/api/documents/ingest", files=files, data={"case_no": "CASE-004"})
    assert response.status_code == 200
    body = response.json()
    assert body["doc_type"] == "UNKNOWN"
    assert body["status"] == "NEEDS_REVIEW"
    assert "doc_type:UNKNOWN" in body["warnings"]
    assert body["doc_type_rule_set_version"] == "v1"


def test_compare_documents_within_case() -> None:
    po_files = {"file": ("sample_po.png", b"fake-image-bytes", "image/png")}
    po_response = client.post(
        "/api/documents/ingest",
        files=po_files,
        data={"case_no": "CASE-002", "doc_type": "PO"},
    )
    assert po_response.status_code == 200
    po_body = po_response.json()

    inv_files = {"file": ("sample_inv.png", b"fake-image-bytes", "image/png")}
    inv_response = client.post(
        "/api/documents/ingest",
        files=inv_files,
        data={"case_no": "CASE-002", "doc_type": "INV"},
    )
    assert inv_response.status_code == 200
    inv_body = inv_response.json()

    compare_response = client.post(
        f"/api/cases/{po_body['chain_id']}/comparisons",
        json={
            "base_document_id": po_body["document_id"],
            "target_document_id": inv_body["document_id"],
            "rule_set_version": "v1",
        },
    )
    assert compare_response.status_code == 200
    compare_body = compare_response.json()
    assert compare_body["result_status"] == "WARN"
    assert len(compare_body["items"]) == 1
    assert compare_body["items"][0]["is_acceptable"] is True


def test_ingest_rejects_non_image() -> None:
    files = {"file": ("sample.txt", b"hello", "text/plain")}
    response = client.post("/api/documents/ingest", files=files)
    assert response.status_code == 400


def test_cases_requires_process_id() -> None:
    response = client.get("/api/cases")
    assert response.status_code == 422


def test_admin_doc_type_rule_set_lifecycle() -> None:
    before = client.get("/api/admin/document-type-rule-sets")
    assert before.status_code == 200
    assert isinstance(before.json(), list)

    create_response = client.post(
        "/api/admin/document-type-rule-sets",
        json={
            "version": "v2",
            "rules": [
                {
                    "rule_id": "v2-inv-1",
                    "doc_type": "INV",
                    "condition_type": "FIELD_EXISTS",
                    "condition_key": "invoice_number",
                    "condition_value": None,
                    "score": 1.0,
                    "priority": 100,
                }
            ],
        },
    )
    assert create_response.status_code == 200
    assert create_response.json()["version"] == "v2"

    activate_response = client.post("/api/admin/document-type-rule-sets/v2/activate")
    assert activate_response.status_code == 200
    assert activate_response.json()["version"] == "v2"


def test_doc_type_override_and_metrics() -> None:
    files = {"file": ("sample_unknown.png", b"fake-image-bytes", "image/png")}
    ingest_response = client.post("/api/documents/ingest", files=files, data={"case_no": "CASE-005"})
    assert ingest_response.status_code == 200
    document_id = ingest_response.json()["document_id"]

    patch_response = client.patch(f"/api/documents/{document_id}/doc-type", json={"doc_type": "PO"})
    assert patch_response.status_code == 200
    assert patch_response.json()["doc_type"] == "PO"

    logs_response = client.get("/api/admin/document-type-inference-logs")
    assert logs_response.status_code == 200
    assert len(logs_response.json()) >= 1

    metrics_response = client.get("/api/admin/document-type-metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert "unknown_rate" in metrics
    assert "override_rate" in metrics
