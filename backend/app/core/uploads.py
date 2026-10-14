from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
ALLOWED = {".pdf": "application/pdf", ".txt": "text/plain; charset=utf-8", ".md": "text/plain; charset=utf-8"}
MAX_BYTES = 10 * 1024 * 1024


def store_upload(file: UploadFile) -> tuple[str, str]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, "Only PDF, txt, and Markdown files are allowed")
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "File is too large")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid4().hex}{suffix}"
    (UPLOAD_DIR / stored).write_bytes(data)
    name = Path(file.filename).name[:255] if file.filename else f"file{suffix}"
    return name, stored


def unlink(stored: str) -> None:
    (UPLOAD_DIR / stored).unlink(missing_ok=True)


def file_response(stored: str, name: str) -> FileResponse:
    path = UPLOAD_DIR / stored
    if not path.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(path, media_type=ALLOWED[path.suffix.lower()], filename=name, content_disposition_type="inline")
