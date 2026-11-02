# Modelo por fase

Los modelos cambian de nombre y de capacidad cada pocos meses; el flujo no. Por eso aquí solo se habla de **niveles**, con los alias que el host resuelve siempre al modelo actual de ese nivel (`opus`, `sonnet`, `haiku` en Claude Code; nunca un id con fecha). Elegir bien ahorra dinero en lo mecánico y evita errores caros en lo que exige razonar.

## Por defecto

| Fase | Nivel | Por qué |
|---|---|---|
| Crear el delta (leer ticket, decidir requisitos, escribir GIVEN/WHEN/THEN) | **Máximo** (`opus`) | Es donde se decide qué se construye; un requisito mal escrito cuesta más que todo el resto |
| Implementar (TDD requisito a requisito) | **Medio** (`sonnet`) | Trabajo acotado por un delta aprobado y por tests; suficiente y más barato |
| Revisar el diff con el checklist | **Máximo** (`opus`) | Hay que encontrar lo que falta, no seguir pasos |
| Fusionar, regenerar índices, cerrar ticket, `scan`, `where` | **Rápido** (`haiku`) | Es ejecutar el script y leer su salida |

La sesión principal usa el modelo que tenga configurado quien la abre; la skill aplica esta tabla cuando **delega** una fase a un subagente (implementación, revisión) y la recomienda en voz alta cuando no delega ("este delta toca contratos entre servicios; conviene el nivel máximo para escribirlo").

## Cuándo el agente cambia de nivel por su cuenta

Subir al máximo:

- El delta añade o modifica más de tres requisitos, toca un contrato (`Publica:` / `Consume:`), persistencia o autorización.
- Un requisito falla sus tests dos veces seguidas durante la implementación.
- El `spec.md` de la feature tiene decisiones que contradicen lo que pide el ticket.

Bajar al rápido:

- Cambios de solo documentación, regenerar índices, archivar, consultar `where`.
- Vía rápida en código trivial (una línea, un literal, un mensaje) con el test ya existente.

Siempre decirlo en el resumen: qué nivel se usó en cada fase y por qué, para que el equipo pueda corregir la tabla.

## Cómo lo cambia el equipo

`sdd.json` en la raíz del repo del producto (opcional; la plantilla está en `templates/sdd.json`):

```json
{
  "models": { "change": "opus", "impl": "sonnet", "review": "opus", "merge": "haiku" },
  "tracker": "AzureDevOps",
  "createTasks": true,
  "selfService": ["docs/**", "**/*.resx", "**/i18n/**", "src/**/appsettings.Texts.json"]
}
```

- `models`: alias por fase. Si una clave falta, vale la tabla por defecto. Si el host ofrece un nivel nuevo, basta con escribir su alias aquí.
- `tracker`: `AzureDevOps`, `Jira` o `None`; evita que el agente tenga que adivinar qué MCP usar.
- `createTasks`: si al pasar a implementar se crean las tareas hijas del plan sin preguntar (`true`), preguntando (`false`), o no se crean nunca (`"never"`).
- `selfService`: lista de rutas (patrones glob) que una persona sin perfil técnico puede cambiar sin developer cuando no hay cambio de requisitos: textos, traducciones, documentación, valores de configuración acotados. Fuera de esas rutas, o con cambio de requisitos, hace falta un developer. Vacía por defecto: el equipo decide qué abre.

Comprobar qué modelos hay disponibles en la sesión: `/model` en Claude Code. Si el alias configurado no existe, el agente usa el nivel por defecto de la fase y lo dice. Para ver, recomendar o cambiar la tabla sin editar el JSON a mano: `/sdd-models` (`show`, `recommend`, `set <fase> <alias>`, `reset`).
