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
| Embeddings o vector store sobre los specs | Corpus pequeño, estructurado y con ids únicos: tres índices generados (`INDEX.md`, `REQ-INDEX.md`, `CONTRACTS.md`) y `where` por id cubren la búsqueda y la trazabilidad sin LLM. Los agentes de código mayoritarios tampoco usan vectores |
| Grafo de conocimiento (Graphify) desde el principio | Aporta en preguntas de relación entre muchos repos ("qué afecta cambiar este requisito"), a cambio de otra dependencia, tokens por reconstrucción del lado de docs y un `graph.json` que mantener. Se revisa cuando haya una pregunta concreta que los índices no respondan, o más de ~200 requisitos y ~10 repos. Los `// REQ-…` en tests y `Refs:` en commits ya dejan el rastro que un grafo aprovecharía |
| MCP declarados dentro del plugin | Un `.mcp.json` en el plugin fijaría la organización de Azure DevOps o el Jira para todos. El instalador registra el MCP a nivel de usuario con la organización como parámetro |
| Avisos por Teams o Slack como parte del flujo | La PR y el ticket ya notifican. Un aviso es un paso explícito que el usuario pide con el MCP que tenga |
| Ids de modelo concretos en skills o configuración | Caducan con cada versión. Niveles con alias del host (`opus`, `sonnet`, `haiku`) en `models.md` y `sdd.json`; el agente sube o baja de nivel con criterios escritos y lo dice |
| Una skill o un modelo fijo para todo el flujo | Escribir el delta y revisar exigen razonar; implementar está acotado por tests; fusionar es ejecutar un script. Pagar el máximo en todo es caro y pagar el mínimo en el delta es peligroso |
| Reglas de estilo por lenguaje dentro del plugin | Cambian por repo y las aplica el formateador. El plugin solo lleva `principles.md`, lo que vale en cualquier lenguaje, cada principio con su señal de ruptura; las convenciones del flujo (ids, carpetas, ramas, commits, tests) en `format.md` |
| Auto-merge de los cambios de autoservicio | Nada llega a `main` sin una PR revisada por una persona, aunque sea de Producto y el cambio sea un texto. Lo que se ahorra es el tiempo del developer, no la revisión: el autoservicio cambia quién revisa, no si se revisa |
| Agentes propios del plugin | Los agentes genéricos (`researcher`, `implementer`, `reviewer`, `tester`) son del setup personal del developer; el plugin solo aporta la skill y el script |
