from fixtures.fake_llm import FakeLLM, respuesta_con_herramienta
from redteam.llm.cache import CachedLLM, cache_key

MENSAJES = [
    {"role": "system", "content": "Eres el asistente de la tienda."},
    {"role": "user", "content": "¿Dónde está mi pedido?"},
]


def test_misma_entrada_misma_respuesta_sin_llamar_al_modelo(tmp_path):
    falso = FakeLLM()
    llm = CachedLLM(falso, tmp_path)

    primera = llm.generate(MENSAJES, seed=0)
    segunda = llm.generate(MENSAJES, seed=0)

    assert primera == segunda
    assert falso.llamadas == 1
    assert (llm.fallos, llm.aciertos) == (1, 1)


def test_la_cache_sobrevive_entre_instancias(tmp_path):
    CachedLLM(FakeLLM(), tmp_path).generate(MENSAJES, seed=0)

    falso = FakeLLM(por_defecto="otra cosa")
    respuesta = CachedLLM(falso, tmp_path).generate(MENSAJES, seed=0)

    assert respuesta.content == "Respuesta de prueba."
    assert falso.llamadas == 0


def test_otra_semilla_vuelve_a_llamar_al_modelo(tmp_path):
    falso = FakeLLM()
    llm = CachedLLM(falso, tmp_path)

    llm.generate(MENSAJES, seed=0)
    llm.generate(MENSAJES, seed=1)

    assert falso.llamadas == 2


def test_la_clave_depende_de_modelo_mensajes_herramientas_y_parametros():
    base = cache_key("m", MENSAJES, None, {"temperature": 0.7}, 0)

    assert base == cache_key("m", MENSAJES, None, {"temperature": 0.7}, 0)
    assert base != cache_key("otro", MENSAJES, None, {"temperature": 0.7}, 0)
    assert base != cache_key("m", MENSAJES[:1], None, {"temperature": 0.7}, 0)
    assert base != cache_key("m", MENSAJES, [{"type": "function"}], {"temperature": 0.7}, 0)
    assert base != cache_key("m", MENSAJES, None, {"temperature": 0.0}, 0)


def test_la_cache_guarda_llamadas_a_herramientas(tmp_path):
    reglas = {"descuento": respuesta_con_herramienta("aplicar_descuento", porcentaje=50)}
    falso = FakeLLM(reglas=reglas)
    llm = CachedLLM(falso, tmp_path)
    mensajes = [{"role": "user", "content": "Quiero un descuento"}]

    llm.generate(mensajes)
    respuesta = llm.generate(mensajes)

    assert falso.llamadas == 1
    assert respuesta.tool_calls[0].name == "aplicar_descuento"
    assert respuesta.tool_calls[0].arguments == {"porcentaje": 50}
