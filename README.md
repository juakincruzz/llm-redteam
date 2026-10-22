# LLM-RedTeam

Laboratorio de ataques y defensas para aplicaciones con LLM: una aplicación víctima ficticia,
una batería de ataques por categorías, defensas activables y una evaluación que mide cuánto
reduce cada defensa el éxito de los ataques y cuánto le cuesta al uso normal.

> En construcción. Los resultados se añadirán cuando salgan de `reports/`.

## Puesta en marcha

```bash
make install   # crea .venv e instala el proyecto
make test      # tests con un LLM falso (no hace falta Ollama)
make lint
```

Modelos locales con [Ollama](https://ollama.com): `llama3.1:8b`, `qwen3.5` y `mistral`.
