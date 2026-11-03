# Sdd-Developer-setup

Marketplace de Claude Code con dos plugins: `sdd` (Spec-Driven Development mínimo: un `spec.md` por feature, un `delta.md` por cambio, las skills `/sdd`, `/sdd-models` y `/sdd-languages`, paquetes de lenguaje y un script) y `libraries` (catálogo de skills de uso de librerías por stack). Este fichero es para el agente; las personas leen `README.md` (uso), `docs/IMPLEMENTACION.md` (cómo está hecho), `docs/SKILLS.md` (definición de cada skill) y `docs/decisiones.md` (qué se dejó fuera y por qué).

## Documentación: parte del cambio, no un paso aparte

- Cada cambio actualiza en el **mismo commit** lo que afecte de `README.md` (si cambia lo que ve el usuario), `docs/IMPLEMENTACION.md` (si cambia cómo funciona), `docs/SKILLS.md` (si cambia una skill), `docs/decisiones.md` (si se descarta o adopta algo), `examples/happy-path/` (si cambia el flujo) y este fichero (si una regla deja de ser cierta). Una PR que cambia comportamiento sin tocar documentación está incompleta.
- Antes de dar por terminado: releer la sección de documentación afectada como si fueras un developer nuevo, y comprobar que los ejemplos de comandos siguen siendo exactos (nombres de parámetros, rutas, salidas).
- `docs/features/registro-usuario/` y sus índices son ejemplo **y** fixture del CI: `sdd.py scan docs` e `index --check` deben dar `ok`. Si cambia el formato, actualizar ejemplo, índices (`sdd.py index docs`) y `format.md` a la vez.
- Documentación en español; nombres de ficheros, skills, comandos y código en inglés. Sin comentarios en el código: el nombre tiene que bastar; los porqués van en `docs/`.

## Estructura y dónde se cambia cada cosa

