from copy import deepcopy

import pytest
from pydantic import ValidationError

from backend.models import Questionnaire

SAMPLE = {
    "titulo": "Ejemplo",
    "idioma": "es",
    "total_items": 1,
    "items": [
        {
            "numero": 1,
            "enunciado": "Elige un color.",
            "tipo": "seleccion_multiple",
            "alternativas": [{"valor": "A", "texto": "Azul"}, {"valor": "B", "texto": "Rojo"}],
            "respuesta_correcta": None,
        }
    ],
}


def test_valid_output() -> None:
    assert Questionnaire.model_validate(SAMPLE).model_dump() == SAMPLE


@pytest.mark.parametrize(
    "change",
    [
        "count",
        "duplicate_number",
        "answer",
        "empty_text",
        "duplicate_choice",
        "essay_choices",
        "true_false_count",
    ],
)
def test_rejects_inconsistent_output(change: str) -> None:
    data = deepcopy(SAMPLE)
    item = data["items"][0]
    if change == "count":
        data["total_items"] = 2
    elif change == "duplicate_number":
        data["items"].append(deepcopy(item))
        data["total_items"] = 2
    elif change == "answer":
        item["respuesta_correcta"] = "C"
    elif change == "empty_text":
        item["enunciado"] = " "
    elif change == "duplicate_choice":
        item["alternativas"][1]["valor"] = "A"
    elif change == "essay_choices":
        item["tipo"] = "desarrollo"
    else:
        item["tipo"] = "verdadero_falso"
        item["alternativas"].pop()
    with pytest.raises(ValidationError):
        Questionnaire.model_validate(data)


def test_matching_representation() -> None:
    data = deepcopy(SAMPLE)
    data["items"][0].update(
        tipo="emparejamiento",
        alternativas=[
            {"valor": "L1", "texto": "Sol"},
            {"valor": "L2", "texto": "Luna"},
            {"valor": "RA", "texto": "Noche"},
            {"valor": "RB", "texto": "Día"},
        ],
        respuesta_correcta="L1=RB;L2=RA",
    )
    Questionnaire.model_validate(data)
    data["items"][0]["respuesta_correcta"] = "L1=RC"
    with pytest.raises(ValidationError):
        Questionnaire.model_validate(data)
