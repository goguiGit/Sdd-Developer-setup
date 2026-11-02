# Sdd-Developer-setup

Marketplace de Claude Code con dos plugins: `sdd` (Spec-Driven Development mínimo: un `spec.md` por feature, un `delta.md` por cambio, una skill `/sdd` y un script) y `libraries` (skills de uso de librerías). Este fichero es para el agente; las personas leen `README.md` (uso), `docs/IMPLEMENTACION.md` (cómo está hecho) y `docs/decisiones.md` (qué se dejó fuera y por qué).

## Documentación: parte del cambio, no un paso aparte

- Cada cambio actualiza en el **mismo commit** lo que afecte de `README.md` (si cambia lo que ve el usuario), `docs/IMPLEMENTACION.md` (si cambia cómo funciona), `docs/decisiones.md` (si se descarta o adopta algo) y este fichero (si una regla deja de ser cierta). Una PR que cambia comportamiento sin tocar documentación está incompleta.
- Antes de dar por terminado: releer la sección de documentación afectada como si fueras un developer nuevo, y comprobar que los ejemplos de comandos siguen siendo exactos (nombres de parámetros, rutas, salidas).
- `docs/features/registro-usuario/` y sus índices son ejemplo **y** fixture del CI: `sdd.py scan docs` e `index --check` deben dar `ok`. Si cambia el formato, actualizar ejemplo, índices (`sdd.py index docs`) y `format.md` a la vez.
- Documentación en español; nombres de ficheros, skills, comandos y código en inglés. Sin comentarios en el código: el nombre tiene que bastar; los porqués van en `docs/`.

## Estructura y dónde se cambia cada cosa

| Quiero | Toco |
|---|---|
| El flujo o las fases | `plugins/sdd/skills/sdd/SKILL.md` (la skill del flujo; la fase la decide el `status` del delta; no partirla en una skill por fase). La única otra skill es `sdd-models`, porque "configurar modelos" es otro disparador; no añadir más sin un disparador nuevo |
| El formato de `spec.md`/`delta.md` o lo que se valida | `plugins/sdd/scripts/sdd.py` **primero con un test** en `scripts/tests/`, luego `references/format.md`, el ejemplo y sus índices |
| Qué se hace con Azure DevOps o Jira | `plugins/sdd/skills/sdd/references/trackers.md` y la rama `-Tracker` de los dos instaladores |
| Cómo se revisa un cambio | `plugins/sdd/skills/sdd/references/review-checklist.md` |
| Qué modelo en cada fase, `sdd.json` | `plugins/sdd/skills/sdd/references/models.md`, `templates/sdd.json` y la skill `skills/sdd-models/` (única otra skill del plugin: disparador distinto, solo toca `sdd.json`); solo alias de nivel, nunca ids con fecha |
| Principios de ingeniería independientes del lenguaje | `plugins/sdd/skills/sdd/references/principles.md` (principio + señal de ruptura); las reglas y convenciones de cada lenguaje van al `AGENTS.md` del repo del producto, no aquí |
| Quién puede pedir, quién aprueba, qué es autoservicio | `README.md` ("Quién hace qué"), la sección "Nivel de intervención" de `SKILL.md` y la clave `selfService` de `sdd.json` |
| El ejemplo narrado | `examples/happy-path/README.md`; si cambia el flujo, cambia el ejemplo en el mismo commit |
| Una skill de librería nueva | `plugins/libraries/skills/<area>-<libreria>/SKILL.md` (30-60 líneas, descripción con las frases de uso); modelo: `masstransit-saga`. Nunca reglas SDD ahí |
| Lo que valida el CI de los consumidores | `.github/workflows/sdd-checks.yml`, job `deltas` (`scan` + `index --check`); `script-tests` solo corre aquí |
| Lo que recibe un repo nuevo | `templates/AGENTS.md` (real), `templates/CLAUDE.md` (solo `@AGENTS.md`, así lo leen Claude Code, Codex y Copilot) y `templates/sdd.json` |
| Instalación o actualización | `setup/install.ps1` / `install.sh` y `setup/update.ps1` / `update.sh` (idempotentes; `.ps1` con BOM UTF-8, `.sh` en LF) |

## Reglas que no se deducen del código

- Este repo **es** el marketplace: `.claude-plugin/marketplace.json` lista los plugins de `plugins/`. La versión de cada plugin vive en su `plugin.json` y en su entrada del marketplace y deben coincidir; subirla en los dos y mergear a `main` es publicar (la tarea diaria de cada developer la recoge). `MAJOR` si cambia el formato de `spec.md`/`delta.md`, `MINOR` si cambia una skill o se añade una, `PATCH` texto o script sin cambio de formato.
- `sdd.py` es stdlib puro, a propósito: CI lo ejecuta con `actions/setup-python` y las skills con el Python del developer. Tests: `python -I -m unittest discover -s plugins/sdd/scripts/tests` (28). Subcomandos: `lint`, `check`, `merge`, `scan`, `index [--check]`, `where`.
- Los índices (`INDEX.md`, `REQ-INDEX.md`, `CONTRACTS.md` en `docs/features/`) son generados y deterministas; no se editan. `merge` los regenera; `index --check` en CI impide que queden viejos. El recuento de "tests" es ficheros de código fuera de `docs/` que contienen el id (`CODE_EXTENSIONS`, sin `SKIP_DIRS`).
- Un requisito es un bloque desde su `### REQ-…` hasta el siguiente `###` o `##` (`split_requirements`); la primera versión se tragaba `## Decisiones`. Las líneas `Publica:` / `Consume:` dentro del bloque alimentan `CONTRACTS.md`.
- La skill no nombra herramientas concretas del host ni de los MCP: describe operaciones. La única dependencia es `${CLAUDE_PLUGIN_ROOT}` para localizar el script.
- Frontmatter de las skills: `description` como bloque plegado (`>-`) y `argument-hint` entre comillas; un `:` suelto en una descripción en línea rompe el YAML y Claude carga la skill sin metadatos (lo detecta `claude plugin validate plugins/<plugin>`, no el de la raíz). Cada `plugin.json` lleva `license` y el repo un `LICENSE` (MIT).
- Tarea diaria de actualización: Windows Task Scheduler (`Claude sdd plugin update`), macOS LaunchAgent (`com.sdd.plugin-update`, sin probar en un Mac real), Linux crontab (`# claude-sdd-plugin-update`). `update.*` actualiza el marketplace y **todos** los plugins instalados desde él y escribe `~/.claude/sdd-update.log`.
- Grafo de conocimiento (Graphify) y vector stores: descartados por ahora con criterio escrito en `docs/decisiones.md`; no añadirlos sin una pregunta concreta que los índices y `where` no respondan.

## Verificar antes de commitear

```
python -I -m unittest discover -s plugins/sdd/scripts/tests
python -I plugins/sdd/scripts/sdd.py scan docs
python -I plugins/sdd/scripts/sdd.py index docs --check
claude plugin validate .
bash -n setup/install.sh setup/update.sh
```

Commits convencionales (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). Autor: la identidad personal de `git config --local`. No force push.
