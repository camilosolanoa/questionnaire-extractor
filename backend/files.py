from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from docx import Document
from docx.table import Table
from openpyxl import load_workbook
from pypdf import PdfReader

MAX_BYTES = 3_000_000
MAX_CHARS = 60_000


class DocumentError(Exception):
    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.status = status


def check_office(data: bytes, suffix: str) -> None:
    try:
        with ZipFile(BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 2000 or sum(entry.file_size for entry in entries) > 20_000_000:
                raise DocumentError("El documento comprimido excede el límite permitido.", 413)
            required = "word/document.xml" if suffix == ".docx" else "xl/workbook.xml"
            if required not in archive.namelist():
                raise DocumentError("El contenido no corresponde al formato indicado.", 415)
    except BadZipFile as error:
        raise DocumentError("Archivo Office inválido o dañado.", 415) from error


def extract_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx", ".xlsx"}:
        raise DocumentError("Formato inválido. Usa PDF, DOCX o XLSX.", 415)
    if not data:
        raise DocumentError("El archivo está vacío.")
    if len(data) > MAX_BYTES:
        raise DocumentError("El archivo supera el límite de 3 MB.", 413)
    parts: list[str] = []
    length = 0

    def add(text: str) -> None:
        nonlocal length
        length += len(text) + 1
        if length > MAX_CHARS:
            raise DocumentError("El documento supera el límite de 60.000 caracteres.", 413)
        if text.strip():
            parts.append(text)

    try:
        if suffix == ".pdf":
            if not data.startswith(b"%PDF-"):
                raise DocumentError("El contenido no es un PDF válido.", 415)
            pdf = PdfReader(BytesIO(data))
            if pdf.is_encrypted:
                raise DocumentError("No se admiten PDF protegidos por contraseña.")
            if len(pdf.pages) > 20:
                raise DocumentError("El PDF supera el límite de 20 páginas.", 413)
            for page in pdf.pages:
                text = page.extract_text(extraction_mode="layout") or ""
                if not text.strip():
                    raise DocumentError("El PDF contiene páginas sin texto. Se requiere OCR.")
                add(text)
        else:
            check_office(data, suffix)
            if suffix == ".docx":
                doc = Document(BytesIO(data))
                for block in doc.iter_inner_content():
                    if isinstance(block, Table):
                        for row in block.rows:
                            add(" | ".join(cell.text for cell in row.cells))
                    else:
                        add(block.text)
            else:
                book = load_workbook(BytesIO(data), read_only=True, data_only=False)
                try:
                    if len(book.worksheets) > 10:
                        raise DocumentError("El Excel supera el límite de 10 hojas.", 413)
                    for sheet in book.worksheets:
                        add(f"[Hoja: {sheet.title}]")
                        sheet.reset_dimensions()
                        for index, row in enumerate(sheet.iter_rows()):
                            if index >= 2000 or len(row) > 50:
                                raise DocumentError(
                                    "Excel: máximo 2.000 filas y 50 columnas por hoja.", 413
                                )
                            if any(cell.data_type == "f" for cell in row):
                                raise DocumentError(
                                    "El Excel contiene fórmulas. Exporta sus valores antes de "
                                    "subirlo."
                                )
                            add(
                                " | ".join(
                                    "" if cell.value is None else str(cell.value) for cell in row
                                )
                            )
                finally:
                    book.close()
    except DocumentError:
        raise
    except Exception as error:
        raise DocumentError(
            "No se pudo leer el archivo. Puede estar dañado o protegido."
        ) from error
    text = "\n".join(parts).strip()
    if not text:
        raise DocumentError("No se encontró texto. Los PDF escaneados requieren OCR.")
    return text
