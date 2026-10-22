VENV := .venv
PY := $(VENV)/bin/python

.PHONY: install victim attack evaluate web test lint

# Crea el entorno virtual e instala el proyecto con las dependencias de desarrollo.
install:
	python3 -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

victim:
	@echo "Pendiente: fase 2 (víctima)."

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
