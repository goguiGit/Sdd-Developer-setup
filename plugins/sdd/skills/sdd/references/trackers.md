# Gestor de tareas (Azure DevOps o Jira)

El flujo funciona sin gestor: el id del delta es un número y el usuario cuenta lo que haga falta. Con un gestor conectado por MCP, la skill lee el ticket, crea las tareas del plan y cierra el ticket al fusionar. El MCP se registra una vez en la máquina (`setup/install.ps1 -Tracker …` o a mano); comprueba cuál hay con `claude mcp list` y usa los nombres de herramienta que ese servidor exponga.

## Qué hace la skill en cada fase

| Fase | Con gestor | Sin gestor |
|---|---|---|
| Crear el delta | Lee título, descripción y criterios de aceptación del ticket; si el ticket tiene un estado de "listo para trabajar", lo pasa a "en curso" y se lo asigna al usuario | Pregunta al usuario lo imprescindible, una vez |
| Delta aprobado, al empezar a implementar | Si el usuario quiere, crea **una tarea hija por casilla del plan**, con el texto de la casilla y enlazada al ticket padre; al marcar cada casilla, cierra su tarea | Solo las casillas del delta |
| Fusionar | Copia los `GIVEN / WHEN / THEN` de `ADDED` y `MODIFIED` a los criterios de aceptación del ticket y lo cierra, si el usuario lo pide | Le dice al usuario qué cerrar a mano |

Nunca crear tareas antes de la aprobación: un delta en `draft` puede cambiar entero. Nunca cerrar un ticket cuya PR no esté mergeada.

## Azure DevOps

MCP oficial de Microsoft, `@azure-devops/mcp` (npm), con la organización como argumento; se autentica con la sesión de `az login`:

```
claude mcp add --scope user azure-devops -- npx -y @azure-devops/mcp <organizacion>
```

Operaciones que usa la skill (nombres orientativos; confírmalos en la lista de herramientas del servidor): obtener un work item con todos los campos, crear work items hijos de tipo `Task` enlazados al PBI, actualizar campos (`Acceptance Criteria`, `State`, `Assigned To`). Sin MCP, la CLI sirve para leer: `az boards work-item show --id <id> --org https://dev.azure.com/<organizacion>`.

Convenciones: rama `feature/<id>-<slug>` o `bugfix/<id>-<slug>`; trailer `Refs: PBI-<id>` en los commits y `AB#<id>` en el título o cuerpo de la PR para que Azure Boards la enlace.

## Jira

MCP remoto de Atlassian (OAuth en el navegador la primera vez):

```
claude mcp add --transport sse --scope user atlassian https://mcp.atlassian.com/v1/sse
```

Operaciones: leer la issue, crear sub-tareas enlazadas a la issue padre, editar la descripción o el campo de criterios de aceptación y transicionar el estado. El id del delta es la clave de la issue (`PROJ-123`), y `pbi:` en el frontmatter la guarda tal cual; la carpeta es `PROJ-123-<slug>`, la rama `feature/PROJ-123-<slug>` y el trailer de los commits `Refs: PROJ-123` (Jira enlaza la clave allí donde aparezca).

## Otros canales

Avisar por Teams o Slack de que un delta espera aprobación o de que una PR está lista no forma parte del flujo: la PR y el ticket ya notifican por sus propios medios. Si el equipo quiere un aviso, es un paso explícito que el usuario pide ("avisa en el canal del equipo") con el MCP que tenga conectado; la skill no lo hace por su cuenta.
