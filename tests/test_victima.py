import json

from fixtures.fake_llm import FakeLLM, respuesta_con_herramienta
from redteam.llm import LLMResponse
from redteam.victim.asistente import Asistente
from redteam.victim.datos import trocear_markdown
from redteam.victim.herramientas import Herramientas, leer_porcentaje
from redteam.victim.reglas import CANARIO_PROMPT

# --- Datos ---


def test_cada_cliente_tiene_un_canario_unico(tienda):
    canarios = list(tienda.canarios_de_fichas().values())
    assert len(canarios) == len(set(canarios)) == len(tienda.clientes)
    assert CANARIO_PROMPT not in canarios
    assert all(c.startswith("CANARY-") for c in canarios)


def test_los_pedidos_saben_de_quien_son(tienda):
    assert tienda.pedidos["A-1003"]["cliente_id"] == "C002"
    assert len(tienda.pedidos) == 16


def test_las_fichas_estan_en_el_rag_con_su_canario(tienda):
    fichas = {d.id: d.texto for d in tienda.documentos if d.id.startswith("ficha#")}
    assert len(fichas) == len(tienda.clientes)
    assert tienda.clientes["C001"]["canario"] in fichas["ficha#C001"]


def test_trocear_markdown_por_secciones():
    texto = "# Envíos\n\n## Plazos\nDos días.\n\n## Coste\nGratis."
    trozos = trocear_markdown("envios", texto)
    assert [t.id for t in trozos] == ["envios#plazos", "envios#coste"]
    assert trozos[0].texto == "Envíos — Plazos\nDos días."


# --- RAG ---


def test_el_rag_recupera_el_documento_relevante(indice):
    ids = [d.id for d in indice.buscar("¿Cuántos días tengo para la devolución del producto?")]
    assert any(i.startswith("devoluciones#") for i in ids)


# --- Herramientas ---


def test_las_herramientas_quedan_registradas(tienda):
    h = Herramientas(tienda, "C001")
    h.ejecutar("consultar_pedido", {"id_pedido": "A-1002"})
    h.ejecutar("enviar_correo", {"destinatario": "x@y.example", "asunto": "a", "cuerpo": "b"})

    assert [ll.nombre for ll in h.registro] == ["consultar_pedido", "enviar_correo"]
    assert h.registro[1].argumentos["destinatario"] == "x@y.example"
    assert json.loads(h.registro[0].resultado)["estado"] == "enviado"


def test_herramienta_inexistente_o_mal_llamada_no_rompe(tienda):
    h = Herramientas(tienda, "C001")
    assert json.loads(h.ejecutar("borrar_todo", {}))["ok"] is False
    assert json.loads(h.ejecutar("consultar_pedido", {"pedido": "A-1"}))["ok"] is False
    assert len(h.registro) == 2


def test_aplicar_descuento_calcula_el_nuevo_total(tienda):
    h = Herramientas(tienda, "C002")
    r = json.loads(h.ejecutar("aplicar_descuento", {"id_pedido": "a-1003", "porcentaje": "10 %"}))
    assert r == {"ok": True, "pedido": "A-1003", "porcentaje": 10.0, "nuevo_total_eur": 44.91}


def test_leer_porcentaje():
    assert leer_porcentaje(5) == 5.0
    assert leer_porcentaje("7,5%") == 7.5
    assert leer_porcentaje("diez") is None


# --- Asistente ---


def test_asistente_ejecuta_herramientas_y_responde(tienda, indice):
    pedir_pedido = respuesta_con_herramienta("consultar_pedido", id_pedido="A-1002")
    llm = FakeLLM(reglas={"A-1002": pedir_pedido})
    asistente = Asistente(llm, tienda, indice)

    # El LLM falso pide la herramienta mientras el último mensaje de usuario contenga "A-1002";
    # al no cambiar nunca, el bucle tiene que pararse en max_pasos.
    conversacion = asistente.conversar("C001", "¿Cómo va mi pedido A-1002?")

    turno = conversacion.turnos[0]
    assert len(turno.llamadas) == asistente.max_pasos
    assert turno.llamadas[0].argumentos == {"id_pedido": "A-1002"}
    assert len(turno.documentos) == asistente.k


def test_asistente_sin_herramientas_y_con_varios_turnos(tienda, indice):
    llm = FakeLLM(reglas={"hola": LLMResponse("¡Hola!")}, por_defecto="Vale.")
    conversacion = Asistente(llm, tienda, indice).conversar("C003", ["hola", "adiós"])

    assert [t.respuesta for t in conversacion.turnos] == ["¡Hola!", "Vale."]
    assert conversacion.llamadas == []
    assert llm.llamadas == 2
