import asyncio
from types import SimpleNamespace

import pytest

from backend import llm
from backend.files import DocumentError
from backend.models import ExtractionResult, Questionnaire
from tests.test_models import SAMPLE


@pytest.mark.parametrize(
    "status,parsed,expected",
    [
        (
            "completed",
            ExtractionResult(status="ok", questionnaire=Questionnaire.model_validate(SAMPLE)),
            None,
        ),
        ("incomplete", None, 502),
        ("completed", None, 502),
        ("completed", ExtractionResult(status="no_items", questionnaire=None), 422),
        ("completed", ExtractionResult(status="too_many_items", questionnaire=None), 413),
    ],
)
def test_provider_contract(monkeypatch, status, parsed, expected):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["max_retries"] == 0
            self.responses = self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def parse(self, **kwargs):
            assert kwargs["store"] is False
            assert kwargs["reasoning"] == {"effort": "none"}
            assert kwargs["max_output_tokens"] == 24000
            return SimpleNamespace(status=status, output_parsed=parsed)

    monkeypatch.setattr(llm, "AsyncOpenAI", FakeClient)
    if expected:
        with pytest.raises(DocumentError) as error:
            asyncio.run(llm.extract_questionnaire("Document text"))
        assert error.value.status == expected
    else:
        assert asyncio.run(llm.extract_questionnaire("Document text")) == parsed.questionnaire


def test_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(DocumentError) as error:
        asyncio.run(llm.extract_questionnaire("text"))
    assert error.value.status == 503
