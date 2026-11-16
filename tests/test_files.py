from io import BytesIO
from zipfile import ZipFile

import pytest
from docx import Document
from openpyxl import Workbook
from pypdf import PdfWriter

from backend.files import MAX_BYTES, DocumentError, extract_text


def docx_bytes() -> bytes:
    doc = Document()
    doc.add_paragraph("Cuestionario inventado")
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "1. ¿Cómo te sientes?"
    table.cell(0, 1).text = "A. Bien | B. Mal"
    doc.add_paragraph("Fin del documento")
    stream = BytesIO()
    doc.save(stream)
    return stream.getvalue()


def test_docx_preserves_body_order_and_tables() -> None:
    text = extract_text("sample.docx", docx_bytes())
    assert text.index("Cuestionario") < text.index("¿Cómo") < text.index("Fin")
    assert "A. Bien" in text


def test_xlsx_preserves_cells_and_sheets() -> None:
    workbook = Workbook()
    workbook.active.append(["Pregunta", "Alternativas"])
    workbook.active.append(["1. Elige.", "A. Uno | B. Dos"])
    workbook.create_sheet("Clave").append([1, "A"])
    stream = BytesIO()
    workbook.save(stream)
    text = extract_text("sample.xlsx", stream.getvalue())
    assert "1. Elige." in text and "A. Uno | B. Dos" in text and "Clave" in text


@pytest.mark.parametrize(
    "name,content",
    [
        ("bad.txt", b"hi"),
        ("fake.pdf", b"not PDF"),
        ("fake.docx", b"PK nonsense"),
        ("empty.pdf", b""),
        ("large.pdf", b"x" * (MAX_BYTES + 1)),
    ],
)
def test_rejects_invalid_upload(name: str, content: bytes) -> None:
    with pytest.raises(DocumentError):
        extract_text(name, content)


def test_rejects_wrong_office_container() -> None:
    with pytest.raises(DocumentError):
        extract_text("wrong.xlsx", docx_bytes())


def test_rejects_zip_expansion() -> None:
    stream = BytesIO()
    with ZipFile(stream, "w", compression=8) as archive:
        archive.writestr("word/document.xml", "x" * 21_000_000)
    with pytest.raises(DocumentError):
        extract_text("bomb.docx", stream.getvalue())


def test_pdf_without_text_is_explicitly_rejected() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    stream = BytesIO()
    writer.write(stream)
    with pytest.raises(DocumentError, match="texto|OCR"):
        extract_text("scan.pdf", stream.getvalue())
