# <Nombre del repo>

<Una o dos frases: qué es este sistema y con qué se integra.>

## Empezar

Lee este fichero una vez por tarea; después inspecciona la implementación, sus llamadores y sus tests. Una petición clara de implementación autoriza cambios locales, tests y documentación; no autoriza desplegar, tocar datos de producción ni llamar a sistemas externos.

## Spec-Driven Development

Las especificaciones viven en `docs/features/<feature>/spec.md` (requisitos `REQ-<AREA>-NNN` en GIVEN/WHEN/THEN) y cada cambio que añade, modifica o quita un requisito en `docs/features/<feature>/changes/<id>-<slug>/delta.md`.

- Un cambio que toca requisitos empieza por su delta y no se implementa hasta que esté en `status: approved`. Un cambio que no toca requisitos (bug dentro de un REQ, refactor) se implementa directamente citando el REQ.
- El `spec.md` solo lo modifica la fusión del delta, al cerrar.
- Cada commit de implementación nombra su requisito (`feat: … (REQ-AREA-NNN)`) y lleva `Refs: PBI-<id>`.
- Skill: `sdd` (`/sdd <id>` decide la fase por el estado del delta). CI: `sdd-checks` valida los deltas abiertos en cada PR.
- Gestor de tareas: <!-- Azure DevOps (organización, proyecto) o Jira (proyecto); MCP registrado con setup/install -Tracker. Qué tipo de work item es un PBI y cuál una tarea. -->

## Límites

<!-- 3-6 puntos: qué carpeta es dueña de qué, y qué contratos no se rompen. -->
-

## Verificar

- Build: `<comando>`
- Tests: `<comando>`
- Servicios necesarios: `<ninguno | SQL Server local | …>`
