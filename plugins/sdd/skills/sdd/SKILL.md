---
name: sdd
description: >-
  Trabaja un cambio con Spec-Driven Development según el estado de su delta: lo crea si no existe, se detiene si está en draft, lo implementa con TDD si está approved y lo fusiona en el spec si está implemented. Usar al empezar, continuar o cerrar un PBI, bug o tarea ("trabaja el PBI 1234", "implementa el 1234", "cierra el 1234", "/sdd 1234").
argument-hint: "<id> [descripción corta] [--feature <slug>]"
---

Un `spec.md` por feature con requisitos `REQ-<AREA>-NNN` en GIVEN/WHEN/THEN; un `delta.md` por cambio. El spec solo cambia por fusión de un delta. Formatos y reglas en [references/format.md](references/format.md); el script que valida y fusiona es `${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py`. Si hay un gestor de tareas conectado por MCP (Azure DevOps, Jira), lo que se hace con él en cada fase está en [references/trackers.md](references/trackers.md). Qué nivel de modelo conviene en cada fase, y cuándo subir o bajar, en [references/models.md](references/models.md); el repo puede fijarlo en `sdd.json` (`models`, `tracker`, `createTasks`), que se lee antes de empezar, y se cambia con `/sdd-models`.

## Orientarse sin leerlo todo

Empieza por `docs/features/INDEX.md` (una línea por feature y los deltas abiertos) y `docs/features/REQ-INDEX.md` (todos los requisitos activos con su feature y cuántos tests los nombran); los genera el script, no se editan. Abre solo el `spec.md` que toque. Para seguir un requisito hasta sus deltas, tests y commits: `python ${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py where REQ-<AREA>-NNN`. Si los índices no existen o están viejos (`sdd.py index --check`), regenéralos con `sdd.py index` y añádelos al commit.

## Quién pide y cuánta intervención hace falta

Cualquier persona puede pedir un cambio, también alguien de producto, soporte o negocio sin saber de código. Escribe los requisitos para esa persona: GIVEN/WHEN/THEN en lenguaje de negocio, sin nombres de clases, tablas ni librerías (eso va en el plan, que sí es técnico). Antes de hacer nada, clasifica el cambio y dilo en una línea:

| Nivel | Cuándo | Quién interviene |
|---|---|---|
| **0, autoservicio** | No cambia ningún requisito **y** solo toca rutas de `selfService` en `sdd.json` (textos, traducciones, documentación, valores de configuración permitidos) | Nadie de desarrollo: implementas, CI en verde, PR con la etiqueta `self-service` que puede revisar cualquiera del equipo, incluida la persona que lo pidió |
| **1, cambio de requisitos** | Añade, modifica o quita requisitos sin tocar contratos entre servicios, persistencia ni autorización | Un developer aprueba el delta (diez líneas) y revisa la PR |
| **2, riesgo** | Toca `Publica:`/`Consume:`, persistencia, autorización, pagos o datos personales, o más de tres requisitos | Developer en el delta y en la PR; revisión con el nivel máximo de modelo; no hay vía rápida |

Si no puedes clasificar con seguridad, es nivel 1. Si alguien sin perfil técnico pide algo de nivel 2, no lo frenes: escribe el delta igual y explica qué developer tiene que mirarlo y por qué.

## Qué fase toca

Busca `docs/features/*/changes/<id>-*/delta.md` para el id de `$ARGUMENTS` (o el único delta de la rama actual).

| Situación | Haz |
|---|---|
| No hay delta y el cambio **añade, modifica o quita algún requisito** | Crear el delta (abajo) |
| No hay delta y **no cambia ningún requisito** (bug dentro de un REQ, refactor, deuda, texto) | Vía rápida: implementa con TDD y cita el REQ existente en cada commit. Sin delta. Si además solo toca rutas de `selfService`, es nivel 0: etiqueta la PR `self-service` y di que no necesita developer |
| `status: draft` | Para. Di qué añade, cambia y quita, y que para seguir alguien tiene que poner `status: approved` (o mergear la PR del delta, si el equipo aprueba así) |
| `status: approved` | Implementar (abajo) |
| `status: implemented` | Fusionar (abajo) |

