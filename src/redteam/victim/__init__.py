"""Aplicación víctima: asistente de la tienda online ficticia Albarizo."""

from typing import Any

from redteam.config import RAIZ
from redteam.llm import LLM, build_llm
from redteam.victim.asistente import Asistente, Conversacion, Turno
from redteam.victim.datos import Tienda, cargar_tienda
from redteam.victim.rag import Indice, OllamaEmbedder

__all__ = ["Asistente", "Conversacion", "Turno", "Tienda", "crear_asistente", "crear_indice"]


def crear_indice(config: dict[str, Any], tienda: Tienda) -> Indice:
    embedder = OllamaEmbedder(
        modelo=config["victima"]["modelo_embeddings"],
        host=config["ollama"]["host"],
        directorio_cache=RAIZ / config["cache"]["directorio_embeddings"],
    )
    return Indice(embedder, tienda.documentos)


def crear_asistente(
    config: dict[str, Any],
    modelo: str | None = None,
    llm: LLM | None = None,
    tienda: Tienda | None = None,
    indice: Indice | None = None,
) -> Asistente:
    """Monta la víctima según la config. Se pueden pasar piezas ya creadas para reutilizarlas."""
    tienda = tienda or cargar_tienda()
    return Asistente(
        llm=llm or build_llm(config, modelo),
        tienda=tienda,
        indice=indice or crear_indice(config, tienda),
        k=config["victima"]["rag_k"],
        max_pasos=config["victima"]["max_pasos_herramientas"],
    )
