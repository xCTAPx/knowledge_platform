import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from http.client import HTTPResponse

from fastapi import HTTPException

from app.core.config import settings


def _open(prompt: str) -> HTTPResponse:
    if not settings.llm_api_key:
        raise HTTPException(503, "Here is no API key")
    payload = json.dumps(
        {
            "model": settings.llm_model,
            "stream": True,
            "messages": [
                {
                    "role": "system",
                    "content": "Answer using only the user's library excerpts. If they are not enough, say so.",
                },
                {"role": "user", "content": prompt},
            ],
        }
    ).encode()
    req = urllib.request.Request(
        f"{settings.llm_base_url.rstrip('/')}/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.frontend_origin,
            "X-Title": settings.app_name,
        },
    )
    try:
        return urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as err:
        raise HTTPException(502, err.read().decode()[:300] or "LLM request failed") from err
    except urllib.error.URLError as err:
        raise HTTPException(502, "Could not reach the LLM") from err


def stream(prompt: str) -> Iterator[bytes]:
    res = _open(prompt)

    def chunks() -> Iterator[bytes]:
        with res:
            while True:
                line = res.readline()
                if not line:
                    break
                raw = line.decode().strip()
                if not raw.startswith("data:"):
                    continue
                data = raw[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    piece = json.loads(data)["choices"][0]["delta"].get("content")
                except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                    continue
                if piece:
                    yield str(piece).encode()

    return chunks()
