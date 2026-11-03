---
name: python
title: Python
owner: Sdd-Developer-setup (soporte de primera)
extensions: .py
skipDirs: __pycache__, .venv, venv, .pytest_cache, .mypy_cache, .tox, build, dist
testCommand: python -m pytest
buildCommand: python -m build
reqComment: "# REQ-<AREA>-NNN"
---
# Python

Lo que cambia respecto al flujo común cuando el repo es Python. Las reglas de estilo (ruff, black, mypy) van en el `AGENTS.md` del repo.

## Cómo se cita un requisito

- En el test, el id en el nombre en `snake_case`: `test_fifth_wrong_code_discards_registration_req_reg_006`, o un comentario `# REQ-REG-006` encima de la función.
- Nombre del test: `test_<escenario>_<resultado>`; una aserción principal por test.
- Frameworks habituales: `pytest`; `unittest` si el repo no tiene dependencias (como el script de este plugin).

## Estructura habitual

```
src/<paquete>/             código
tests/                     test_*.py espejo del paquete
pyproject.toml             dependencias y configuración de herramientas
```

## Comandos

- Tests: `python -m pytest` (o `python -m unittest discover -s tests`); un fichero: `python -m pytest tests/test_x.py`.
- En macOS y Linux el ejecutable suele ser `python3`; en Windows, `python`. Los scripts del flujo se invocan con `python3` salvo en Windows.

## Trampas del lenguaje para el flujo

- Entornos virtuales (`.venv/`, `venv/`) copian paquetes completos: fuera del índice (ya en `skipDirs`).
- Un fichero guardado con BOM por un editor de Windows rompe parsers que esperan UTF-8 puro; leer con `utf-8-sig`.
- Excepciones para flujo de negocio son idiomáticas en Python (`KeyError`, `ValueError`), pero en la frontera de un servicio se traducen a resultados o códigos; no dejar que lleguen al cliente.

## Ejemplos de los principios en este lenguaje

| Principio | Señal en Python |
|---|---|
| Responsabilidad única | Un módulo `utils.py` o `helpers.py` que crece con cada PBI |
| Inversión de dependencias | `import sqlalchemy` o `requests` dentro del módulo de dominio en vez de recibir un objeto que lo haga |
| Errores explícitos | `except Exception: pass`; `assert` como validación en producción |
| Idempotencia | Un consumidor que hace `INSERT` sin `ON CONFLICT` o sin comprobar el id |
