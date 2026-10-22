"""Carga de config/config.yaml."""

from pathlib import Path
from typing import Any

import yaml

# Raíz del repositorio (src/redteam/config.py -> ../../).
RAIZ = Path(__file__).resolve().parents[2]
RUTA_CONFIG = RAIZ / "config" / "config.yaml"


def cargar_config(ruta: Path | str = RUTA_CONFIG) -> dict[str, Any]:
    """Lee el YAML de configuración y lo devuelve como diccionario."""
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)
