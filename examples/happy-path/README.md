# Ejemplo: el camino feliz, de principio a fin

Un PBI real del servicio de registro, desde que llega hasta que el spec lo absorbe, con lo que escribe la persona, lo que hace el agente, qué ficheros cambian, qué tareas aparecen en el gestor y qué modelo se usa en cada fase. El repo de ejemplo es [MassTransit.Saga.Demo](https://github.com/goguiGit/MassTransit.Saga.Demo), cuyo spec está en [`docs/features/registro-usuario/`](../../docs/features/registro-usuario/spec.md); el gestor es Azure DevOps conectado por MCP, y el `sdd.json` del repo es [este](sdd.json).

## Punto de partida

- PBI **1234** en Azure DevOps, estado *Approved*: "Límite de intentos al confirmar el email. Hoy un código incorrecto no tiene consecuencias; con seis dígitos y 24 h se puede probar por fuerza bruta. Criterio: tras el quinto fallo el registro se descarta y se avisa".
- `docs/features/registro-usuario/spec.md` con cinco requisitos, `REQ-REG-001` a `REQ-REG-005`.
- `docs/features/INDEX.md` y `REQ-INDEX.md` al día.

## Paso 1. Crear el delta

**La persona escribe**, en Claude Code dentro del repo:

```
/sdd 1234 límite de intentos al confirmar el email
```

**El agente** (nivel máximo, porque va a decidir requisitos):

1. Lee `INDEX.md`: una feature, `registro-usuario`, sin deltas abiertos. Abre solo ese spec.
2. Lee el PBI 1234 por el MCP de Azure DevOps: título, descripción, criterios de aceptación. Lo pasa a *In Progress* y se lo asigna.
3. Escribe `docs/features/registro-usuario/changes/1234-limite-intentos/delta.md` en `status: draft`: por qué (fuerza bruta), `ADDED` con `REQ-REG-006 Límite de intentos fallidos`, `MODIFIED` con el texto nuevo completo de `REQ-REG-003 Código incorrecto` (ahora cuenta el intento), `REMOVED` vacío, y un plan de cuatro casillas.
4. `sdd.py lint` y `check`: ok.
5. Rama `feature/1234-limite-intentos`, commit `docs: delta del PBI 1234, límite de intentos de confirmación` con `Refs: PBI-1234`.

**Resumen que devuelve**: "Delta en draft: añade REQ-REG-006, modifica REQ-REG-003, no quita nada. Para implementar hace falta `status: approved`. Usé el nivel máximo para escribirlo porque modifica un requisito existente."

Nada de código todavía.

## Paso 2. Aprobar

Otra persona del equipo lee el delta (doce líneas de requisitos) y cambia `status: draft` por `status: approved`, o aprueba la PR que solo contiene el delta si el equipo trabaja así. Si quisiera cambiar el umbral de cinco a tres intentos, lo dice ahora y el agente reescribe el delta; es barato cambiarlo aquí y caro después.

## Paso 3. Implementar, con tareas en el gestor

**La persona escribe**:

```
/sdd 1234
```

**El agente** lee el delta: `approved`. Lee `sdd.json`: `"tracker": "AzureDevOps"`, `"createTasks": true`, `"impl": "sonnet"`.

1. **Crea las tareas** en Azure DevOps, una por casilla del plan, hijas del PBI 1234, y lo dice:

   | Tarea creada | Texto |
   |---|---|
   | 1234-1 | Test: el quinto código incorrecto publica `RegistrationDiscarded` (REQ-REG-006) |
   | 1234-2 | Test: el cuarto código incorrecto deja la saga en `AwaitingConfirmation` con `FailedAttempts = 4` (REQ-REG-003) |
   | 1234-3 | `RegistrationState.FailedAttempts` y `Reject()` en el dominio |
   | 1234-4 | La rama `Ignore` de `EmailConfirmed` pasa a `When` que cuenta y decide |

   Con `"createTasks": false` habría preguntado antes; con `"never"`, no las crea.

2. **Delega la implementación en un subagente de nivel medio** (`sonnet`) con el delta y el spec como contexto, requisito a requisito:
   - `REQ-REG-006`: test `RegistrationStateMachine_FifthWrongCode_DiscardsRegistration` en rojo → `FailedAttempts` en `RegistrationState`, `Reject()` → verde → commit `feat: discard the registration after five wrong codes (REQ-REG-006)` con `Refs: PBI-1234`. Cierra la tarea 1234-1 y 1234-3.
   - `REQ-REG-003`: cambia el test existente al nuevo GIVEN/WHEN/THEN, lo ve fallar, cambia el `Ignore` por un `When` que incrementa → commit `feat: count failed confirmation attempts (REQ-REG-003)`. Cierra 1234-2 y 1234-4.
3. Suite completa en verde (30 tests de la demo más los dos nuevos). Comprueba que `REQ-REG-006` y `REQ-REG-003` tienen tests que los nombran.
4. Marca las casillas del plan, `status: implemented`, commit `docs: PBI 1234 implementado`.

**Resumen**: "Dos requisitos implementados en cuatro commits, 32 tests en verde, cuatro tareas cerradas en Azure DevOps. Implementación con nivel medio; no hizo falta subir porque ningún test falló dos veces. Siguiente paso: PR."

Si durante la implementación un test hubiera fallado dos veces seguidas, el agente habría subido al nivel máximo para ese requisito y lo habría dicho en el resumen.

## Paso 4. PR y revisión

La persona abre la PR. El CI ejecuta `sdd.py scan` (el delta encaja con el spec) e `index --check` (los índices no cambian en esta PR porque el spec no cambia hasta la fusión). El revisor aplica las siete filas del [checklist](../../plugins/sdd/skills/sdd/references/review-checklist.md); si pide la revisión al agente, va en nivel máximo.

## Paso 5. Fusionar

Tras el merge, la persona escribe:

```
/sdd 1234
```

**El agente** lee el delta: `implemented`. Nivel rápido: solo ejecuta el script y lee su salida.

1. `sdd.py merge`: `REQ-REG-006` entra en el spec, `REQ-REG-003` queda con el texto nuevo, fila `| 2026-11-02 | 1234 | Límite de intentos de confirmación |` en el historial, carpeta movida a `changes/archive/2026-11-02-1234-limite-intentos/`, índices regenerados (`REQ-INDEX.md` gana una línea).
2. Relee el spec: numeración correcta, la decisión "la saga decide si el código es correcto" sigue siendo cierta.
3. Commit `docs: fusiona el PBI 1234 en el spec de registro-usuario`, `Refs: PBI-1234`.
4. Como se lo piden, copia los GIVEN/WHEN/THEN de `ADDED` y `MODIFIED` a los criterios de aceptación del PBI 1234 y lo pasa a *Done*.

## Qué quedó

```
docs/features/registro-usuario/spec.md                                   ← 6 requisitos, historial con el 1234
docs/features/registro-usuario/changes/archive/2026-11-02-1234-limite-intentos/delta.md
docs/features/INDEX.md, REQ-INDEX.md, CONTRACTS.md                       ← regenerados
src/… y tests/…                                                          ← 4 commits con (REQ-REG-006) y (REQ-REG-003)
Azure DevOps                                                             ← PBI 1234 Done, 4 tareas cerradas, criterios de aceptación = los requisitos
```

Y `python plugins/sdd/scripts/sdd.py where REQ-REG-006` lo enseña todo junto: el bloque del spec, el delta archivado, los dos ficheros de test y los commits.

## Variantes del mismo camino

- **Lo pide Producto, no un developer**: la persona de producto escribe `/sdd 1250 que el correo de bienvenida diga "Hola, <nombre>" en vez de "Bienvenida"`. El agente clasifica: no cambia ningún requisito (REQ-REG-002 sigue siendo cierto) y solo toca `**/*.resx`, que está en `selfService`: **nivel 0**. Implementa, deja el test de la bienvenida en verde, abre la PR con la etiqueta `self-service` y dice que la puede revisar cualquiera del equipo. Ningún developer ha intervenido. Si en cambio hubiera pedido "que el código tenga ocho dígitos", el agente habría escrito el delta igual de claro y habría dicho: "nivel 1, un developer tiene que aprobar este delta".

- **Sin gestor** (`"tracker": "None"`): el agente pregunta por el PBI una vez, no crea tareas y al final dice qué cerrar a mano.
- **Sin cambio de requisitos** (por ejemplo, el correo de bienvenida tenía una falta de ortografía): no hay delta; `/sdd 1300 corrige la bienvenida` implementa con TDD citando `REQ-REG-002` en el commit. Nivel rápido.
- **El ticket cambia a mitad**: el delta vuelve a `draft`, se reescribe y se vuelve a aprobar. Las tareas ya creadas se actualizan o se cierran como descartadas, y se dice cuáles.
