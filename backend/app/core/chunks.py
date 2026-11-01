from pathlib import Path

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from pypdf import PdfReader

CHUNK_TOKENS = 600
CHUNK_OVERLAP = 80

_headers = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
    strip_headers=False,
)
_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base",
    chunk_size=CHUNK_TOKENS,
    chunk_overlap=CHUNK_OVERLAP,
)


def file_text(path: Path) -> str:
    if not path.is_file():
        return ""
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix != ".pdf":
        return ""
    pages = [page.extract_text() or "" for page in PdfReader(path).pages]
    return "\n\n".join(pages)


def split_text(text: str, title: str, markdown: bool) -> list[str]:
    body = text.strip()
    if not body:
        return []
    sections = _headers.split_text(body) if markdown else []
    pieces = [doc.page_content for doc in sections] or [body]
    head = f"# {title}\n" if title else ""
    return [head + piece.strip() for piece in _flatten(pieces) if piece.strip()]


def _flatten(pieces: list[str]) -> list[str]:
    out: list[str] = []
    for piece in pieces:
        out.extend(_splitter.split_text(piece))
    return out
