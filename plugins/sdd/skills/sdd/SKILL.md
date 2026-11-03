---
name: sdd
description: >-
  Trabaja un cambio con Spec-Driven Development según el estado de su delta: lo crea si no existe, se detiene si está en draft, lo implementa con TDD si está approved y lo fusiona en el spec si está implemented. Usar al empezar, continuar o cerrar un PBI, bug o tarea ("trabaja el PBI 1234", "implementa el 1234", "cierra el 1234", "revisa el 1234", "/sdd 1234").
argument-hint: "<id> [descripción corta] [--feature <slug>]"
---

Un `spec.md` por feature con requisitos `REQ-<AREA>-NNN` en GIVEN/WHEN/THEN; un `delta.md` por cambio. El spec solo cambia por fusión de un delta. Formatos y reglas en [references/format.md](references/format.md); el script que valida y fusiona es `${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py` (se invoca con `python3`; en Windows, `python`). Si hay un gestor de tareas conectado por MCP (Azure DevOps, Jira), lo que se hace con él en cada fase está en [references/trackers.md](references/trackers.md). Qué nivel de modelo conviene en cada fase, en [references/models.md](references/models.md). El repo fija todo eso en `sdd.json` (`models`, `tracker`, `createTasks`, `selfService`, `languages`), que se lee antes de empezar y se cambia con `/sdd-models` y `/sdd-languages`.

## Orientarse sin leerlo todo

Empieza por `docs/features/INDEX.md` (una línea por feature y los deltas abiertos) y `docs/features/REQ-INDEX.md` (todos los requisitos activos con su feature); los genera el script, no se editan. Abre solo el `spec.md` que toque. Para seguir un requisito hasta sus deltas, ficheros y commits: `sdd.py where REQ-<AREA>-NNN`; para ver qué requisitos no nombra ningún fichero de código: `sdd.py coverage`. **Todo commit que toque `docs/features/` lleva los índices regenerados** (`sdd.py index`); CI lo comprueba con `index --check`.

Reglas del lenguaje: `sdd.json` → `languages` dice qué paquetes están activos (`csharp`, `typescript` y `python` vienen en `references/languages/`; cualquier otro, en `docs/sdd/languages/` del repo). Antes de implementar lee el paquete del lenguaje que vas a tocar: cómo se cita un requisito en un test, comandos de build y tests, trampas. Sin paquete activo manda el `AGENTS.md` del repo y propones `/sdd-languages use <lang>`.

## Quién pide y cuánta intervención hace falta

Cualquier persona puede pedir un cambio, también alguien de producto, soporte o negocio sin saber de código. Escribe los requisitos para esa persona: GIVEN/WHEN/THEN en lenguaje de negocio, sin nombres de clases, tablas ni librerías (eso va en el plan, que sí es técnico). Antes de hacer nada, clasifica el cambio y dilo en una línea:

| Nivel | Cuándo | Quién interviene |
|---|---|---|
| **0, autoservicio** | No cambia ningún requisito **y** solo toca rutas de `selfService` en `sdd.json` (textos, traducciones, documentación, valores de configuración permitidos) | Nadie de desarrollo: implementas, CI en verde, y **una persona** pone a la PR la etiqueta `self-service`, que puede revisar cualquiera del equipo, incluida quien lo pidió. Si al implementar tocas un fichero fuera de `selfService`, deja de ser nivel 0: dilo y pide revisión de un developer (`git diff --name-only main | sdd.py selfservice` lo comprueba) |
| **1, cambio de requisitos** | Añade, modifica o quita requisitos sin tocar contratos entre servicios, esquema de datos ni autorización | Un developer aprueba el delta (diez líneas) y revisa la PR |
| **2, riesgo** | Toca `Publica:`/`Consume:`, el esquema de datos (migración, tabla, columna, índice), autorización, pagos o datos personales, o más de tres requisitos | Developer en el delta y en la PR; revisión con el nivel máximo de modelo; no hay vía rápida |

Si no puedes clasificar con seguridad, es nivel 1. Si alguien sin perfil técnico pide algo de nivel 2, no lo frenes: escribe el delta igual y explica qué developer tiene que mirarlo y por qué.

## Qué fase toca

Busca `docs/features/*/changes/<id>-*/delta.md` para el id de `$ARGUMENTS` (o el único delta de la rama actual).

| Situación | Haz |
|---|---|
| No hay delta y el cambio **añade, modifica o quita algún requisito** | Crear el delta (abajo) |
| No hay delta y **no cambia ningún requisito** (bug dentro de un REQ, refactor, deuda, texto) | Vía rápida: implementa con TDD y cita el REQ existente en cada commit. Sin delta. Si además solo toca rutas de `selfService`, es nivel 0: di que la PR puede llevar la etiqueta `self-service` y no necesita developer |
| `status: draft` | Para. Di qué añade, cambia y quita, y que para seguir una persona tiene que poner `status: approved` y su nombre en `approved_by` (o mergear la PR del delta, si el equipo aprueba así). **Tú nunca escribes `approved` ni `approved_by`** |
| `status: approved` | Implementar (abajo); `lint` rechaza un `approved` sin `approved_by` |
| `status: implemented` | Fusionar (abajo) |
| `$ARGUMENTS` empieza por `review` o te piden "revisa el <id>" | Revisar (abajo) |

