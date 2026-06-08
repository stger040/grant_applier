"""Optional OpenAI-backed helpers for richer draft text generation."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"


def can_use_openai(use_llm: bool) -> bool:
    return use_llm and bool(os.getenv("OPENAI_API_KEY"))


def generate_section_with_openai(
    *,
    use_llm: bool,
    model: str,
    prompt: str,
    timeout_seconds: int = 40,
) -> str | None:
    if not can_use_openai(use_llm):
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    payload = {
        "model": model,
        "input": prompt,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_RESPONSES_ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="ignore")
    except (urllib.error.URLError, TimeoutError):
        return None
    except Exception:
        return None

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return extract_text(parsed)


def extract_text(payload: dict) -> str | None:
    output = payload.get("output")
    if not isinstance(output, list):
        return None
    chunks: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") in {"output_text", "text"}:
                text = block.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
    if not chunks:
        return None
    return "\n\n".join(chunks)
