# Formato de spec.md y delta.md

Rutas: `docs/features/<feature>/spec.md` y `docs/features/<feature>/changes/<id>-<slug>/delta.md`. Las features son un solo nivel bajo `docs/features/` (sin subcarpetas por servicio o módulo: para eso está el área del requisito). Los cambios cerrados van a `docs/features/<feature>/changes/archive/<YYYY-MM-DD>-<id>-<slug>/`.

## spec.md

```markdown
---
feature: <slug>
title: <Nombre de la feature>
---
# <Nombre de la feature>

Una o dos frases: qué hace y para quién.

## Requisitos

### REQ-<AREA>-001 <Título corto>
GIVEN <situación de partida>
WHEN <lo que ocurre>
THEN <resultado observable>

## Decisiones

- <Decisión y su porqué: problema, alternativa descartada, qué se gana.>

## Historial

| Fecha | PBI | Cambio |
|---|---|---|
| <YYYY-MM-DD> | <id> | Spec inicial |
```

- `AREA` son mayúsculas y dígitos (`REG`, `PAY2`); el número, tres dígitos, correlativo dentro del área y nunca reutilizado. El área es el contexto de negocio, no el repo ni la carpeta: sobrevive a las reorganizaciones.
- Un requisito puede terminar con `Publica: Mensaje1, Mensaje2` o `Consume: Mensaje` cuando emite o recibe mensajes entre servicios. De esas líneas sale `CONTRACTS.md`.
- Un requisito es un bloque desde su `### REQ-…` hasta el siguiente `###` o `##`. Solo lo escribe la fusión de un delta.
- Los ficheros se leen como UTF-8 con o sin BOM; se escriben sin BOM.

## delta.md

```markdown
---
pbi: <id>
title: <Título del cambio>
feature: <slug de la feature>
status: draft
---
## Por qué

<Problema e impacto en dos o tres frases. Si es un bug, la causa raíz.>

## ADDED

### REQ-<AREA>-NNN <Título>
GIVEN <situación>
WHEN <acción>
THEN <resultado>

## MODIFIED

<Texto completo del requisito tal y como debe quedar, con su misma cabecera `### REQ-…`. Vacío si no hay.>

## REMOVED

- REQ-<AREA>-NNN <Título del requisito que se quita>

## Plan

- [ ] <Test que se escribe primero y fichero que toca>
```

- `status`: `draft` (escrito, sin aprobar), `approved` (se puede implementar), `implemented` (listo para fusionar).
- `approved_by: <persona>` es obligatorio en cuanto el `status` deja de ser `draft`. Lo escribe la persona que aprueba, nunca el agente; `lint` lo exige.
- `REMOVED` es una lista de líneas `- REQ-<AREA>-NNN` seguidas del título; cualquier otra forma falla el `lint`. Un mismo id no puede repetirse ni aparecer en dos secciones.
- La carpeta empieza por el id: `<pbi>-<slug>`.

## Nombres

Valen para cualquier lenguaje; las convenciones del lenguaje (PascalCase, snake_case, sufijos) las pone su paquete de lenguaje (`references/languages/` o `docs/sdd/languages/`) y el `AGENTS.md` del repo.

| Qué | Convención | Ejemplo |
|---|---|---|
| Feature | `kebab-case`, el nombre de negocio, sin el nombre del servicio | `registro-usuario`, `aprobacion-vacaciones` |
| Área de requisito | 2-5 mayúsculas del contexto de negocio, estable aunque el código se reorganice | `REG`, `VAC`, `NOM` |
| Requisito | `REQ-<AREA>-NNN` más un título de 2-6 palabras en lenguaje de negocio | `REQ-REG-006 Límite de intentos fallidos` |
| Carpeta del cambio | `<id>-<slug-kebab>` | `1234-limite-intentos` |
| Rama | `feature/<id>-<slug>` o `bugfix/<id>-<slug>` | `feature/1234-limite-intentos` |
| Commit | Conventional commit, el requisito entre paréntesis al final, trailer `Refs: PBI-<id>` (con Jira, `Refs: <clave>`) | `feat: discard the registration after five wrong codes (REQ-REG-006)` |
| Test | Nombre que cuente el GIVEN/WHEN/THEN y el id en el nombre o en una línea, con la forma del lenguaje | C#: `FifthWrongCode_DiscardsRegistration` con `// REQ-REG-006`; TypeScript: `it('discards the registration after the fifth wrong code (REQ-REG-006)')`; Python: `test_fifth_wrong_code_discards_registration_req_reg_006` |
| Mensaje entre servicios | Evento en pasado, comando en imperativo, en inglés como el código | `UserActivated`, `SendWelcomeEmail` |
| PR | Título corto con el id delante; etiqueta `self-service`, puesta por una persona, si es nivel 0 | `1234 Límite de intentos al confirmar` |

## Lo que comprueba `sdd.py`

| Comando | Comprueba |
|---|---|
| `lint <delta>` | Frontmatter con `pbi`, `title`, `feature`, `status` válido y `approved_by` si no es `draft`; carpeta `<pbi>-…`; las tres secciones; ids `REQ-<AREA>-NNN` sin repetir ni en dos secciones; `REMOVED` con la forma `- REQ-… <título>` |
| `check <delta>` | `ADDED` no existe aún en el spec; `MODIFIED` y `REMOVED` sí existen |
| `merge <delta>` | Lo anterior, y que el `status` sea `approved` o `implemented`; aplica, añade historial y archiva |
| `scan [docs]` | `lint` + `check` de todos los deltas abiertos (`archive/` se ignora), un mismo requisito en dos specs, dos deltas abiertos que añaden o modifican el mismo requisito, y que los paquetes de `languages` existen con `owner` y `extensions`. Es lo que corre CI |
| `index [docs] [--check]` | Escribe `docs/features/INDEX.md` (features y deltas abiertos), `REQ-INDEX.md` (requisitos activos con título y feature) y `CONTRACTS.md` (mensajes publicados y consumidos). Con `--check`, falla si están desactualizados; es lo que corre CI. `merge` los regenera solo |
| `where <REQ> [docs]` | El bloque del requisito, los deltas (abiertos y archivados) que lo tocaron, los ficheros de código que lo nombran (palabra completa, en las extensiones de los paquetes activos, saltando sus carpetas generadas) y los commits (`git log --grep`) |
| `coverage [docs]` | Requisitos activos que ningún fichero de código nombra |
| `selfservice [docs]` | Lee rutas por stdin (por ejemplo `git diff --name-only main`) y dice cuáles quedan fuera de los patrones `selfService` de `sdd.json` |
| `settings [docs]` | Que cada paquete de `languages` existe (repo o plugin), tiene `owner` y `extensions`; muestra extensiones y carpetas saltadas resultantes |

Sin `languages` en `sdd.json`, `where` y `coverage` usan una lista amplia de extensiones y carpetas que cubre los ecosistemas comunes.
