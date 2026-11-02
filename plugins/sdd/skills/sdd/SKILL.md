---
name: sdd
description: Trabaja un cambio con Spec-Driven Development según el estado de su delta: lo crea si no existe, se detiene si está en draft, lo implementa con TDD si está approved y lo fusiona en el spec si está implemented. Usar al empezar, continuar o cerrar un PBI, bug o tarea ("trabaja el PBI 1234", "implementa el 1234", "cierra el 1234", "/sdd 1234").
argument-hint: <id> [descripción corta] [--feature <slug>]
---

Un `spec.md` por feature con requisitos `REQ-<AREA>-NNN` en GIVEN/WHEN/THEN; un `delta.md` por cambio. El spec solo cambia por fusión de un delta. Formatos y reglas en [references/format.md](references/format.md); el script que valida y fusiona es `${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py`. Si hay un gestor de tareas conectado por MCP (Azure DevOps, Jira), lo que se hace con él en cada fase está en [references/trackers.md](references/trackers.md).

## Qué fase toca

Busca `docs/features/*/changes/<id>-*/delta.md` para el id de `$ARGUMENTS` (o el único delta de la rama actual).

| Situación | Haz |
|---|---|
| No hay delta y el cambio **añade, modifica o quita algún requisito** | Crear el delta (abajo) |
| No hay delta y **no cambia ningún requisito** (bug dentro de un REQ, refactor, deuda) | Vía rápida: implementa con TDD y cita el REQ existente en cada commit. Sin delta |
| `status: draft` | Para. Di qué añade, cambia y quita, y que para seguir alguien tiene que poner `status: approved` (o mergear la PR del delta, si el equipo aprueba así) |
| `status: approved` | Implementar (abajo) |
| `status: implemented` | Fusionar (abajo) |

Si dudas de si cambia un requisito, lee el `spec.md` de la feature: si la frase GIVEN/WHEN/THEN de algún REQ dejaría de ser cierta, o hace falta una nueva, es un delta.

## Crear el delta

1. Lee el ticket si hay gestor conectado (título, descripción, criterios de aceptación; ver `trackers.md`); si no, lo que cuente el usuario. Pregunta **una sola vez** lo que de verdad cambie el delta.
2. Elige la feature por `--feature` o por el título entre `docs/features/*/spec.md`; si no existe, crea su `spec.md` con la plantilla de `format.md`.
3. Escribe `docs/features/<feature>/changes/<id>-<slug>/delta.md` en `status: draft`: por qué, `ADDED` / `MODIFIED` / `REMOVED` (siempre las tres, aunque vacías), y un plan de 3 a 6 casillas con los tests que irán primero. Un requisito, una idea comprobable; en `MODIFIED` el texto completo nuevo.
4. `python ${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py lint <delta>` y `check <delta>`; arregla lo que digan.
5. Rama `feature/<id>-<slug>` (`bugfix/` si es un bug) y commit solo con el delta: `docs: delta del PBI <id>, <título>`, trailer `Refs: PBI-<id>`. Termina aquí: nada de código antes de la aprobación.

## Implementar

1. `sdd.py check <delta>` en verde; si no, el delta no encaja con el spec y se arregla antes.
2. Lee el `spec.md` para no romper requisitos vecinos. El spec es de solo lectura en esta fase. Si hay gestor conectado y el usuario quiere, crea una tarea hija por casilla del plan, enlazada al ticket; cierra cada una al marcar su casilla.
3. Un requisito cada vez, en el orden del plan: test que demuestra el GIVEN/WHEN/THEN con el id en el nombre o en una línea, verlo fallar por el motivo correcto, código mínimo, refactor en verde, commit `feat: <qué> (REQ-AREA-NNN)` con `Refs: PBI-<id>`. `REMOVED`: borra comportamiento y test en su propio commit. `MODIFIED`: primero cambia el test, mira cómo falla, luego el código.
4. Nada fuera del delta. Si falta un requisito o uno está mal, no lo cueles: propón ampliar el delta (vuelve a `draft`, se cambia, se aprueba).
5. Al acabar: suite completa en verde; cada REQ de `ADDED`/`MODIFIED` tiene un test que lo nombra y ninguno nombra un `REMOVED` ([review-checklist.md](references/review-checklist.md)); marca el plan, pon `status: implemented` y commit `docs: PBI <id> implementado`. El siguiente paso es la PR.

## Fusionar

Después de mergear la PR del cambio.

1. `python ${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py merge <delta>`: valida, aplica `ADDED`/`MODIFIED`/`REMOVED` al spec, añade la fila al historial y mueve la carpeta a `changes/archive/<fecha>-<id>-<slug>/`. Rechaza un `draft`; con un `approved` sin implementar, pregunta antes.
2. Lee el spec resultante: numeración coherente, sin duplicados, decisiones todavía ciertas; si un `REMOVED` deja una decisión obsoleta, actualízala.
3. Commit `docs: fusiona el PBI <id> en el spec de <feature>`, trailer `Refs: PBI-<id>`. Si el usuario lo pide y hay gestor conectado, copia los GIVEN/WHEN/THEN a los criterios de aceptación del ticket y ciérralo; solo con la PR ya mergeada.
