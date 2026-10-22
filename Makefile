VENV := .venv
PY := $(VENV)/bin/python

.PHONY: install victim normal attack evaluate web test lint

# Crea el entorno virtual e instala el proyecto con las dependencias de desarrollo.
install:
	python3 -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

# Chat interactivo con la víctima (p. ej.: make victim ARGS="--cliente C002 --modelo mistral").
victim:
	$(PY) -m redteam.victim $(ARGS)

# Peticiones legítimas: ¿la víctima funciona bien en su uso normal?
normal:
	$(PY) -m redteam.evaluation.uso_normal $(ARGS)

attack:
	@echo "Pendiente: fase 3 (ataques)."

evaluate:
	@echo "Pendiente: fases 3-5 (evaluación)."

web:
	@echo "Pendiente: fase 6 (panel web)."

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check src tests
	$(PY) -m ruff format --check src tests
