from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class LLMResponse:
    ok: bool
    content: str
    model: str
    provider: str
    error: str | None = None


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str, system_prompt: str | None = None, temperature: float = 0.1) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        req = request.Request(
            url=f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                body = resp.read().decode("utf-8")
                parsed = json.loads(body)
        except error.URLError as exc:
            return LLMResponse(
                ok=False,
                content="",
                model=self.model,
                provider="ollama",
                error=f"Could not reach Ollama at {self.base_url}: {exc}",
            )
        except json.JSONDecodeError as exc:
            return LLMResponse(
                ok=False,
                content="",
                model=self.model,
                provider="ollama",
                error=f"Invalid JSON from Ollama: {exc}",
            )

        response_text = parsed.get("response") if isinstance(parsed, dict) else None
        if not isinstance(response_text, str):
            return LLMResponse(
                ok=False,
                content="",
                model=self.model,
                provider="ollama",
                error="Ollama response did not include text output.",
            )

        return LLMResponse(
            ok=True,
            content=response_text.strip(),
            model=self.model,
            provider="ollama",
        )

    def is_available(self) -> tuple[bool, str | None]:
        req = request.Request(url=f"{self.base_url}/api/tags", method="GET")
        try:
            with request.urlopen(req, timeout=min(self.timeout_seconds, 5)) as resp:
                body = resp.read().decode("utf-8")
                parsed = json.loads(body)
        except error.URLError as exc:
            return False, f"Could not reach Ollama at {self.base_url}: {exc}"
        except json.JSONDecodeError as exc:
            return False, f"Invalid JSON from Ollama: {exc}"

        if not isinstance(parsed, dict):
            return False, "Unexpected Ollama health response."
        return True, None
