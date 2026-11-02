# Formato de spec.md y delta.md

Rutas: `docs/features/<feature>/spec.md` y `docs/features/<feature>/changes/<id>-<slug>/delta.md`. Los cambios cerrados van a `docs/features/<feature>/changes/archive/<YYYY-MM-DD>-<id>-<slug>/`.

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

<Lista `- REQ-<AREA>-NNN`. Vacío si no hay.>

## Plan

- [ ] <Test que se escribe primero y fichero que toca>
```

- `status`: `draft` (escrito, sin aprobar), `approved` (se puede implementar), `implemented` (listo para fusionar).
- La carpeta empieza por el id: `<pbi>-<slug>`.

## Lo que comprueba `sdd.py`

| Comando | Comprueba |
|---|---|
| `lint <delta>` | Frontmatter con `pbi`, `title`, `feature`, `status` válido; carpeta `<pbi>-…`; las tres secciones; ids `REQ-<AREA>-NNN` |
| `check <delta>` | `ADDED` no existe aún en el spec; `MODIFIED` y `REMOVED` sí existen |
| `merge <delta>` | Lo anterior, y que el `status` sea `approved` o `implemented`; aplica, añade historial y archiva |
| `scan [docs]` | `lint` + `check` de todos los deltas abiertos; `archive/` se ignora. Es lo que corre CI |
| `index [docs] [--check]` | Escribe `docs/features/INDEX.md` (features y deltas abiertos), `REQ-INDEX.md` (requisitos activos con su feature y cuántos ficheros de código los nombran) y `CONTRACTS.md` (mensajes publicados y consumidos). Con `--check`, falla si están desactualizados; es lo que corre CI. `merge` los regenera solo |
| `where <REQ> [docs]` | El bloque del requisito, los deltas (abiertos y archivados) que lo tocaron, los ficheros de código que lo nombran y los commits (`git log --grep`) |
