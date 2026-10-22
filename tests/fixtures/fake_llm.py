"""LLM falso y determinista para los tests: ningún test llama a un modelo de verdad."""

from typing import Any

from redteam.llm.base import LLMResponse, Message, Tool, ToolCall


class FakeLLM:
    """Responde según reglas fijas: si el último mensaje del usuario contiene una clave de
    `reglas`, devuelve esa respuesta; si no, devuelve `por_defecto`.

    Cuenta las llamadas para poder comprobar, p. ej., que la caché no llama al modelo.
    """

    def __init__(
        self,
        reglas: dict[str, LLMResponse] | None = None,
        por_defecto: str = "Respuesta de prueba.",
        name: str = "fake",
    ):
        self.name = name
        self.reglas = reglas or {}
        self.por_defecto = por_defecto
        self.llamadas = 0

    def params(self) -> dict[str, Any]:
        return {}

    def generate(
        self, messages: list[Message], tools: list[Tool] | None = None, *, seed: int = 0
    ) -> LLMResponse:
        self.llamadas += 1
        ultimo = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        for clave, respuesta in self.reglas.items():
            if clave in ultimo:
                return respuesta
        return LLMResponse(content=self.por_defecto)


def respuesta_con_herramienta(nombre: str, **argumentos: Any) -> LLMResponse:
    """Atajo para reglas que hacen que el LLM falso llame a una herramienta."""
    return LLMResponse(content="", tool_calls=[ToolCall(nombre, argumentos)])
