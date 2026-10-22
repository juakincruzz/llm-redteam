"""RAG sencillo: embeddings locales con Ollama e índice en memoria.

Con unas pocas decenas de trozos no hace falta ninguna base de datos vectorial: se calcula la
similitud del coseno con todos y se devuelven los k mejores.
"""

import hashlib
import json
import math
from pathlib import Path
from typing import Protocol

import httpx

from redteam.victim.datos import Documento


class Embedder(Protocol):
    def embed(self, textos: list[str]) -> list[list[float]]: ...


class OllamaEmbedder:
    """Embeddings con Ollama (/api/embed), guardados en disco para no recalcularlos."""

    def __init__(
        self, modelo: str, host: str, directorio_cache: Path | str, timeout_s: float = 120
    ):
        self.modelo = modelo
        self.host = host.rstrip("/")
        self.directorio = Path(directorio_cache)
        self.timeout_s = timeout_s

    def _ruta(self, texto: str) -> Path:
        clave = hashlib.sha256(f"{self.modelo}\n{texto}".encode()).hexdigest()
        return self.directorio / f"{clave}.json"

    def embed(self, textos: list[str]) -> list[list[float]]:
        faltan = [t for t in dict.fromkeys(textos) if not self._ruta(t).exists()]
        if faltan:
            r = httpx.post(
                f"{self.host}/api/embed",
                json={"model": self.modelo, "input": faltan},
                timeout=self.timeout_s,
            )
            r.raise_for_status()
            self.directorio.mkdir(parents=True, exist_ok=True)
            for texto, vector in zip(faltan, r.json()["embeddings"], strict=True):
                self._ruta(texto).write_text(json.dumps(vector))
        return [json.loads(self._ruta(t).read_text()) for t in textos]


def coseno(a: list[float], b: list[float]) -> float:
    producto = sum(x * y for x, y in zip(a, b, strict=True))
    normas = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return producto / normas if normas else 0.0


class Indice:
    # nomic-embed-text espera estos prefijos para distinguir consultas de documentos.
    PREFIJO_DOC = "search_document: "
    PREFIJO_CONSULTA = "search_query: "

    def __init__(self, embedder: Embedder, documentos: list[Documento]):
        self.embedder = embedder
        self.documentos = list(documentos)
        self.vectores = embedder.embed([self.PREFIJO_DOC + d.texto for d in self.documentos])

    def buscar(self, consulta: str, k: int = 3) -> list[Documento]:
        v = self.embedder.embed([self.PREFIJO_CONSULTA + consulta])[0]
        puntuados = sorted(
            zip(self.documentos, self.vectores, strict=True),
            key=lambda dv: coseno(v, dv[1]),
            reverse=True,
        )
        return [d for d, _ in puntuados[:k]]

    def con_documentos_extra(self, extra: list[Documento]) -> "Indice":
        """Copia del índice con documentos añadidos (p. ej., envenenados para un ataque)."""
        return Indice(self.embedder, self.documentos + extra)
