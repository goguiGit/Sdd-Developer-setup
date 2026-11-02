# Decisiones

Qué se dejó fuera del flujo y por qué, frente a un setup corporativo de referencia (8 skills de SDD, 7 artefactos por cambio, ~12.000 líneas de instalador) y a [agent-kit](https://github.com/devtuc/agent-kit) (una skill de 38 líneas, tres capas sin duplicar).

| Fuera | Por qué |
|---|---|
| `mission.md`, `roadmap.md`, `proposal.md`, `design.md`, `spec-index.md` | Se solapan entre sí y con el work item. El "por qué" cabe en el delta; el diseño, si hace falta, es un bloque Mermaid dentro del delta |
| `plan.md` separado | Era una plantilla fija de cinco pasos TDD. El plan real son las casillas del delta |
| Una skill por fase (`change`, `impl`, `merge`, `trace`…) | Un solo disparador: "trabajo en el PBI". La fase la decide el `status` del delta. Es la regla de agent-kit: una skill por disparador real |
| Skill de trazado REQ ↔ diff | Una tabla de revisión de siete filas que el revisor aplica al diff |
| Delta obligatorio para todo | Vía rápida: sin cambio de requisitos no hay delta. Evita deltas vacíos por ceremonia |
| Modos de archivado "solo docs" y "solo cierre" | Un solo momento: tras el merge |
| Sincronización de ficheros entre repos | El plugin se instala, el workflow se referencia por `uses:`. Cada repo solo tiene su `docs/` y su `AGENTS.md` |
| Instaladores de cientos de líneas, recibo, worktree pinneado, hooks de deriva | Lo hace `claude plugin`, y una tarea diaria del sistema lo mantiene al día |
| Aprobación como campo editable sin control | Si importa, el delta va en su PR y CODEOWNERS decide |
| Checks en modo aviso | `enforce: true` por defecto; un aviso que no bloquea no cambia hábitos |
| Beads u otro gestor de estado | El estado durable es el `status` del delta y el historial del spec |
| MCP declarados dentro del plugin | Un `.mcp.json` en el plugin fijaría la organización de Azure DevOps o el Jira para todos. El instalador registra el MCP a nivel de usuario con la organización como parámetro |
| Avisos por Teams o Slack como parte del flujo | La PR y el ticket ya notifican. Un aviso es un paso explícito que el usuario pide con el MCP que tenga |
| Agentes propios del plugin | Los agentes genéricos (`researcher`, `implementer`, `reviewer`, `tester`) son del setup personal del developer; el plugin solo aporta la skill y el script |
