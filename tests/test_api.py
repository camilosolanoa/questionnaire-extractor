import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.files import DocumentError
from backend.models import Questionnaire
from tests.test_files import docx_bytes
from tests.test_models import SAMPLE


@pytest.fixture
def client(monkeypatch):
    main.requests_by_ip.clear()

    async def fake(text):
        assert "¿Cómo te sientes?" in text
        return Questionnaire.model_validate(SAMPLE)

    monkeypatch.setattr(main, "extract_questionnaire", fake)
    return TestClient(main.app)


def test_upload_returns_json(client):
    response = client.post("/api/extract", files={"file": ("example.docx", docx_bytes())})
    assert response.status_code == 200
    assert response.json() == SAMPLE
    assert response.headers["cache-control"] == "no-store"


def test_invalid_file_never_calls_llm(client, monkeypatch):
    async def forbidden(text):
        raise AssertionError("LLM must not receive invalid files")

    monkeypatch.setattr(main, "extract_questionnaire", forbidden)
    response = client.post("/api/extract", files={"file": ("bad.pdf", b"invalid")})
    assert response.status_code == 415
    assert response.json()["detail"]


@pytest.mark.parametrize("status", [422, 502, 503, 504])
def test_provider_error_is_clear(client, monkeypatch, status):
    async def failure(text):
        raise DocumentError("No se pudo procesar.", status)

    monkeypatch.setattr(main, "extract_questionnaire", failure)
    response = client.post("/api/extract", files={"file": ("sample.docx", docx_bytes())})
    assert response.status_code == status
    assert response.json() == {"detail": "No se pudo procesar."}


def test_rate_limit(client):
    for _ in range(10):
        assert (
            client.post("/api/extract", files={"file": ("bad.txt", b"invalid")}).status_code == 415
        )
    assert client.post("/api/extract", files={"file": ("bad.txt", b"invalid")}).status_code == 429


def test_oversized_request(client):
    response = client.post("/api/extract", content=b"x" * 3_100_000)
    assert response.status_code == 413
