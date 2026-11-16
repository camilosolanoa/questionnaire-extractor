from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Value = StrictInt | Text


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Alternative(StrictModel):
    valor: Value
    texto: Text


class Item(StrictModel):
    numero: int = Field(ge=1)
    enunciado: Text
    tipo: Literal[
        "escala_likert", "seleccion_multiple", "verdadero_falso", "desarrollo", "emparejamiento"
    ]
    alternativas: list[Alternative] = Field(max_length=100)
    respuesta_correcta: Value | None

    @model_validator(mode="after")
    def consistent(self) -> Self:
        values = [str(choice.valor) for choice in self.alternativas]
        if len(values) != len(set(values)):
            raise ValueError("Los valores de las alternativas deben ser únicos.")
        if self.tipo == "desarrollo":
            if self.alternativas or self.respuesta_correcta is not None:
                raise ValueError("Desarrollo requiere alternativas vacías y respuesta null.")
        elif self.tipo == "emparejamiento":
            left = {v for v in values if v.startswith("L")}
            right = {v for v in values if v.startswith("R")}
            if not left or not right or len(left | right) != len(values):
                raise ValueError("Emparejamiento requiere alternativas L y R.")
            if self.respuesta_correcta is not None:
                pairs = str(self.respuesta_correcta).split(";")
                used = set()
                for pair in pairs:
                    parts = pair.split("=")
                    if len(parts) != 2 or parts[0] not in left or parts[1] not in right:
                        raise ValueError("Clave de emparejamiento inválida.")
                    if parts[0] in used:
                        raise ValueError("Clave de emparejamiento repetida.")
                    used.add(parts[0])
        else:
            if len(values) < 2 or (self.tipo == "verdadero_falso" and len(values) != 2):
                raise ValueError("Número de alternativas inválido.")
            if self.respuesta_correcta is not None and str(self.respuesta_correcta) not in values:
                raise ValueError("La respuesta correcta debe identificar una alternativa.")
        return self


class Questionnaire(StrictModel):
    titulo: Text
    idioma: str = Field(pattern=r"^[a-z]{2}$")
    total_items: int = Field(ge=0, le=100)
    items: list[Item] = Field(max_length=100)

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.total_items != len(self.items):
            raise ValueError("total_items no coincide con items.")
        if len({item.numero for item in self.items}) != len(self.items):
            raise ValueError("Los números de ítem deben ser únicos.")
        return self


class ExtractionResult(StrictModel):
    status: Literal["ok", "no_items", "too_many_items"]
    questionnaire: Questionnaire | None

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if (self.status == "ok") != (self.questionnaire is not None):
            raise ValueError("El resultado debe acompañar únicamente al estado ok.")
        return self
