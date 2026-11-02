# Catálogo de skills

Qué skills reparte este marketplace, cuándo se activan, qué hacen y qué no, y con qué modelo. Es la definición de referencia: si una skill cambia, cambia esta página en el mismo commit.

Una skill es una carpeta con un `SKILL.md`: un frontmatter (nombre, descripción, pista de argumentos y, si hace falta, modelo) y las instrucciones que el agente sigue cuando la skill se activa. Se activa de dos formas: la persona la invoca (`/sdd 1234`) o el agente la elige porque lo que le piden encaja con la **descripción**; por eso la descripción lleva las frases con las que alguien pediría ese trabajo.

## Plugin `sdd`

| Skill | Cuándo se activa | Qué hace | Qué no hace | Modelo |
|---|---|---|---|---|
| **`/sdd <id> [descripción]`** | "trabaja el PBI 1234", "implementa el 1234", "cierra el 1234", o la invocación directa | Lee los índices, localiza el delta del id y actúa según su `status`: sin delta lo crea (y clasifica el nivel de intervención: 0 autoservicio, 1 developer aprueba, 2 riesgo); `draft` se detiene; `approved` implementa con TDD requisito a requisito y crea las tareas en el gestor si `sdd.json` lo pide; `implemented` fusiona en el spec, regenera los índices y archiva | No escribe código antes de la aprobación; no toca `spec.md` salvo al fusionar; no cierra un ticket con la PR sin mergear; no notifica por Teams ni Slack | Por fase, según `sdd.json` → `models` (por defecto `opus` para el delta y la revisión, `sonnet` para implementar, `haiku` para fusionar); sube o baja con los criterios de `models.md` y lo dice |
| **`/sdd-models [show \| recommend \| set <fase> <alias> \| reset]`** | "qué modelo usa cada fase", "cambia el modelo de implementación", "hay modelos nuevos" | Muestra la tabla fase → alias de `sdd.json`; compara con los modelos que ofrece el host y propone cambios; escribe una fase; vuelve a los valores por defecto. Cada cambio en su commit `chore:` | No cambia el modelo de la sesión ni la configuración global de Claude Code; no toca nada fuera de `sdd.json` | El de la sesión |

Referencias que las dos skills cargan solo cuando las necesitan (`plugins/sdd/skills/sdd/references/`): `format.md` (formato de `spec.md` y `delta.md`, nombres, qué comprueba el script), `review-checklist.md` (ocho filas para revisar un cambio), `trackers.md` (qué se hace con Azure DevOps o Jira), `models.md` (niveles, criterios, `sdd.json`) y `principles.md` (principios independientes del lenguaje con su señal de ruptura).

Script que ambas usan: `plugins/sdd/scripts/sdd.py` (`lint`, `check`, `merge`, `scan`, `index`, `where`).

## Plugin `libraries` (instalación opcional)

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
