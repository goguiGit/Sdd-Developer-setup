---
name: sdd-languages
description: >-
  Lista, activa, añade o comprueba los paquetes de lenguaje del flujo SDD (C#, TypeScript y Python vienen con el plugin; cualquier otro se añade en el repo con un dueño). Usar al preparar un repo nuevo, al añadir un lenguaje o stack, o cuando el índice no encuentra los tests ("qué lenguajes soporta", "añade Go", "activa typescript", "/sdd-languages").
argument-hint: "[list | use <lang> | add <lang> --owner <persona> | check]"
---

El flujo no depende del lenguaje; lo que sí depende (extensiones, carpetas a saltar, cómo se cita un requisito en un test, comandos de build y tests, ejemplos de los principios) vive en **paquetes de lenguaje**: un `.md` con frontmatter. Los del plugin están en `${CLAUDE_PLUGIN_ROOT}/skills/sdd/references/languages/` (`csharp`, `typescript`, `python`); los del repo, en `docs/sdd/languages/<lang>.md`. Los activos se listan en `sdd.json` → `languages`, y `/sdd` y el script (`index`, `where`, `coverage`) los usan.

## Qué hace según `$ARGUMENTS`

| Argumento | Acción |
|---|---|
| vacío o `list` | Tabla con los paquetes disponibles (plugin y repo), su `owner`, extensiones y si están activos en `sdd.json` |
| `use <lang>` | Comprueba que el paquete existe y tiene `owner`, lo añade a `languages` en `sdd.json` (crea el fichero desde `${CLAUDE_PLUGIN_ROOT}/templates/sdd.json` si no existe) y rellena o actualiza la sección "Reglas del lenguaje" de `AGENTS.md` con el resumen del paquete (comandos, cómo se cita el requisito) y el enlace al fichero. Commit `chore: activa el paquete de lenguaje <lang>` |
| `add <lang> --owner <persona>` | Crea `docs/sdd/languages/<lang>.md` desde `${CLAUDE_PLUGIN_ROOT}/templates/language.md`, rellena lo que sepas del lenguaje y deja `<...>` en lo que no, con el `owner` indicado; luego hace `use <lang>`. **Sin `--owner`, se niega**: un paquete sin dueño no se activa. Si el lenguaje es de uso general, dilo y propón enviarlo a este marketplace con una PR para que pase a soporte de primera |
| `check` | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sdd.py settings` (paquetes activos que existen, con `owner` y `extensions`) y revisa que la sección "Reglas del lenguaje" de `AGENTS.md` no contradiga los paquetes. Informa; no cambia nada |

## Reglas

- Los tres paquetes del plugin los mantiene este marketplace. No los copies al repo para editarlos: si falta algo, propón el cambio aquí. Lo específico del repo va en su `AGENTS.md`.
- Un paquete del repo con el mismo nombre que uno del plugin tiene prioridad (el script mira primero `docs/sdd/languages/`); úsalo solo cuando el equipo necesite otras extensiones o carpetas, y dilo en el `owner`.
- Nunca actives un lenguaje que no esté en el repo (mira extensiones reales con un vistazo al árbol); un paquete activo de más ensancha el índice sin motivo.
- Si `sdd.json` no declara `languages`, el script usa una lista amplia por defecto que cubre los ecosistemas comunes; activar paquetes la acota y acelera `where` y `coverage`.
