"""Capa de modelos: interfaz única, cliente de Ollama y caché en disco."""

from typing import Any

from redteam.config import RAIZ
from redteam.llm.base import LLM, LLMResponse, Message, Tool, ToolCall
from redteam.llm.cache import CachedLLM
from redteam.llm.ollama import OllamaLLM

__all__ = ["LLM", "LLMResponse", "Message", "Tool", "ToolCall", "CachedLLM", "build_llm"]


def build_llm(config: dict[str, Any], modelo: str | None = None) -> LLM:
    """Crea el modelo indicado (o el de `config["modelo"]`), con caché si está activa."""
    modelo = modelo or config["modelo"]
    opciones = config["modelos"].get(modelo) or {}
    gen = config["generacion"]
    llm: LLM = OllamaLLM(
        name=modelo,
        host=config["ollama"]["host"],
        temperature=gen["temperatura"],
        max_tokens=gen["max_tokens"],
        think=opciones.get("think"),
        timeout_s=config["ollama"]["timeout_s"],
    )
    if config["cache"]["activa"]:
        llm = CachedLLM(llm, RAIZ / config["cache"]["directorio"])
    return llm