Si dudas de si cambia un requisito, lee el `spec.md` de la feature: si la frase GIVEN/WHEN/THEN de algún REQ dejaría de ser cierta, o hace falta una nueva, es un delta.

## Crear el delta

Fase de nivel `models.change` (máximo por defecto): es donde se decide qué se construye. Si la sesión va en otro nivel, dilo.

1. Lee el ticket si hay gestor conectado (título, descripción, criterios de aceptación; ver `trackers.md`); si no, lo que cuente el usuario. Pregunta **una sola vez** lo que de verdad cambie el delta.
2. Elige la feature por `--feature` o por el título en `INDEX.md`; si no existe, crea su `spec.md` con la plantilla de `format.md`. Si un requisito publica o consume un mensaje entre servicios, dilo con `Publica:` / `Consume:`: el índice de contratos sale de ahí.
3. Escribe `docs/features/<feature>/changes/<id>-<slug>/delta.md` en `status: draft`: por qué, `ADDED` / `MODIFIED` / `REMOVED` (siempre las tres, aunque vacías), y un plan de 3 a 6 casillas con los tests que irán primero. Un requisito, una idea comprobable; en `MODIFIED` el texto completo nuevo; en `REMOVED`, una línea `- REQ-<AREA>-NNN <título>` por requisito.
4. `sdd.py lint <delta>` y `sdd.py check <delta>`; arregla lo que digan. `sdd.py index`.
5. Rama `feature/<id>-<slug>` (`bugfix/` si es un bug) y commit solo con el delta y los índices: `docs: delta del PBI <id>, <título>`, trailer `Refs: PBI-<id>` (con Jira, `Refs: <clave>`). Termina aquí: nada de código antes de la aprobación.

## Implementar

1. `sdd.py check <delta>` en verde; si no, el delta no encaja con el spec y se arregla antes.
2. Lee el `spec.md` para no romper requisitos vecinos y el paquete de lenguaje activo. El spec es de solo lectura en esta fase. Si hay gestor conectado, crea una tarea hija por casilla del plan, enlazada al ticket, según `createTasks` de `sdd.json` (`true` sin preguntar, `false` preguntando, `"never"` nunca); cierra cada una al marcar su casilla.
3. **Delega** la implementación en un subagente con el alias de `models.impl` (`sonnet` por defecto), pasándole el delta, el spec, el paquete de lenguaje y [references/principles.md](references/principles.md); un requisito por turno, en el orden del plan. Si el host no permite elegir modelo al delegar, implementa en la sesión y di en el resumen que el nivel configurado no se aplicó. Si un requisito falla sus tests dos veces, repite ese requisito con el alias de `models.change` y dilo.
4. Por requisito: test que demuestra el GIVEN/WHEN/THEN con el id en el nombre o en una línea (como diga el paquete de lenguaje), verlo fallar por el motivo correcto, código mínimo, refactor en verde, commit `feat: <qué> (REQ-AREA-NNN)` con `Refs: PBI-<id>`. `REMOVED`: borra comportamiento y test en su propio commit. `MODIFIED`: primero cambia el test, mira cómo falla, luego el código.
5. Nada fuera del delta. Si falta un requisito o uno está mal, no lo cueles: propón ampliar el delta (vuelve a `draft`, se cambia, se aprueba).
6. Al acabar: suite completa en verde; `sdd.py coverage` no lista ningún REQ de `ADDED`/`MODIFIED` y ningún test nombra un `REMOVED`; marca el plan, pon `status: implemented`, `sdd.py index`, commit `docs: PBI <id> implementado`. El siguiente paso es la PR; nivel 0 solo si `sdd.py selfservice` no se queja de ningún fichero.

## Revisar

Solo cuando lo piden. Delega en un subagente con el alias de `models.review` (máximo por defecto) el diff de la rama contra `main`, el delta y [references/review-checklist.md](references/review-checklist.md). Devuelve hallazgos que citan la fila del checklist o el principio y su señal, no preferencias de estilo. No cambia código: lo que haya que arreglar vuelve a la fase de implementar.

## Fusionar

Después de mergear la PR del cambio. Fase de nivel `models.merge` (rápido por defecto): ejecutar el script y leer su salida.

1. `sdd.py merge <delta>`: valida, aplica `ADDED`/`MODIFIED`/`REMOVED` al spec, añade la fila al historial, mueve la carpeta a `changes/archive/<fecha>-<id>-<slug>/` y regenera los índices. Rechaza un `draft`; con un `approved` sin implementar, pregunta antes.
2. Lee el spec resultante: numeración coherente, sin duplicados, decisiones todavía ciertas; si un `REMOVED` deja una decisión obsoleta, actualízala.
3. Commit con el spec, la carpeta archivada y los índices: `docs: fusiona el PBI <id> en el spec de <feature>`, trailer `Refs: PBI-<id>`. Si el usuario lo pide y hay gestor conectado, copia los GIVEN/WHEN/THEN a los criterios de aceptación del ticket y ciérralo; solo con la PR ya mergeada.
