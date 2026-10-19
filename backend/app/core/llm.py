import json
import urllib.error
import urllib.request

from fastapi import HTTPException

from app.core.config import settings


def complete(prompt: str) -> str:
    if not settings.llm_api_key:
        raise HTTPException(503, "Here is no API key")
    payload = json.dumps(
        {
            "model": settings.llm_model,
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
        with urllib.request.urlopen(req, timeout=60) as res:
            data = json.loads(res.read().decode())
    except urllib.error.HTTPError as err:
        raise HTTPException(502, err.read().decode()[:300] or "LLM request failed") from err
    except urllib.error.URLError as err:
        raise HTTPException(502, "Could not reach the LLM") from err
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as err:
        raise HTTPException(502, "LLM returned an empty answer") from err
    if not text or not str(text).strip():
        raise HTTPException(502, "LLM returned an empty answer")
    return str(text).strip()
