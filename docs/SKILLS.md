# Catálogo de skills

Qué skills reparte este marketplace, cuándo se activan, qué hacen y qué no, y con qué modelo. Es la definición de referencia: si una skill cambia, cambia esta página en el mismo commit.

Una skill es una carpeta con un `SKILL.md`: un frontmatter (nombre, descripción, pista de argumentos y, si hace falta, modelo) y las instrucciones que el agente sigue cuando la skill se activa. Se activa de dos formas: la persona la invoca (`/sdd 1234`) o el agente la elige porque lo que le piden encaja con la **descripción**; por eso la descripción lleva las frases con las que alguien pediría ese trabajo.

## Plugin `sdd`

| Skill | Cuándo se activa | Qué hace | Qué no hace | Modelo |
|---|---|---|---|---|
| **`/sdd <id> [descripción]`** | "trabaja el PBI 1234", "implementa el 1234", "revisa el 1234", "cierra el 1234", o la invocación directa | Lee los índices y `sdd.json`, localiza el delta del id y actúa según su `status`: sin delta lo crea (y clasifica el nivel de intervención: 0 autoservicio, 1 developer aprueba, 2 riesgo); `draft` se detiene hasta que una persona ponga `approved` y `approved_by`; `approved` crea las tareas en el gestor si `sdd.json` lo pide y delega la implementación TDD requisito a requisito; `implemented` fusiona en el spec, regenera los índices y archiva; `review <id>` delega la revisión del diff con el checklist y devuelve hallazgos. Regenera los índices en todo commit que toque `docs/features/` | No escribe código antes de la aprobación; nunca escribe `approved` ni `approved_by`; no toca `spec.md` salvo al fusionar; no pone la etiqueta `self-service` (la pone una persona); no cierra un ticket con la PR sin mergear; no notifica por Teams ni Slack | Por fase, según `sdd.json` → `models`: delega implementar con `impl` (`sonnet`) y revisar con `review` (`opus`); crear el delta (`change`, `opus`) y fusionar (`merge`, `haiku`) van en la sesión y dice si el nivel no coincide. Sube o baja con los criterios de `models.md` y lo dice, también cuando el host no le dejó aplicar la tabla |
| **`/sdd-models [show \| recommend \| set <fase> <alias> \| reset]`** | "qué modelo usa cada fase", "cambia el modelo de implementación", "hay modelos nuevos" | Muestra la tabla fase → alias de `sdd.json`; compara con los modelos que ofrece el host y propone cambios; escribe una fase; vuelve a los valores por defecto. Cada cambio en su commit `chore:` | No cambia el modelo de la sesión ni la configuración global de Claude Code; no toca nada fuera de `sdd.json` | El de la sesión |
| **`/sdd-languages [list \| use <lang> \| add <lang> --owner <persona> \| check]`** | "qué lenguajes soporta", "activa typescript", "añade Go", al preparar un repo o cuando `where` no encuentra los tests | Lista los paquetes de lenguaje (los tres del plugin y los del repo en `docs/sdd/languages/`) con su `owner`; activa uno en `sdd.json` → `languages` y rellena "Reglas del lenguaje" en `AGENTS.md`; crea uno nuevo desde la plantilla con el `owner` indicado; comprueba que los activos existen y tienen dueño (`sdd.py settings`) | No crea un paquete sin `--owner`; no edita los paquetes del plugin en el repo (se proponen aquí por PR); no activa lenguajes que el repo no usa | El de la sesión |

Referencias que las skills cargan solo cuando las necesitan (`plugins/sdd/skills/sdd/references/`): `format.md` (formato de `spec.md` y `delta.md`, nombres, qué comprueba el script), `review-checklist.md` (ocho filas para revisar un cambio), `trackers.md` (qué se hace con Azure DevOps o Jira), `models.md` (niveles, criterios, `sdd.json`), `principles.md` (principios independientes del lenguaje con su señal de ruptura) y `languages/<lang>.md` (paquetes de lenguaje de primera: `csharp`, `typescript`, `python`). Plantillas que copian al repo: `plugins/sdd/templates/sdd.json` y `language.md`.

Script que todas usan: `plugins/sdd/scripts/sdd.py` (`lint`, `check`, `merge`, `scan`, `index [--check]`, `where`, `coverage`, `selfservice`, `settings`); se invoca con `python3` (`python` en Windows).

## Plugin `libraries` (instalación opcional)

Catálogo de skills de uso de librerías, una por librería y stack.

| Skill | Cuándo se activa | Qué hace | Qué no hace | Modelo |
|---|---|---|---|---|
| **`masstransit-saga`** | "necesito una saga", "proceso con timeout", "state machine de MassTransit", "test harness de MassTransit", o al tocar una saga existente | Resume cómo montar y probar una saga con MassTransit 8 (forma de la máquina, `Schedule`, `Ignore`, `OnMissingInstance`, repositorio EF, transportes SQL Server, RabbitMQ y Azure Service Bus, trampas del test harness) y remite a [MassTransit.Saga.Demo](https://github.com/goguiGit/MassTransit.Saga.Demo) | No sustituye la documentación oficial ni contiene reglas del flujo SDD | El de la sesión |

Cómo se añade una skill de librería: [`IMPLEMENTACION.md`](IMPLEMENTACION.md#añadir-una-skill-de-librería).

## Cambiar el modelo

Hay dos sitios, para dos cosas distintas:

| Quiero | Dónde | Cómo |
|---|---|---|
| Que una **fase del flujo** use otro nivel (por ejemplo, implementar con el máximo en un repo delicado) | `sdd.json` del repo del producto, clave `models` | `/sdd-models set impl opus`, o editar el JSON. Vale por repo y lo ve todo el equipo |
| Que una **skill entera** corra siempre con un modelo concreto | Frontmatter del `SKILL.md`, campo `model: <alias>` (la skill de Claude Code admite `model`, `context: fork` y `agent`) | Editar la skill en este repo, subir la versión del plugin y mergear; todos lo reciben en la actualización diaria |
| El modelo de **mi sesión** | Claude Code | `/model`. No lo cambia ninguna skill |

Siempre alias de nivel (`opus`, `sonnet`, `haiku` o el que el host añada), nunca ids con fecha: cuando el proveedor publica una generación nueva, el alias ya apunta a ella y aquí no cambia nada. Ninguna skill de este marketplace fija `model` en su frontmatter a propósito: `sdd` necesita un nivel distinto por fase, y las demás trabajan bien con el modelo de la sesión. Si un equipo quiere fijarlo, es una línea en el frontmatter y una versión nueva del plugin.

## Añadir una skill

Una skill nueva solo cuando hay un **disparador distinto** de los que ya existen (agent-kit: "una skill por disparador real, no por fase"). Si lo hay: carpeta en el plugin que corresponda, `SKILL.md` con descripción que contenga las frases de uso (bloque `>-`, nunca un `:` suelto en una línea), cuerpo de 30 a 60 líneas, lo largo en `references/`, versión `MINOR` del plugin en sus dos sitios, y una fila en este catálogo.
