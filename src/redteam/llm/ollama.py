"""Modelos locales servidos por Ollama (API /api/chat)."""

from typing import Any

import httpx

from redteam.llm.base import LLMResponse, Message, Tool, ToolCall


class OllamaLLM:
    def __init__(
        self,
        name: str,
        host: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 512,
        think: bool | None = None,
        timeout_s: float = 180,
    ):
        self.name = name
        self.host = host.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.think = think
        self.timeout_s = timeout_s

    def params(self) -> dict[str, Any]:
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "think": self.think,
        }

    def generate(
        self, messages: list[Message], tools: list[Tool] | None = None, *, seed: int = 0
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "seed": seed,
            },
        }
        if tools:
            payload["tools"] = tools
        if self.think is not None:
            payload["think"] = self.think

        r = httpx.post(f"{self.host}/api/chat", json=payload, timeout=self.timeout_s)
        r.raise_for_status()
        msg = r.json()["message"]
        calls = [
            ToolCall(c["function"]["name"], c["function"].get("arguments") or {})
            for c in msg.get("tool_calls") or []
        ]
        return LLMResponse(content=msg.get("content", ""), tool_calls=calls)
