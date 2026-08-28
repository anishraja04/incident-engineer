"""OpenAI-compatible LLM client (works with DeepSeek, Gemini, any compatible endpoint).

Configuration via env vars (or .env file at repo root):
    LLM_BASE_URL  e.g. https://api.deepseek.com
    LLM_API_KEY
    LLM_MODEL     e.g. deepseek-chat, gemini-2.5-pro

Prices (USD per 1M tokens) are configurable for cost accounting.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()


PRICES: dict[str, tuple[float, float]] = {
    # model -> (input $/1M tokens, output $/1M tokens)
    "deepseek-chat": (0.27, 1.10),
    "deepseek-reasoner": (0.55, 2.19),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.5-flash": (0.30, 2.50),
}


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0

    def cost(self, model: str) -> float:
        in_p, out_p = PRICES.get(model, (0.5, 1.5))
        return (
            self.input_tokens * in_p / 1_000_000
            + self.output_tokens * out_p / 1_000_000
            + self.cache_read_tokens * in_p / 1_000_000 * 0.1
        )


@dataclass
class LLMResult:
    content: str
    usage: Usage = field(default_factory=Usage)
    raw: Any = None


class LLM:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = base_url or os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.model = model or os.environ.get("LLM_MODEL", "deepseek-chat")
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int | None = 4096,
        json_mode: bool = False,
    ) -> LLMResult:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self.client.chat.completions.create(**kwargs)
        u = resp.usage
        usage = Usage(
            input_tokens=u.prompt_tokens or 0,
            output_tokens=u.completion_tokens or 0,
            cache_read_tokens=getattr(u, "prompt_tokens_details", None)
            and getattr(u.prompt_tokens_details, "cached_tokens", 0)
            or 0,
        )
        return LLMResult(content=resp.choices[0].message.content or "", usage=usage, raw=resp)

    def chat_json(self, messages: list[dict], temperature: float = 0.2) -> LLMResult:
        res = self.chat(messages, temperature=temperature, json_mode=True)
        res.content = res.content.strip()
        if res.content.startswith("```"):
            res.content = res.content.strip("`")
            if res.content.startswith("json"):
                res.content = res.content[4:]
        res.json = json.loads(res.content)  # type: ignore[attr-defined]
        return res