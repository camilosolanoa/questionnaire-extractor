import asyncio
from collections import deque
from pathlib import Path
from time import monotonic

from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.files import MAX_BYTES, DocumentError, extract_text
from backend.llm import extract_questionnaire
from backend.models import Questionnaire

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
app = FastAPI(title="Questionnaire Extractor")
requests_by_ip: dict[str, deque[float]] = {}


@app.middleware("http")
async def upload_limits(request: Request, call_next):
    if request.url.path == "/api/extract" and request.method == "POST":
        size = request.headers.get("content-length")
        if size and (not size.isdigit() or int(size) > MAX_BYTES + 65_536):
            return JSONResponse({"detail": "El archivo supera el límite de 3 MB."}, status_code=413)
        now = monotonic()
        for address in list(requests_by_ip):
            if not requests_by_ip[address] or requests_by_ip[address][-1] <= now - 60:
                del requests_by_ip[address]
        address = request.client.host if request.client else "unknown"
        if address not in requests_by_ip and len(requests_by_ip) >= 1000:
            return JSONResponse(
                {"detail": "Servicio ocupado. Intenta en un minuto."}, status_code=429
            )
        recent = requests_by_ip.setdefault(address, deque())
        while recent and recent[0] <= now - 60:
            recent.popleft()
        if len(recent) >= 10:
            return JSONResponse(
                {"detail": "Máximo 10 intentos por minuto. Espera e intenta de nuevo."},
                status_code=429,
                headers={"Retry-After": "60"},
            )
        recent.append(now)
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(DocumentError)
async def document_error(request: Request, error: DocumentError):
    return JSONResponse({"detail": str(error)}, status_code=error.status)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/extract", response_model=Questionnaire)
async def extract(file: UploadFile):
    try:
        data = await file.read(MAX_BYTES + 1)
        text = await asyncio.to_thread(extract_text, file.filename or "", data)
        return await extract_questionnaire(text)
    finally:
        await file.close()


app.mount("/examples", StaticFiles(directory=ROOT / "examples", check_dir=False), name="examples")
frontend = ROOT / "frontend" / "dist"
if frontend.is_dir():

    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTMLResponse(
            (frontend / "index.html").read_text(encoding="utf-8"),
            headers={"Cache-Control": "no-store"},
        )

    app.mount("/", StaticFiles(directory=frontend), name="frontend")
