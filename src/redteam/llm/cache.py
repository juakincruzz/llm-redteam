"""Caché de respuestas en disco.

La clave es un hash de modelo + mensajes + herramientas + parámetros + semilla. Si ya existe,
se devuelve la respuesta guardada sin llamar al modelo: los experimentos se repiten gratis y
el panel carga al instante.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from redteam.llm.base import LLM, LLMResponse, Message, Tool


def cache_key(
    model: str,
    messages: list[Message],
    tools: list[Tool] | None,
    params: dict[str, Any],
    seed: int,
) -> str:
    datos = {
        "model": model,
        "messages": messages,
        "tools": tools or [],
        "params": params,
        "seed": seed,
    }
    # sort_keys para que el mismo contenido dé siempre el mismo hash.
    texto = json.dumps(datos, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


class CachedLLM:
    """Envuelve cualquier LLM y guarda sus respuestas en `directorio`."""

    def __init__(self, llm: LLM, directorio: Path | str):
        self.llm = llm
        self.name = llm.name
        self.directorio = Path(directorio)
        self.aciertos = 0
        self.fallos = 0

    def params(self) -> dict[str, Any]:
        return self.llm.params()

    def _ruta(self, clave: str) -> Path:
        # Subcarpetas por los dos primeros caracteres para no tener miles de ficheros juntos.
        return self.directorio / clave[:2] / f"{clave}.json"

    def generate(
        self, messages: list[Message], tools: list[Tool] | None = None, *, seed: int = 0
    ) -> LLMResponse:
        clave = cache_key(self.name, messages, tools, self.params(), seed)
        ruta = self._ruta(clave)
        if ruta.exists():
            self.aciertos += 1
            return LLMResponse.from_dict(json.loads(ruta.read_text(encoding="utf-8")))

        self.fallos += 1
        respuesta = self.llm.generate(messages, tools, seed=seed)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(respuesta.to_dict(), ensure_ascii=False), encoding="utf-8")
        return respuesta
