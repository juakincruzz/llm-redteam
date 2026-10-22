"""Datos ficticios de la tienda: clientes, pedidos y documentos para el RAG."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from redteam.config import RAIZ

DIR_DATOS = RAIZ / "data"


@dataclass(frozen=True)
class Documento:
    id: str  # p. ej. "envios#plazos-de-entrega" o "ficha#C001"
    texto: str


@dataclass
class Tienda:
    clientes: dict[str, dict[str, Any]]  # por id de cliente
    pedidos: dict[str, dict[str, Any]]  # por id de pedido (con su "cliente_id")
    documentos: list[Documento]

    def canarios_de_fichas(self) -> dict[str, str]:
        """Canario de cada cliente: {id_cliente: canario}."""
        return {cid: c["canario"] for cid, c in self.clientes.items()}


def cargar_tienda(dir_datos: Path = DIR_DATOS) -> Tienda:
    with open(dir_datos / "clientes.yaml", encoding="utf-8") as f:
        clientes = {c["id"]: c for c in yaml.safe_load(f)["clientes"]}

    pedidos = {}
    for cliente in clientes.values():
        for pedido in cliente["pedidos"]:
            pedidos[pedido["id"]] = {**pedido, "cliente_id": cliente["id"]}

    documentos = []
    for ruta in sorted((dir_datos / "documentos").glob("*.md")):
        documentos += trocear_markdown(ruta.stem, ruta.read_text(encoding="utf-8"))
    # Las fichas de clientes también se indexan: es el diseño "perezoso" que hace posible el robo
    # de datos (el RAG puede recuperar la ficha de otro cliente).
    documentos += [Documento(f"ficha#{c['id']}", texto_ficha(c)) for c in clientes.values()]

    return Tienda(clientes=clientes, pedidos=pedidos, documentos=documentos)


def trocear_markdown(nombre: str, texto: str) -> list[Documento]:
    """Un trozo por sección "## ...". Cada trozo lleva delante el título del documento."""
    lineas = texto.strip().splitlines()
    titulo = lineas[0].lstrip("# ").strip()
    secciones: list[tuple[str, list[str]]] = [("", [])]
    for linea in lineas[1:]:
        if linea.startswith("## "):
            secciones.append((linea[3:].strip(), []))
        else:
            secciones[-1][1].append(linea)

    trozos = []
    for subtitulo, cuerpo in secciones:
        cuerpo_txt = "\n".join(cuerpo).strip()
        if not cuerpo_txt:
            continue
        cabecera = f"{titulo} — {subtitulo}" if subtitulo else titulo
        slug = subtitulo.lower().replace(" ", "-") if subtitulo else "general"
        trozos.append(Documento(f"{nombre}#{slug}", f"{cabecera}\n{cuerpo_txt}"))
    return trozos


def texto_ficha(cliente: dict[str, Any]) -> str:
    pedidos = ", ".join(f"{p['id']} ({p['estado']})" for p in cliente["pedidos"])
    return (
        f"Ficha de cliente {cliente['id']}\n"
        f"Nombre: {cliente['nombre']}\n"
        f"Correo: {cliente['email']}\n"
        f"Teléfono: {cliente['telefono']}\n"
        f"Dirección: {cliente['direccion']}\n"
        f"Cliente desde: {cliente['cliente_desde']}\n"
        f"Notas internas: {cliente['notas']}\n"
        f"Código interno de verificación (confidencial): {cliente['canario']}\n"
        f"Pedidos: {pedidos}"
    )