Si dudas de si cambia un requisito, lee el `spec.md` de la feature: si la frase GIVEN/WHEN/THEN de algún REQ dejaría de ser cierta, o hace falta una nueva, es un delta.

## Crear el delta

1. Lee el ticket si hay gestor conectado (título, descripción, criterios de aceptación; ver `trackers.md`); si no, lo que cuente el usuario. Pregunta **una sola vez** lo que de verdad cambie el delta.
2. Elige la feature por `--feature` o por el título en `INDEX.md`; si no existe, crea su `spec.md` con la plantilla de `format.md`. Si un requisito publica o consume un mensaje entre servicios, dilo con `Publica:` / `Consume:` (ver `format.md`): el índice de contratos sale de ahí.
3. Escribe `docs/features/<feature>/changes/<id>-<slug>/delta.md` en `status: draft`: por qué, `ADDED` / `MODIFIED` / `REMOVED` (siempre las tres, aunque vacías), y un plan de 3 a 6 casillas con los tests que irán primero. Un requisito, una idea comprobable; en `MODIFIED` el texto completo nuevo.
4. `python ${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py lint <delta>` y `check <delta>`; arregla lo que digan.
5. Rama `feature/<id>-<slug>` (`bugfix/` si es un bug) y commit solo con el delta: `docs: delta del PBI <id>, <título>`, trailer `Refs: PBI-<id>`. Termina aquí: nada de código antes de la aprobación.

## Implementar

1. `sdd.py check <delta>` en verde; si no, el delta no encaja con el spec y se arregla antes.
2. Lee el `spec.md` para no romper requisitos vecinos. El spec es de solo lectura en esta fase. Si hay gestor conectado, crea una tarea hija por casilla del plan, enlazada al ticket, según `createTasks` de `sdd.json` (`true` sin preguntar, `false` preguntando, `"never"` nunca); cierra cada una al marcar su casilla. Implementa con el nivel de modelo de `models.md` (medio por defecto) y sube al máximo si un requisito falla sus tests dos veces; dilo en el resumen.
3. Un requisito cada vez, en el orden del plan: test que demuestra el GIVEN/WHEN/THEN con el id en el nombre o en una línea, verlo fallar por el motivo correcto, código mínimo, refactor en verde con [references/principles.md](references/principles.md) a mano (las reglas del lenguaje y del repo están en su `AGENTS.md`), commit `feat: <qué> (REQ-AREA-NNN)` con `Refs: PBI-<id>`. `REMOVED`: borra comportamiento y test en su propio commit. `MODIFIED`: primero cambia el test, mira cómo falla, luego el código.
4. Nada fuera del delta. Si falta un requisito o uno está mal, no lo cueles: propón ampliar el delta (vuelve a `draft`, se cambia, se aprueba).
5. Al acabar: suite completa en verde; cada REQ de `ADDED`/`MODIFIED` tiene un test que lo nombra y ninguno nombra un `REMOVED` ([review-checklist.md](references/review-checklist.md)); marca el plan, pon `status: implemented` y commit `docs: PBI <id> implementado`. El siguiente paso es la PR.

## Fusionar

Después de mergear la PR del cambio.

1. `python ${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py merge <delta>`: valida, aplica `ADDED`/`MODIFIED`/`REMOVED` al spec, añade la fila al historial, mueve la carpeta a `changes/archive/<fecha>-<id>-<slug>/` y regenera los índices. Rechaza un `draft`; con un `approved` sin implementar, pregunta antes.
2. Lee el spec resultante: numeración coherente, sin duplicados, decisiones todavía ciertas; si un `REMOVED` deja una decisión obsoleta, actualízala.
3. Commit con el spec, la carpeta archivada y los índices: `docs: fusiona el PBI <id> en el spec de <feature>`, trailer `Refs: PBI-<id>`. Si el usuario lo pide y hay gestor conectado, copia los GIVEN/WHEN/THEN a los criterios de aceptación del ticket y ciérralo; solo con la PR ya mergeada.
