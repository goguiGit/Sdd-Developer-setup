# Decisiones

Qué se dejó fuera del flujo y por qué, frente a un setup corporativo de referencia (8 skills de SDD, 7 artefactos por cambio, ~12.000 líneas de instalador) y a [agent-kit](https://github.com/devtuc/agent-kit) (una skill de 38 líneas, tres capas sin duplicar).

| Fuera | Por qué |
|---|---|
| `mission.md`, `roadmap.md`, `proposal.md`, `design.md`, `spec-index.md` | Se solapan entre sí y con el work item. El "por qué" cabe en el delta; el diseño, si hace falta, es un bloque Mermaid dentro del delta |
| `plan.md` separado | Era una plantilla fija de cinco pasos TDD. El plan real son las casillas del delta |
| Una skill por fase (`change`, `impl`, `review`, `merge`, `trace`…) | Un solo disparador: "trabajo en el PBI". La fase la decide el `status` del delta; la revisión es un tramo de la misma skill que solo corre cuando se pide. Es la regla de agent-kit: una skill por disparador real |
| Skill de trazado REQ ↔ diff | Una tabla de revisión de ocho filas que el revisor aplica al diff, y `coverage` para los requisitos sin test |
| Delta obligatorio para todo | Vía rápida: sin cambio de requisitos no hay delta. Evita deltas vacíos por ceremonia |
| Modos de archivado "solo docs" y "solo cierre" | Un solo momento: tras el merge |
| Sincronización de ficheros entre repos | El plugin se instala, el workflow se referencia por `uses:`. Cada repo solo tiene su `docs/`, su `AGENTS.md` y su `sdd.json` |
| Instaladores de cientos de líneas, recibo, worktree pinneado, hooks de deriva | Lo hace `claude plugin`, y una tarea diaria del sistema lo mantiene al día |
| Aprobación como un campo que cualquiera (incluido el agente) puede cambiar | `approved_by` obligatorio fuera de `draft`, escrito por una persona; el agente tiene prohibido escribirlo. Si además importa quién, el delta va en su PR y CODEOWNERS decide |
| Checks en modo aviso | `enforce: true` por defecto; un aviso que no bloquea no cambia hábitos. La única excepción es el check de autoservicio, porque la etiqueta la pone una persona y la decisión es suya |
| El agente etiqueta `self-service` o auto-mergea | Nada llega a `main` sin una PR revisada por una persona, aunque sea de Producto y el cambio sea un texto. La etiqueta la pone una persona; el agente solo dice si el cambio la merece y `selfservice` lo comprueba |
| Recuento de ficheros por requisito en `REQ-INDEX.md` | Cambiaba con cada commit de código y rompía `index --check` en PRs sin cambios de docs. La pregunta real ("qué requisito no tiene test") la responde `coverage` |
| Beads u otro gestor de estado | El estado durable es el `status` del delta y el historial del spec |
| Embeddings o vector store sobre los specs | Corpus pequeño, estructurado y con ids únicos: tres índices generados (`INDEX.md`, `REQ-INDEX.md`, `CONTRACTS.md`) y `where` por id cubren la búsqueda y la trazabilidad sin LLM. Los agentes de código mayoritarios tampoco usan vectores |
| Grafo de conocimiento (Graphify) desde el principio | Aporta en preguntas de relación entre muchos repos ("qué afecta cambiar este requisito"), a cambio de otra dependencia, tokens por reconstrucción del lado de docs y un `graph.json` que mantener. Se revisa cuando haya una pregunta concreta que los índices no respondan, o más de ~200 requisitos y ~10 repos. Los `// REQ-…` en tests y `Refs:` en commits ya dejan el rastro que un grafo aprovecharía |
| MCP declarados dentro del plugin | Un `.mcp.json` en el plugin fijaría la organización de Azure DevOps o el Jira para todos. El instalador registra el MCP a nivel de usuario con la organización como parámetro |
| Avisos por Teams o Slack como parte del flujo | La PR y el ticket ya notifican. Un aviso es un paso explícito que el usuario pide con el MCP que tenga |
| Ids de modelo concretos en skills o configuración | Caducan con cada versión. Niveles con alias del host (`opus`, `sonnet`, `haiku`) en `models.md` y `sdd.json`; el agente sube o baja de nivel con criterios escritos y lo dice |
| Una skill o un modelo fijo para todo el flujo | Escribir el delta y revisar exigen razonar; implementar está acotado por tests; fusionar es ejecutar un script. Pagar el máximo en todo es caro y pagar el mínimo en el delta es peligroso |
| Prometer un nivel por fase que el host quizá no aplique | La skill delega implementar y revisar con el alias configurado; cuando no puede, lo dice. La promesa es saber siempre qué nivel trabajó, no que la tabla se cumpla a ciegas |
| Reglas de estilo por lenguaje dentro de la skill | Cambian por repo y las aplica el formateador. El plugin lleva `principles.md` (lo que vale en cualquier lenguaje, sin nombres de librerías) y un paquete por lenguaje con lo que el flujo necesita de él; el estilo del repo va a su `AGENTS.md` |
| Soportar todos los lenguajes en el plugin | Cada paquete sin mantenedor se queda viejo y hace daño. Tres de primera (C#, TypeScript, Python), que este repo puede prometer; cualquier otro vive en el repo que lo usa con un `owner` obligatorio, y `/sdd-languages add` sin `--owner` se niega. Un paquete que madura se propone aquí por PR |
| Dos copias de la plantilla `sdd.json` (raíz y plugin) | Las skills necesitan la plantilla instalada (`${CLAUDE_PLUGIN_ROOT}/templates/`); el instalador copia esa misma. Una sola fuente, aunque quede fuera de `templates/` |
| Agentes propios del plugin | Los agentes genéricos (`researcher`, `implementer`, `reviewer`, `tester`) son del setup personal del developer; el plugin solo aporta las skills, los paquetes de lenguaje y el script |
