---
name: sdd-change
description: Crea el delta.md de un cambio a partir de un work item o de una descripción, en la carpeta de su feature, y la rama de trabajo. Usar al empezar un PBI, bug o tarea, antes de tocar código ("empieza el PBI 1234", "crea el delta de", "/sdd-change").
argument-hint: <id> <descripción corta> [--feature <slug>]
---

Crea el delta de un cambio. No escribas código de producción en esta skill: termina cuando el delta está en `draft` y la rama creada.

## Qué necesitas saber antes de escribir

1. **El id y el título.** Vienen en `$ARGUMENTS` o te los da el usuario. Si hay un work item en Azure DevOps y tienes acceso (MCP de Azure DevOps o `az boards work-item show --id <id>`), lee título, descripción y criterios de aceptación. Si no, trabaja con lo que te cuente el usuario y pregúntale **una sola vez** lo que de verdad cambie el delta.
2. **La feature.** Lista `docs/features/*/spec.md`. Si `--feature` no viene, elige por el título y confírmalo con el usuario si hay duda. Si no existe ninguna feature adecuada, crea `docs/features/<slug>/spec.md` desde la plantilla (`${CLAUDE_PLUGIN_ROOT}/../../templates/spec.md` en este repo, o `templates/spec.md` del plugin) con el frontmatter y los REQ que ya se cumplen hoy, si los conoces; si no, con la sección `## Requisitos` vacía.
3. **El spec actual.** Lee `spec.md` entero. Los REQ existentes son lo único que puedes poner en `MODIFIED` y `REMOVED`; los nuevos van en `ADDED` con el siguiente número libre del área (`REQ-<AREA>-NNN`, tres dígitos).

## Qué escribes

`docs/features/<feature>/changes/<id>-<slug>/delta.md`, copiando `templates/delta.md`:

- Frontmatter: `pbi`, `title`, `feature`, `status: draft`.
- `## Por qué`: dos o tres frases con el problema y el impacto. Si el work item tiene causa raíz (bug), aquí.
- `## ADDED`, `## MODIFIED`, `## REMOVED`: siempre las tres secciones, aunque alguna quede vacía. Cada requisito es `### REQ-<AREA>-NNN <título>` seguido de `GIVEN` / `WHEN` / `THEN`, una idea por requisito, comprobable con un test. En `MODIFIED` va el texto **completo** nuevo del requisito, no la diferencia. En `REMOVED`, solo la lista `- REQ-...`.
- `## Plan`: de 3 a 6 casillas con los tests que vas a escribir primero y los ficheros que tocarán, nada genérico.

## Antes de terminar

1. Ejecuta `python ${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py lint <ruta al delta>` y después `check`. Arregla lo que digan.
2. Crea la rama `feature/<id>-<slug>` (o `bugfix/<id>-<slug>` si es un bug) desde la rama principal actualizada, y haz un commit solo con el delta: `docs: delta del PBI <id>, <título>` con el trailer `Refs: PBI-<id>`.
3. Dile al usuario que el delta está en `draft`, qué requisitos añade, cambia y quita, y que para aprobarlo hay que cambiar `status` a `approved` (o abrir la PR del delta, si el equipo aprueba así). Hasta entonces, `/sdd-impl` se negará a implementar.
