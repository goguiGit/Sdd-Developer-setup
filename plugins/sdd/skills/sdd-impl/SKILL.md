---
name: sdd-impl
description: Implementa un delta aprobado con TDD, requisito a requisito, con el spec.md en solo lectura. Usar cuando el delta está en approved ("implementa el PBI 1234", "/sdd-impl").
argument-hint: [<id> | ruta al delta.md]
---

Implementa el cambio descrito en un delta. El spec es solo lectura: el único fichero de documentación que tocas es el propio delta (su `## Plan` y su `status`).

## Antes de escribir código

1. Localiza el delta: por `$ARGUMENTS` (id o ruta) o, si no hay, el único `docs/features/*/changes/*/delta.md` de la rama actual. Si hay varios, pregunta cuál.
2. Lee el frontmatter. Si `status` no es `approved`, **para** y dile al usuario que el delta no está aprobado; no implementes nada. Si es `implemented`, avisa de que ya se hizo.
3. Ejecuta `python ${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py check <delta>`. Si falla, el delta no encaja con el spec: arréglalo primero con el usuario, no sigas.
4. Lee `spec.md` de la feature para conocer los requisitos vecinos que no deben romperse.

## Cómo implementas

Un requisito cada vez, en el orden de `## Plan`:

1. **Rojo**: escribe el test que demuestra el `GIVEN / WHEN / THEN` del requisito, con el id en el nombre o en un comentario de una línea (`// REQ-REG-004`), y ejecútalo: debe fallar por el motivo correcto.
2. **Verde**: el código mínimo que lo hace pasar.
3. **Refactor** con la suite en verde.
4. Marca la casilla del plan y haz commit: `feat: <qué> (REQ-REG-004)` con el trailer `Refs: PBI-<id>`. Un requisito por commit es lo normal; dos si son inseparables.

Para `REMOVED`: borra el comportamiento y su test, en su propio commit. Para `MODIFIED`: primero cambia el test al nuevo GIVEN/WHEN/THEN, mira cómo falla, luego el código.

No implementes nada que no esté en el delta. Si al implementar descubres que falta un requisito o uno está mal, no lo cueles: dile al usuario y propón ampliar el delta (vuelve a `draft`, cambia, vuelve a aprobar).

## Al terminar

1. Suite completa del proyecto en verde (el comando que use el repo, no solo tus tests).
2. Comprueba que cada REQ de `ADDED` y `MODIFIED` tiene al menos un test que lo nombra y que ningún test nombra un REQ de `REMOVED`. Si falta algo, no has terminado.
3. Cambia `status: approved` por `status: implemented` en el delta y haz commit `docs: PBI <id> implementado`.
4. Resume al usuario: requisitos implementados, tests añadidos, y que el siguiente paso es la PR; al mergearla, `/sdd-merge` (o el workflow de CI) fusiona el delta en el spec y lo archiva.
