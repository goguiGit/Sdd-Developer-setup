---
name: typescript
title: TypeScript / JavaScript
owner: Sdd-Developer-setup (soporte de primera)
extensions: .ts, .tsx, .js, .jsx, .mjs, .cjs, .vue, .svelte
skipDirs: node_modules, dist, build, out, coverage, .next, .nuxt, .svelte-kit, .angular
testCommand: npm test
buildCommand: npm run build
reqComment: // REQ-<AREA>-NNN
---
# TypeScript / JavaScript

Lo que cambia respecto al flujo común cuando el repo es Node, Angular, React, Vue o Svelte. Las reglas de estilo (ESLint, Prettier, convenciones del framework) van en el `AGENTS.md` del repo.

## Cómo se cita un requisito

- En el test, el id dentro del nombre del caso, que en estos frameworks es una frase: `it('discards the registration after the fifth wrong code (REQ-REG-006)', …)`. Alternativa: `// REQ-REG-006` encima del `it`/`test`.
- Nombre del test: una frase en presente que cuente el WHEN/THEN; `describe` con la unidad o la feature.
- Frameworks habituales: Vitest, Jest, Jasmine/Karma en Angular antiguo, Playwright o Cypress para end-to-end. No introducir otro.

## Estructura habitual

```
src/                       código; un componente, servicio o módulo por carpeta
src/**/*.spec.ts           tests junto al código (Angular, Vitest) o en tests/ (Node)
package.json               scripts: build, test, lint; versiones fijadas en package-lock.json
```

## Comandos

- Build: `npm run build` (o `pnpm`/`yarn` si el repo los usa; mirar el lockfile).
- Tests: `npm test`; un fichero: `npx vitest run <ruta>` o `npx jest <ruta>`; Angular: `npx ng test --watch=false`.
- Lint: `npm run lint`.

## Trampas del lenguaje para el flujo

- `node_modules/`, `dist/`, `.next/` y similares pesan miles de ficheros: fuera del índice (ya en `skipDirs`); un `where` sin podarlos tarda minutos.
- En PowerShell, `npm` ejecuta `npm.ps1` y la política de scripts puede bloquearlo; `npm.cmd` en scripts de Windows.
- Un `it` sin `expect` pasa siempre; cada test del requisito tiene al menos una aserción sobre el resultado observable.
- Promesas sin `await` en tests pasan antes de fallar; `async`/`await` o devolver la promesa.

## Ejemplos de los principios en este lenguaje

| Principio | Señal en TypeScript |
|---|---|
| Responsabilidad única | Un servicio Angular que llama a la API, formatea y guarda estado de UI; un componente con lógica de negocio |
| Inversión de dependencias | Importar `axios` o el cliente HTTP dentro de la lógica de dominio en vez de inyectar una interfaz |
| Errores explícitos | `catch (e) {}`; `throw` para "no encontrado" en vez de devolver un resultado tipado |
| Idempotencia | Un handler de evento que hace `push` a una lista sin comprobar si el id ya está |
