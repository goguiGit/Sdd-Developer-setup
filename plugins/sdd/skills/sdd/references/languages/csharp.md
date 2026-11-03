---
name: csharp
title: C# / .NET
owner: Sdd-Developer-setup (soporte de primera)
extensions: .cs, .razor, .cshtml, .fs
skipDirs: bin, obj, TestResults, packages
testCommand: dotnet test
buildCommand: dotnet build
reqComment: // REQ-<AREA>-NNN
---
# C# / .NET

Lo que cambia respecto al flujo común cuando el repo es .NET. Las reglas de estilo del repo (nullable, analizadores, orden de `using`) van en su `AGENTS.md`; aquí solo lo que el flujo necesita.

## Cómo se cita un requisito

- En el test: una línea `// REQ-REG-006` encima del método, o el id en el nombre si el equipo lo prefiere (`Confirm_FifthWrongCode_DiscardsRegistration_REQ_REG_006` es legal pero largo; la línea es más legible).
- Nombre del test: `Clase_Metodo_Resultado` o `Escenario_Resultado` en PascalCase, un comportamiento por test (`FifthWrongCode_DiscardsRegistration`).
- Frameworks habituales: NUnit (`Assert.That`), xUnit (`Assert.Equal`), con Shouldly o FluentAssertions si el repo ya los usa. No introducir otro.

## Estructura habitual

```
src/<Proyecto>/            código; namespace = ruta de carpetas
tests/<Proyecto>.Tests/    espejo de src; un fichero de test por clase o por feature
Directory.Build.props      TargetFramework, Nullable, LangVersion (no repetirlos en los csproj)
Directory.Packages.props   versiones centralizadas (PackageReference sin Version)
```

## Comandos

- Build: `dotnet build <solución>.slnx` (o `.sln`).
- Tests: `dotnet test <solución>`; un fichero: `dotnet test --filter "FullyQualifiedName~Nombre"`.
- Formato: `dotnet format` si el repo lo tiene configurado.

## Trampas del lenguaje para el flujo

- `bin/` y `obj/` contienen copias de los fuentes y ficheros generados: siempre fuera del índice (ya están en `skipDirs`).
- Un `record` con una lista dentro no compara por valor; para `Is.EqualTo` sobre el resultado completo, usar texto o colecciones comparables.
- Los tests de integración contra servicios reales llevan `[Category("Integration")]` y `Assert.Ignore` si falta la configuración; nunca credenciales en código ni en `appsettings*.json` (user-secrets).
- `async` siempre con `CancellationToken cancellationToken = default` y sufijo `Async`; nunca `.Result` ni `.Wait()`.

## Ejemplos de los principios en este lenguaje

| Principio | Señal en C# |
|---|---|
| Responsabilidad única | Una clase `XManager` o `XHelper` que crece con cada PBI; un handler de MediatR que valida, persiste y publica |
| Inversión de dependencias | `using Microsoft.EntityFrameworkCore` o un `HttpClient` dentro del proyecto de dominio |
| Errores explícitos | `catch (Exception) { }`; lanzar `NotFoundException` para un caso de negocio en vez de devolver un `Result` |
| Idempotencia | Un `IConsumer<T>` que hace `Add` sin comprobar si ya existe |
