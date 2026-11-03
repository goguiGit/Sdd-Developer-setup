---
name: <slug en minúsculas: go, java, kotlin, rust, sql...>
title: <Nombre del lenguaje o stack>
owner: <persona o equipo que lo mantiene; obligatorio>
extensions: <lista separada por comas: .go>
skipDirs: <carpetas generadas o de dependencias: vendor, target>
testCommand: <comando que ejecuta los tests>
buildCommand: <comando de build>
reqComment: <cómo se cita un requisito en un comentario: // REQ-<AREA>-NNN>
---
# <Nombre del lenguaje>

Solo lo que cambia respecto al flujo común. Las reglas de estilo del repo van en su `AGENTS.md`.

## Cómo se cita un requisito

- <En el nombre del test o en una línea de comentario; ejemplo concreto.>
- <Convención de nombres de tests del lenguaje.>
- <Frameworks de test habituales; no introducir otro.>

## Estructura habitual

```
<carpetas típicas y qué hay en cada una>
```

## Comandos

- Build: `<comando>`
- Tests: `<comando>`; un fichero: `<comando>`

## Trampas del lenguaje para el flujo

- <Carpetas que hay que excluir del índice y por qué.>
- <Lo que hace que un test pase sin probar nada en este lenguaje.>

## Ejemplos de los principios en este lenguaje

| Principio | Señal en <lenguaje> |
|---|---|
| Responsabilidad única | <señal> |
| Inversión de dependencias | <señal> |
| Errores explícitos | <señal> |
| Idempotencia | <señal> |
