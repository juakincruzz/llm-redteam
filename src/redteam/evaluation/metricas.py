"""Métricas comunes."""

import math


def wilson(exitos: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confianza de Wilson para una proporción (por defecto, al 95 %).

    Se usa en vez del intervalo "normal" (p ± z·sqrt(p(1-p)/n)) porque con pocos casos o
    proporciones cercanas a 0 o 1 ese se sale de [0, 1] o da anchura cero.
    """
    if n == 0:
        return (0.0, 1.0)
    p = exitos / n
    z2 = z * z
    denominador = 1 + z2 / n
    centro = (p + z2 / (2 * n)) / denominador
    margen = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denominador
    return (max(0.0, centro - margen), min(1.0, centro + margen))
