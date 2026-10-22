"""Embedder falso y determinista: bolsa de palabras con hashing. Basta para que los textos que
comparten palabras se parezcan, sin llamar a ningún modelo."""

import hashlib
import re

DIMENSION = 256


class FakeEmbedder:
    def __init__(self):
        self.llamadas = 0

    def embed(self, textos: list[str]) -> list[list[float]]:
        self.llamadas += 1
        return [self._vector(t) for t in textos]

    def _vector(self, texto: str) -> list[float]:
        v = [0.0] * DIMENSION
        for palabra in re.findall(r"\w+", texto.lower()):
            if len(palabra) > 2:  # ignora "de", "la", etc.
                v[int(hashlib.md5(palabra.encode()).hexdigest(), 16) % DIMENSION] += 1.0
        return v