| Quiero | Toco |
|---|---|
| El flujo o las fases | `plugins/sdd/skills/sdd/SKILL.md` (la skill del flujo; la fase la decide el `status` del delta; la revisión es un tramo que solo corre si se pide; no partirla en una skill por fase). Las otras dos skills son `sdd-models` y `sdd-languages`, porque "configurar" es otro disparador; no añadir más sin un disparador nuevo |
| El formato de `spec.md`/`delta.md` o lo que se valida | `plugins/sdd/scripts/sdd.py` **primero con un test** en `scripts/tests/` (`test_rules.py` para reglas), luego `references/format.md`, el ejemplo y sus índices |
| Un paquete de lenguaje de primera (C#, TypeScript, Python) | `plugins/sdd/skills/sdd/references/languages/<lang>.md`; frontmatter con `owner`, `extensions`, `skipDirs` (el script los lee) y el resto para la skill. La plantilla para los repos es `plugins/sdd/templates/language.md`. Otro lenguaje de primera solo si este repo puede mantenerlo; si no, va al repo del producto con `owner` |
| Qué se hace con Azure DevOps o Jira | `plugins/sdd/skills/sdd/references/trackers.md` y la rama `-Tracker` de los dos instaladores |
| Cómo se revisa un cambio | `plugins/sdd/skills/sdd/references/review-checklist.md` (ocho filas) |
| Qué modelo en cada fase, `sdd.json` | `plugins/sdd/skills/sdd/references/models.md`, `plugins/sdd/templates/sdd.json` (única plantilla; el instalador copia esa) y la skill `skills/sdd-models/`; solo alias de nivel, nunca ids con fecha |
| Principios de ingeniería independientes del lenguaje | `plugins/sdd/skills/sdd/references/principles.md` (principio + señal de ruptura, sin nombres de librerías); lo que depende del lenguaje va a su paquete; el estilo del repo a su `AGENTS.md` |
| Quién puede pedir, quién aprueba, qué es autoservicio | `README.md` ("Quién hace qué", "Si no eres developer"), la tabla de niveles de `SKILL.md`, `approved_by` en `format.md` y la clave `selfService` de `sdd.json` |
| El ejemplo narrado | `examples/happy-path/README.md` y su `sdd.json`; si cambia el flujo, cambia el ejemplo en el mismo commit |
| La definición de una skill (qué hace, cuándo, modelo) | `docs/SKILLS.md`, en el mismo commit que la skill. Ninguna skill fija `model` en el frontmatter; el nivel por fase va en `sdd.json` del repo del producto |
| Una skill de librería nueva | `plugins/libraries/skills/<area>-<libreria>/SKILL.md` (30-60 líneas, descripción con las frases de uso; el stack delante si hay varias); modelo: `masstransit-saga`. Nunca reglas SDD ahí |
| Lo que valida el CI de los consumidores | `.github/workflows/sdd-checks.yml`, job `deltas` (`scan` + `index --check` + aviso de autoservicio en PRs etiquetadas); `script-tests` solo corre en este repo (`if: github.repository == …`) |
| Lo que recibe un repo nuevo | `templates/AGENTS.md` (real, con la sección "Reglas del lenguaje"), `templates/CLAUDE.md` (solo `@AGENTS.md`, así lo leen Claude Code, Codex y Copilot) y `plugins/sdd/templates/sdd.json` |
| Instalación o actualización | `setup/install.ps1` / `install.sh` y `setup/update.ps1` / `update.sh` (idempotentes; `.ps1` con BOM UTF-8, `.sh` en LF) |

## Reglas que no se deducen del código

- Este repo **es** el marketplace: `.claude-plugin/marketplace.json` lista los plugins de `plugins/`. La versión de cada plugin vive en su `plugin.json` y en su entrada del marketplace y deben coincidir; subirla en los dos, mergear a `main` y etiquetar `v<versión del plugin sdd>` es publicar (la tarea diaria de cada developer la recoge; los consumidores pueden fijar el CI a la etiqueta). `MAJOR` si cambia el formato de `spec.md`/`delta.md`, `MINOR` si cambia una skill, se añade una o se añade un paquete de lenguaje, `PATCH` texto o script sin cambio de formato.
- `sdd.py` es stdlib puro, a propósito: CI lo ejecuta con `actions/setup-python` y las skills con el Python del developer (`python3`; `python` en Windows). Tests: `python -I -m unittest discover -s plugins/sdd/scripts/tests` (52). Subcomandos: `lint`, `check`, `merge`, `scan`, `index [--check]`, `where`, `coverage`, `selfservice` (rutas por stdin), `settings`. De `sdd.json` el script solo lee `selfService` y `languages`.
- Los índices (`INDEX.md`, `REQ-INDEX.md`, `CONTRACTS.md` en `docs/features/`) son generados y deterministas; no se editan. Todo commit que toque `docs/features/` los regenera; `index --check` en CI impide que queden viejos. `REQ-INDEX.md` no lleva recuentos de ficheros a propósito (cambiarían con cada commit de código); eso lo responde `coverage`.
- Un requisito es un bloque desde su `### REQ-…` hasta el siguiente `###` o `##` (`split_requirements`); la primera versión se tragaba `## Decisiones`. Las líneas `Publica:` / `Consume:` dentro del bloque alimentan `CONTRACTS.md`. Se lee con `utf-8-sig` (BOM de editores Windows) y se escribe sin BOM.
- `approved_by` es obligatorio fuera de `draft` y lo escribe una persona: la skill tiene prohibido escribir `approved` o `approved_by`, y `lint` lo exige. La etiqueta `self-service` también la pone una persona; el agente solo dice si procede y `selfservice` lo comprueba.
- Paquetes de lenguaje: el script resuelve `docs/sdd/languages/<lang>.md` del repo antes que `references/languages/<lang>.md` del plugin, y `scan` falla si un paquete activo no existe o no tiene `owner`. Sin `languages`, `default_settings()` usa una lista amplia de extensiones y carpetas.
- La skill no nombra herramientas concretas del host ni de los MCP: describe operaciones. La única dependencia es `${CLAUDE_PLUGIN_ROOT}` para localizar el script y `templates/`.
- Frontmatter de las skills: `description` como bloque plegado (`>-`) y `argument-hint` entre comillas; un `:` suelto en una descripción en línea rompe el YAML y Claude carga la skill sin metadatos (lo detecta `claude plugin validate plugins/<plugin>`, no el de la raíz). Cada `plugin.json` lleva `license` y el repo un `LICENSE` (MIT).
- Tarea diaria de actualización: Windows Task Scheduler (`Claude sdd plugin update`, con la ruta completa del shell), macOS LaunchAgent (`com.sdd.plugin-update`, sin probar en un Mac real), Linux crontab (`# claude-sdd-plugin-update`). `update.*` actualiza el marketplace y **todos** los plugins instalados desde él y escribe `~/.claude/sdd-update.log`.
- Grafo de conocimiento (Graphify) y vector stores: descartados por ahora con criterio escrito en `docs/decisiones.md`; no añadirlos sin una pregunta concreta que los índices y `where` no respondan.

## Verificar antes de commitear

```
python -I -m unittest discover -s plugins/sdd/scripts/tests
python -I plugins/sdd/scripts/sdd.py scan docs
python -I plugins/sdd/scripts/sdd.py index docs --check
claude plugin validate plugins/sdd
claude plugin validate plugins/libraries
bash -n setup/install.sh setup/update.sh
```

Commits convencionales (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). Autor: la identidad personal de `git config --local`. No force push.
