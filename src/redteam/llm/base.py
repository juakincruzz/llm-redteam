"""Interfaz común a todos los modelos.

Cualquier modelo (Ollama, el LLM falso de los tests...) implementa
`generate(messages, tools) -> LLMResponse`, así que el resto del código no sabe con cuál habla.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol

# Mensaje en el formato de chat habitual: {"role": "system"|"user"|"assistant"|"tool", ...}
Message = dict[str, Any]
# Herramienta en formato JSON Schema, como la espera Ollama:
# {"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
Tool = dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "tool_calls": [{"name": c.name, "arguments": c.arguments} for c in self.tool_calls],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LLMResponse":
        calls = [ToolCall(c["name"], c["arguments"]) for c in d.get("tool_calls", [])]
        return cls(content=d["content"], tool_calls=calls)


class LLM(Protocol):
    # Identificador del modelo (forma parte de la clave de la caché).
    name: str

    def generate(
        self, messages: list[Message], tools: list[Tool] | None = None, *, seed: int = 0
    ) -> LLMResponse: ...

    def params(self) -> dict[str, Any]:
        """Parámetros que influyen en la respuesta (temperatura, etc.), para la caché."""
        ...
