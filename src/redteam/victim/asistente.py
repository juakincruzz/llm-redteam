"""El asistente víctima: RAG + modelo + herramientas, turno a turno."""

from dataclasses import dataclass, field

from redteam.llm import LLM, Message
from redteam.victim.datos import Documento, Tienda
from redteam.victim.herramientas import ESQUEMAS, Herramientas, LlamadaHerramienta
from redteam.victim.rag import Indice
from redteam.victim.reglas import prompt_sistema


@dataclass
class Turno:
    usuario: str
    respuesta: str
    documentos: list[str]  # ids de los trozos recuperados por el RAG
    llamadas: list[LlamadaHerramienta]


@dataclass
class Conversacion:
    cliente_id: str
    turnos: list[Turno] = field(default_factory=list)

    @property
    def llamadas(self) -> list[LlamadaHerramienta]:
        return [ll for t in self.turnos for ll in t.llamadas]

    @property
    def texto_respuestas(self) -> str:
        return "\n".join(t.respuesta for t in self.turnos)


def formatear_documentos(documentos: list[Documento]) -> str:
    return "\n\n".join(f"[{d.id}]\n{d.texto}" for d in documentos)


class Asistente:
    def __init__(self, llm: LLM, tienda: Tienda, indice: Indice, k: int = 3, max_pasos: int = 4):
        self.llm = llm
        self.tienda = tienda
        self.indice = indice
        self.k = k
        self.max_pasos = max_pasos  # máximo de rondas de herramientas por turno

    def conversar(
        self, cliente_id: str, mensajes_usuario: list[str] | str, *, seed: int = 0
    ) -> Conversacion:
        """Procesa uno o varios mensajes del usuario seguidos (ataques de varios turnos)."""
        if isinstance(mensajes_usuario, str):
            mensajes_usuario = [mensajes_usuario]
        cliente = self.tienda.clientes[cliente_id]
        herramientas = Herramientas(self.tienda, cliente_id)
        conversacion = Conversacion(cliente_id)
        historial: list[Message] = []

        for texto in mensajes_usuario:
            documentos = self.indice.buscar(texto, self.k)
            sistema = prompt_sistema(cliente, formatear_documentos(documentos))
            historial.append({"role": "user", "content": texto})
            inicio_registro = len(herramientas.registro)

            respuesta = ""
            for _ in range(self.max_pasos):
                mensajes = [{"role": "system", "content": sistema}, *historial]
                salida = self.llm.generate(mensajes, ESQUEMAS, seed=seed)
                respuesta = salida.content
                if not salida.tool_calls:
                    break
                historial.append(
                    {
                        "role": "assistant",
                        "content": salida.content,
                        "tool_calls": [
                            {"function": {"name": c.name, "arguments": c.arguments}}
                            for c in salida.tool_calls
                        ],
                    }
                )
                for c in salida.tool_calls:
                    resultado = herramientas.ejecutar(c.name, c.arguments)
                    historial.append({"role": "tool", "content": resultado, "tool_name": c.name})
            historial.append({"role": "assistant", "content": respuesta})

            conversacion.turnos.append(
                Turno(
                    usuario=texto,
                    respuesta=respuesta,
                    documentos=[d.id for d in documentos],
                    llamadas=herramientas.registro[inicio_registro:],
                )
            )
        return conversacion
