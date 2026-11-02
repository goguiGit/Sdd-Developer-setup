---
name: sdd-models
description: Muestra, recomienda o cambia el nivel de modelo que el flujo SDD usa en cada fase (crear el delta, implementar, revisar, fusionar), guardándolo en sdd.json del repo. Usar cuando cambien los modelos disponibles, cuando algo salga caro o flojo, o al preguntar qué modelo conviene ("qué modelo usa cada fase", "cambia el modelo de implementación", "hay modelos nuevos", "/sdd-models").
argument-hint: [show | recommend | set <fase> <alias> | reset]
---

Los modelos cambian; el flujo no. Esta skill mantiene la correspondencia fase → nivel en `sdd.json` (raíz del repo) sin tocar nada más. La política y los criterios están en [../sdd/references/models.md](../sdd/references/models.md).

## Qué hace según `$ARGUMENTS`

| Argumento | Acción |
|---|---|
| vacío o `show` | Lee `sdd.json` (o dice que no existe y que valen los valores por defecto) y muestra la tabla fase → alias con la razón de cada nivel. Dice también qué modelo está usando la sesión actual, si lo sabe |
| `recommend` | Mira qué alias de nivel ofrece el host ahora (en Claude Code, los que acepta `/model`; si no puedes consultarlo, pregunta al usuario qué ve en `/model`), compara con `sdd.json` y propone cambios: un alias que ya no existe, un nivel nuevo que encaja mejor en alguna fase, o una fase que según el historial reciente (tests fallando dos veces, deltas rechazados) merece subir. Propone, no cambia |
| `set <fase> <alias>` | Escribe la clave en `models` de `sdd.json` (`change`, `impl`, `review`, `merge`), crea el fichero desde `templates/sdd.json` si no existe, y confirma con la tabla resultante. Rechaza una fase desconocida; un alias desconocido lo avisa pero lo escribe, porque puede ser un nivel nuevo del host |
| `reset` | Devuelve `models` a la tabla por defecto de `models.md` |

## Reglas

- Solo alias de nivel (`opus`, `sonnet`, `haiku` o el que el host añada); nunca ids con fecha. Si el usuario pide fijar un id concreto, explica por qué no y ofrece el alias de su nivel.
- No cambies el modelo de la sesión actual ni la configuración global de Claude Code: eso es de la persona. La skill solo escribe `sdd.json`.
- Cada cambio va en un commit propio, `chore: modelo de <fase> a <alias>`, para que el equipo vea cuándo y por qué cambió. Pide el porqué si no te lo dicen y ponlo en el cuerpo del commit.
- Si `sdd.json` fija un alias que el host no reconoce, el flujo `/sdd` usa el nivel por defecto de esa fase y lo dice; esta skill es el sitio para arreglarlo.
