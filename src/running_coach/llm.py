"""OpenAI-compatible LLM client used by the portable MVP."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    api_key: str
    model: str


class LlmError(RuntimeError):
    """Raised when an LLM request fails."""


def build_client_from_env(*, vision: bool = False, timeout_sec: int = 120) -> "OpenAICompatibleClient":
    """Build a client from LLM_* environment variables."""

    base_url = os.environ.get("LLM_BASE_URL", "").strip()
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    model = ""
    if vision:
        model = os.environ.get("LLM_VISION_MODEL", "").strip()
    model = model or os.environ.get("LLM_MODEL", "").strip()

    missing = [
        name
        for name, value in {
            "LLM_BASE_URL": base_url,
            "LLM_API_KEY": api_key,
            "LLM_VISION_MODEL or LLM_MODEL": model,
        }.items()
        if not value
    ]
    if missing:
        raise LlmError("Missing LLM settings in .env: " + ", ".join(missing))

    return OpenAICompatibleClient(LlmConfig(base_url=base_url, api_key=api_key, model=model), timeout_sec=timeout_sec)


class OpenAICompatibleClient:
    """Small dependency-free client for OpenAI-compatible chat completions."""

    def __init__(self, config: LlmConfig, *, timeout_sec: int = 120) -> None:
        self.config = config
        self.timeout_sec = timeout_sec

    def chat(self, messages: list[dict[str, Any]], *, temperature: float = 0) -> str:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
        }
        response = self._post("/chat/completions", payload)
        try:
            return str(response["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError(f"Unexpected LLM response shape: {response!r}") from exc

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = self.config.base_url.rstrip("/") + path
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise LlmError(f"LLM HTTP {exc.code}: {details}") from exc
        except urllib.error.URLError as exc:
            raise LlmError(f"LLM request failed: {exc.reason}") from exc
