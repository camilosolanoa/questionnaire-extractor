"""Opt-in real API evaluation (incurs token charges); expected files are never rewritten."""

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

from backend.files import extract_text
from backend.llm import extract_questionnaire


async def main():
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")
    for name in ["cuestionario-es.pdf", "questionario-it.docx", "questionnaire-en.xlsx"]:
        path = root / "examples" / name
        expected = json.loads(path.with_suffix(".expected.json").read_text(encoding="utf-8"))
        actual = (await extract_questionnaire(extract_text(name, path.read_bytes()))).model_dump()
        path.with_suffix(".result.json").write_text(
            json.dumps(actual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        assert actual == expected, f"Mismatch: {name}; compare .result.json and .expected.json"
        print(
            f"PASS {name}: six items, five types, shared scale and explicit keys only", flush=True
        )


if __name__ == "__main__":
    asyncio.run(main())
