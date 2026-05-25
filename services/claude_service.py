import base64
import json
from pathlib import Path
from typing import Any

import anthropic

from config.settings import ANTHROPIC_API_KEY

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def ask_text(prompt: str, system: str = "") -> str:
    """Envia un prompt de texto a Claude y retorna la respuesta."""
    messages = [{"role": "user", "content": prompt}]
    response = get_client().messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def ask_with_image(
    image_data: bytes,
    media_type: str,
    prompt: str,
    system: str = "",
) -> str:
    """Envia una imagen con un prompt a Claude Vision y retorna la respuesta."""
    b64_image = base64.b64encode(image_data).decode("utf-8")
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": b64_image,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]
    response = get_client().messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def ask_json(prompt: str, system: str = "") -> dict[str, Any]:
    """Envia un prompt y parsea la respuesta como JSON."""
    raw = ask_text(prompt, system)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned)


def ask_json_with_image(
    image_data: bytes,
    media_type: str,
    prompt: str,
    system: str = "",
) -> dict[str, Any]:
    """Envia una imagen con prompt y parsea la respuesta como JSON."""
    raw = ask_with_image(image_data, media_type, prompt, system)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned)


def detect_media_type(file_path: Path) -> str:
    """Detecta el media type basado en la extension del archivo."""
    suffix = file_path.suffix.lower()
    types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return types.get(suffix, "image/jpeg")
