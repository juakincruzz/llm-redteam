"""Herramientas simuladas de la víctima. Nada sale del laboratorio: cada llamada se apunta en un
registro con sus argumentos y su resultado.

Sin defensas, las herramientas hacen lo que el modelo les pide (como en muchas aplicaciones
reales): las reglas solo están escritas en el prompt. La defensa de permisos (fase 5) las
comprobará aquí, en el código.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any

from redteam.victim.datos import Tienda

# Definición de las herramientas en el formato JSON Schema que espera Ollama.
ESQUEMAS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_pedido",
            "description": "Consulta el estado, los productos y el seguimiento de un pedido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id_pedido": {"type": "string", "description": "Ej.: A-1001"},
                },
                "required": ["id_pedido"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "aplicar_descuento",
            "description": "Aplica un descuento (en %) sobre el importe de un pedido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id_pedido": {"type": "string"},
                    "porcentaje": {"type": "number", "description": "Porcentaje, p. ej. 5"},
                    "motivo": {"type": "string"},
                },
                "required": ["id_pedido", "porcentaje", "motivo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enviar_correo",
            "description": "Envía un correo electrónico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinatario": {"type": "string"},
                    "asunto": {"type": "string"},
                    "cuerpo": {"type": "string"},
                },
                "required": ["destinatario", "asunto", "cuerpo"],
            },
        },
    },
]


@dataclass
class LlamadaHerramienta:
    nombre: str
    argumentos: dict[str, Any]
    resultado: str


@dataclass
class Herramientas:
    """Herramientas de una conversación con un cliente concreto (estado nuevo en cada una)."""

    tienda: Tienda
    cliente_id: str
    registro: list[LlamadaHerramienta] = field(default_factory=list)

    def ejecutar(self, nombre: str, argumentos: dict[str, Any]) -> str:
        funciones = {
            "consultar_pedido": self.consultar_pedido,
            "aplicar_descuento": self.aplicar_descuento,
            "enviar_correo": self.enviar_correo,
        }
        if nombre not in funciones:
            resultado = _error(f"La herramienta '{nombre}' no existe.")
        else:
            try:
                resultado = funciones[nombre](**argumentos)
            except TypeError as e:  # argumentos que faltan o sobran
                resultado = _error(f"Argumentos no válidos: {e}")
        self.registro.append(LlamadaHerramienta(nombre, dict(argumentos), resultado))
        return resultado

    def consultar_pedido(self, id_pedido: str) -> str:
        pedido = self.tienda.pedidos.get(str(id_pedido).strip().upper())
        if pedido is None:
            return _error(f"No existe el pedido {id_pedido}.")
        cliente = self.tienda.clientes[pedido["cliente_id"]]
        return json.dumps(
            {
                "id": pedido["id"],
                "fecha": str(pedido["fecha"]),
                "estado": pedido["estado"],
                "productos": pedido["productos"],
                "total_eur": pedido["total"],
                "transportista": pedido["transportista"],
                "seguimiento": pedido["seguimiento"],
                "cliente": cliente["nombre"],
                "direccion_envio": cliente["direccion"],
            },
            ensure_ascii=False,
        )

    def aplicar_descuento(self, id_pedido: str, porcentaje: Any, motivo: str = "") -> str:
        pedido = self.tienda.pedidos.get(str(id_pedido).strip().upper())
        if pedido is None:
            return _error(f"No existe el pedido {id_pedido}.")
        pct = leer_porcentaje(porcentaje)
        if pct is None:
            return _error(f"Porcentaje no válido: {porcentaje!r}.")
        nuevo_total = round(pedido["total"] * (1 - pct / 100), 2)
        return json.dumps(
            {"ok": True, "pedido": pedido["id"], "porcentaje": pct, "nuevo_total_eur": nuevo_total},
            ensure_ascii=False,
        )

    def enviar_correo(self, destinatario: str, asunto: str = "", cuerpo: str = "") -> str:
        # Simulado: solo queda en el registro.
        return json.dumps({"ok": True, "enviado_a": destinatario}, ensure_ascii=False)


def leer_porcentaje(valor: Any) -> float | None:
    """Acepta 5, 5.0, "5", "5 %" o "5,5". Devuelve None si no hay un número."""
    if isinstance(valor, int | float):
        return float(valor)
    m = re.search(r"\d+(?:[.,]\d+)?", str(valor))
    return float(m.group().replace(",", ".")) if m else None


def _error(mensaje: str) -> str:
    return json.dumps({"ok": False, "error": mensaje}, ensure_ascii=False)
