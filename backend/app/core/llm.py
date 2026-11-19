import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from http.client import HTTPResponse

from fastapi import HTTPException

from app.core.config import settings
from app.core.log import logger

log = logger("llm")


def _post(payload: dict, timeout: int = 120) -> HTTPResponse:
    if not settings.llm_api_key:
        log.error("no API key")
        raise HTTPException(503, "Here is no API key")
    req = urllib.request.Request(
        f"{settings.llm_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.frontend_origin,
            "X-Title": settings.app_name,
        },
    )
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as err:
        detail = err.read().decode()[:300] or "LLM request failed"
        log.error("http %s %s", err.code, detail)
        raise HTTPException(502, detail) from err
    except urllib.error.URLError as err:
        log.error("unreachable %s", err.reason)
        raise HTTPException(502, "Could not reach the LLM") from err


def stream(prompt: str, max_tokens: int | None = None) -> Iterator[bytes]:
    payload = {
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
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    res = _post(payload)

    def chunks() -> Iterator[bytes]:
        got = False
        try:
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
                        got = True
                        yield str(piece).encode()
        except Exception:
            log.exception("stream failed")
            raise
        if not got:
            log.error("stream empty")

    return chunks()


def complete(prompt: str, system: str, max_tokens: int = 24) -> str:
    res = _post(
        {
            "model": settings.llm_model,
            "stream": False,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=30,
    )
    with res:
        data = json.loads(res.read().decode())
    try:
        text = str(data["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError):
        log.error("complete empty")
        return ""
    return text
