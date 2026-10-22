from redteam.config import cargar_config
from redteam.llm import CachedLLM, build_llm
from redteam.llm.ollama import OllamaLLM


def test_config_tiene_lo_necesario_para_ser_reproducible():
    config = cargar_config()

    assert config["modelo"] in config["modelos"]
    assert len(config["modelos"]) >= 2
    assert config["generacion"]["semillas"]
    assert isinstance(config["generacion"]["temperatura"], float)
    # Todas las defensas empiezan desactivadas: la referencia es "sin defensas".
    assert not any(config["defensas"].values())


def test_build_llm_respeta_la_config():
    config = cargar_config()

    llm = build_llm(config, "qwen3.5")

    assert isinstance(llm, CachedLLM)
    assert isinstance(llm.llm, OllamaLLM)
    assert llm.name == "qwen3.5"
    assert llm.params()["think"] is False


def test_build_llm_sin_cache():
    config = cargar_config()
    config["cache"]["activa"] = False

    assert isinstance(build_llm(config), OllamaLLM)
