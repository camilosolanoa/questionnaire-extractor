import logging
import os
from pathlib import Path

from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic import ValidationError

from backend.files import DocumentError
from backend.models import ExtractionResult, Questionnaire

PROMPT = Path(__file__).with_name("prompt.txt").read_text(encoding="utf-8")
logger = logging.getLogger(__name__)


async def extract_questionnaire(text: str) -> Questionnaire:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise DocumentError("El servicio de extracción no está configurado.", 503)
    try:
        async with AsyncOpenAI(api_key=key, timeout=65, max_retries=0) as client:
            response = await client.responses.parse(
                model=os.getenv("OPENAI_MODEL", "gpt-6-luna"),
                instructions=PROMPT,
                input=[{"role": "user", "content": text}],
                text_format=ExtractionResult,
                reasoning={"effort": "none"},
                max_output_tokens=24000,
                store=False,
            )
        if response.status != "completed" or response.output_parsed is None:
            raise DocumentError(
                "No se obtuvo un resultado completo. Prueba con un documento más corto.", 502
            )
        extraction = response.output_parsed
        if extraction.status == "too_many_items":
            raise DocumentError(
                "El cuestionario supera los 100 ítems. Divídelo en documentos más pequeños.", 413
            )
        result = extraction.questionnaire
        if result is None or not result.items:
            raise DocumentError("No se detectaron ítems de cuestionario en el documento.")
        return result
    except APITimeoutError as error:
        raise DocumentError(
            "El procesamiento tardó demasiado. Intenta con menos páginas.", 504
        ) from error
    except RateLimitError as error:
        raise DocumentError(
            "El proveedor está temporalmente ocupado. Intenta más tarde.", 503
        ) from error
    except (APIError, ValidationError) as error:
        logger.warning("Extraction failed: %s", type(error).__name__)
        raise DocumentError(
            "No se pudo obtener un JSON válido. Intenta nuevamente.", 502
        ) from error
