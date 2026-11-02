# <Nombre del repo>

<Una o dos frases: qué es este sistema y con qué se integra.>

## Empezar

Lee este fichero una vez por tarea. Para saber qué funcionalidades y requisitos existen, `docs/features/INDEX.md` y `docs/features/REQ-INDEX.md` (generados; no leas todos los specs). Después inspecciona la implementación, sus llamadores y sus tests. Una petición clara de implementación autoriza cambios locales, tests y documentación; no autoriza desplegar, tocar datos de producción ni llamar a sistemas externos.

## Spec-Driven Development

Las especificaciones viven en `docs/features/<feature>/spec.md` (requisitos `REQ-<AREA>-NNN` en GIVEN/WHEN/THEN) y cada cambio que añade, modifica o quita un requisito en `docs/features/<feature>/changes/<id>-<slug>/delta.md`.

- Un cambio que toca requisitos empieza por su delta y no se implementa hasta que esté en `status: approved`. Un cambio que no toca requisitos (bug dentro de un REQ, refactor) se implementa directamente citando el REQ.
- El `spec.md` solo lo modifica la fusión del delta, al cerrar.
- Cada commit de implementación nombra su requisito (`feat: … (REQ-AREA-NNN)`) y lleva `Refs: PBI-<id>`.
- Skill: `sdd` (`/sdd <id>` decide la fase por el estado del delta). CI: `sdd-checks` valida los deltas abiertos y que los índices estén al día en cada PR.
- La documentación es parte del cambio: un commit que cambia comportamiento actualiza el delta o el spec, el `README.md` afectado y este fichero si una regla deja de ser cierta. Documentación desactualizada es un bug.
- Gestor de tareas: <!-- Azure DevOps (organización, proyecto) o Jira (proyecto); MCP registrado con setup/install -Tracker. Qué tipo de work item es un PBI y cuál una tarea. -->

## Límites

<!-- 3-6 puntos: qué carpeta es dueña de qué, y qué contratos no se rompen. -->
-

## Verificar

- Build: `<comando>`
- Tests: `<comando>`
- Servicios necesarios: `<ninguno | SQL Server local | …>`
