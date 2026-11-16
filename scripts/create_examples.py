"""Create invented fixtures and their independently specified expected outputs."""

import json
from pathlib import Path

from docx import Document
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1] / "examples"
CASES = [
    {
        "stem": "cuestionario-es",
        "lang": "es",
        "title": "Cuestionario ficticio de hábitos y lógica",
        "scale": ["Nunca", "A veces", "Siempre"],
        "intro": (
            "Material inventado. Para los ítems 1 y 2 usa esta escala: 0 = "
            "Nunca; 1 = A veces; 2 = Siempre."
        ),
        "questions": [
            "Organizo mis tareas antes de comenzar.",
            "Reviso mi trabajo al terminar.",
            "¿Qué número sigue en la serie 2, 4, 8, ...?",
            "El agua puede encontrarse en estado sólido.",
            "Describe una actividad que disfrutes.",
            "Relaciona cada elemento de la columna izquierda con la derecha.",
        ],
        "tf": ["Verdadero", "Falso"],
        "matching": ["Sol", "Luna", "Noche", "Día"],
        "matching_intro": "Columna izquierda: 1. Sol; 2. Luna. Columna derecha: A. Noche; B. Día.",
        "key": (
            "Clave de respuestas explícita: ítem 3 = B; ítem 6 = 1-B, 2-A. "
            "No hay claves para los demás ítems."
        ),
    },
    {
        "stem": "questionario-it",
        "lang": "it",
        "title": "Questionario inventato di abitudini e logica",
        "scale": ["Mai", "A volte", "Sempre"],
        "intro": (
            "Materiale inventato. Per gli item 1 e 2 usa questa scala: 0 = "
            "Mai; 1 = A volte; 2 = Sempre."
        ),
        "questions": [
            "Organizzo i miei compiti prima di iniziare.",
            "Controllo il mio lavoro quando finisco.",
            "Quale numero segue nella serie 2, 4, 8, ...?",
            "L'acqua può trovarsi allo stato solido.",
            "Descrivi un'attività che ti piace.",
            "Abbina ogni elemento della colonna sinistra a quella destra.",
        ],
        "tf": ["Vero", "Falso"],
        "matching": ["Sole", "Luna", "Notte", "Giorno"],
        "matching_intro": (
            "Colonna sinistra: 1. Sole; 2. Luna. Colonna destra: A. Notte; B. Giorno."
        ),
        "key": (
            "Chiave esplicita: item 3 = B; item 6 = 1-B, 2-A. Nessuna chiave per gli altri item."
        ),
    },
    {
        "stem": "questionnaire-en",
        "lang": "en",
        "title": "Fictional habits and logic questionnaire",
        "scale": ["Never", "Sometimes", "Always"],
        "intro": (
            "Invented material. For items 1 and 2 use this scale: 0 = Never; "
            "1 = Sometimes; 2 = Always."
        ),
        "questions": [
            "I organize my tasks before starting.",
            "I review my work when I finish.",
            "Which number follows in the sequence 2, 4, 8, ...?",
            "Water can exist in a solid state.",
            "Describe an activity you enjoy.",
            "Match each entry in the left column to the right column.",
        ],
        "tf": ["True", "False"],
        "matching": ["Sun", "Moon", "Night", "Day"],
        "matching_intro": "Left column: 1. Sun; 2. Moon. Right column: A. Night; B. Day.",
        "key": (
            "Explicit answer key: item 3 = B; item 6 = 1-B, 2-A. No answer keys for other items."
        ),
    },
]


def main():
    ROOT.mkdir(exist_ok=True)
    for case in CASES:
        options = [
            "",
            "",
            "A. 10; B. 16; C. 20",
            f"V. {case['tf'][0]}; F. {case['tf'][1]}",
            "",
            case["matching_intro"],
        ]
        lines = [case["title"], case["intro"]]
        for number, (question, choices) in enumerate(
            zip(case["questions"], options, strict=True), 1
        ):
            lines.append(f"{number}. {question}")
            if choices:
                lines.append(choices)
        lines.append(case["key"])
        path = ROOT / case["stem"]
        path.with_suffix(".txt").write_text("\n".join(lines), encoding="utf-8")
        if case["lang"] == "es":
            styles = getSampleStyleSheet()
            content = []
            for index, line in enumerate(lines):
                content.extend(
                    [
                        Paragraph(line, styles["Title"] if index == 0 else styles["BodyText"]),
                        Spacer(1, 12),
                    ]
                )
            SimpleDocTemplate(str(path.with_suffix(".pdf")), pagesize=A4).build(content)
        elif case["lang"] == "it":
            doc = Document()
            doc.add_heading(case["title"], 0)
            doc.add_paragraph(case["intro"])
            for number, (question, choices) in enumerate(
                zip(case["questions"], options, strict=True), 1
            ):
                doc.add_paragraph(f"{number}. {question}")
                if choices:
                    table = doc.add_table(rows=1, cols=1)
                    table.cell(0, 0).text = choices
            doc.add_paragraph(case["key"])
            doc.save(path.with_suffix(".docx"))
        else:
            book = Workbook()
            sheet = book.active
            sheet.title = "Questions"
            sheet.append([case["title"]])
            sheet.append([case["intro"]])
            sheet.append(["Number", "Question", "Alternatives"])
            for number, (question, choices) in enumerate(
                zip(case["questions"], options, strict=True), 1
            ):
                sheet.append([number, question, choices])
            sheet.column_dimensions["A"].width = 12
            sheet.column_dimensions["B"].width = 85
            sheet.column_dimensions["C"].width = 95
            book.create_sheet("Answer key").append([case["key"]])
            book.save(path.with_suffix(".xlsx"))
        choices = [
            [{"valor": n, "texto": value} for n, value in enumerate(case["scale"])],
            [{"valor": n, "texto": value} for n, value in enumerate(case["scale"])],
            [
                {"valor": key, "texto": value}
                for key, value in zip(["A", "B", "C"], ["10", "16", "20"], strict=True)
            ],
            [
                {"valor": key, "texto": value}
                for key, value in zip(["V", "F"], case["tf"], strict=True)
            ],
            [],
            [
                {"valor": key, "texto": value}
                for key, value in zip(["L1", "L2", "RA", "RB"], case["matching"], strict=True)
            ],
        ]
        expected = {
            "titulo": case["title"],
            "idioma": case["lang"],
            "total_items": 6,
            "items": [
                {
                    "numero": i + 1,
                    "enunciado": question,
                    "tipo": kind,
                    "alternativas": alternatives,
                    "respuesta_correcta": answer,
                }
                for i, (question, kind, alternatives, answer) in enumerate(
                    zip(
                        case["questions"],
                        [
                            "escala_likert",
                            "escala_likert",
                            "seleccion_multiple",
                            "verdadero_falso",
                            "desarrollo",
                            "emparejamiento",
                        ],
                        choices,
                        [None, None, "B", None, None, "L1=RB;L2=RA"],
                        strict=True,
                    )
                )
            ],
        }
        path.with_suffix(".expected.json").write_text(
            json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
