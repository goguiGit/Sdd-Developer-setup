# Sdd-Developer-setup

Marketplace de Claude Code con un plugin (`plugins/sdd`) que implementa un Spec-Driven Development mínimo. El `README.md` explica el ciclo y los formatos; aquí solo lo que no se deduce del código.

- Este repo **es** el marketplace: `.claude-plugin/marketplace.json` en la raíz apunta a `plugins/sdd`. La versión del plugin vive en dos sitios y deben coincidir: `plugins/sdd/.claude-plugin/plugin.json` y la entrada en `marketplace.json`. Cambiar una sin la otra rompe `claude plugin update`.
- `plugins/sdd/scripts/sdd.py` es la única lógica. Sin dependencias fuera de la stdlib, a propósito: el workflow de CI de los repos consumidores lo ejecuta con el Python de `actions/setup-python`, y las skills con el del developer. Tests: `python -I -m unittest discover -s plugins/sdd/scripts/tests`. TDD: cualquier regla nueva del formato entra primero como test.
- El bloque de un requisito en `spec.md` va desde su `### REQ-…` hasta el siguiente `### ` o el siguiente `## `. Si se cambia el formato de cabeceras, revisar `split_requirements` y sus tests, que es donde se rompió la primera vez (el último REQ se tragaba `## Decisiones`).
- Las skills referencian el script como `${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py`. Esa variable la pone Claude Code al cargar el plugin; fuera de una sesión con el plugin instalado hay que usar la ruta del repo.
- `docs/features/registro-usuario/` es un ejemplo de verdad y además fixture del CI propio (`sdd.py scan docs` tiene que dar `ok`). Si se toca, que siga pasando. Su delta está en `approved` a propósito para poder probar `merge` sin editar nada; la prueba se deshace con `git checkout docs/ && git clean -fd docs/`.
- El workflow `sdd-checks.yml` sirve para dos cosas: CI de este repo (`script-tests` + `deltas`) y `workflow_call` para los consumidores (`deltas` hace checkout de este repo para tener el script). El job `script-tests` lleva `if: github.event_name != 'workflow_call'` para no correr en los consumidores.
- Documentación en español; nombres de ficheros, skills y comandos en inglés. Sin comentarios en el código salvo el docstring de uso de `sdd.py`. CRLF por `.gitattributes`.
- Commits convencionales (`feat:`, `fix:`, `docs:`, `chore:`). Autor de este repo: la identidad personal configurada en `git config --local`.
