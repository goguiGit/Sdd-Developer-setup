---
name: sdd-merge
description: Fusiona un delta implementado en el spec.md de su feature y lo archiva en changes/archive. Usar después de mergear la PR del cambio ("archiva el PBI 1234", "fusiona el delta", "/sdd-merge").
argument-hint: [<id> | ruta al delta.md]
---

Cierra el ciclo de un cambio: el spec absorbe el delta y el delta pasa al archivo.

1. Localiza el delta como en `/sdd-impl`. Si `status` es `draft`, para: no se fusiona lo que no se aprobó. Si es `approved` pero no `implemented`, pregunta al usuario si de verdad quiere fusionar sin implementar (puede tener sentido para un cambio solo de documentación).
2. Ejecuta `python ${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py merge <delta>`. El script valida (`lint` y `check`), aplica `ADDED`, `MODIFIED` y `REMOVED` sobre `spec.md`, añade la fila al `## Historial` y mueve la carpeta del cambio a `changes/archive/<fecha>-<id>-<slug>/`. Si devuelve error, no toques el spec a mano: arregla el delta y repite.
3. Lee el `spec.md` resultante y comprueba que se lee bien: numeración de REQ sin huecos raros, ningún requisito duplicado, decisiones de diseño todavía ciertas. Si un `REMOVED` deja una decisión obsoleta, bórrala o actualízala y díselo al usuario.
4. Commit: `docs: fusiona el PBI <id> en el spec de <feature>` con el trailer `Refs: PBI-<id>`.
5. Si el work item existe en Azure DevOps y el usuario lo pide, copia los `GIVEN / WHEN / THEN` del delta a sus criterios de aceptación y ciérralo. Si no, dile al usuario qué hacer a mano.
