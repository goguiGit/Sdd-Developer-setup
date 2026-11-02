# <Nombre del repo>

<Una frase sobre qué es este repo.>

## Spec-Driven Development

Las especificaciones viven en `docs/features/<feature>/spec.md` (requisitos `REQ-<AREA>-NNN` en GIVEN/WHEN/THEN) y cada cambio en `docs/features/<feature>/changes/<id>-<slug>/delta.md`. Reglas:

- Nada de código de producción sin un delta en `status: approved`. `/sdd-change` lo crea, una persona lo aprueba, `/sdd-impl` lo implementa con TDD, `/sdd-merge` lo fusiona en el spec al cerrar.
- El `spec.md` solo lo modifica `/sdd-merge`. Si hay que cambiar un requisito, es un delta.
- Cada commit de implementación nombra su requisito (`feat: ... (REQ-AREA-NNN)`) y lleva el trailer `Refs: PBI-<id>`.
- `python <plugin>/scripts/sdd.py scan docs` valida todos los deltas abiertos; el CI lo ejecuta en cada PR.

## Comandos

- Build: `<comando>`
- Tests: `<comando>`
