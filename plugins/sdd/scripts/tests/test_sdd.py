import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sdd  # noqa: E402

SPEC = """---
feature: registro-usuario
title: Registro de usuario
---
# Registro de usuario

## Requisitos

### REQ-REG-001 Alta pendiente
GIVEN un email válido
WHEN se registra
THEN el usuario queda pendiente de confirmación

### REQ-REG-002 Confirmación
GIVEN un usuario pendiente
WHEN confirma con el código correcto
THEN pasa a activo

### REQ-REG-003 Caducidad
GIVEN un usuario pendiente
WHEN pasan 24 horas sin confirmar
THEN el registro se descarta

## Decisiones

- La saga decide si el código es correcto.

## Historial

| Fecha | PBI | Cambio |
|---|---|---|
| 2026-10-30 | 1000 | Spec inicial |
"""

DELTA = """---
pbi: 1234
title: Límite de intentos
feature: registro-usuario
status: approved
approved_by: ana
---
## Por qué

Seis dígitos y 24 horas admiten fuerza bruta.

## ADDED

### REQ-REG-004 Límite de intentos
GIVEN un usuario pendiente con 4 códigos incorrectos
WHEN envía un quinto código incorrecto
THEN el registro se descarta

## MODIFIED

### REQ-REG-002 Confirmación
GIVEN un usuario pendiente con menos de 5 intentos fallidos
WHEN confirma con el código correcto
THEN pasa a activo

## REMOVED

- REQ-REG-003

## Plan

- [ ] Test del quinto intento
"""


def write(folder: Path, name: str, text: str) -> Path:
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


class LintTests(unittest.TestCase):
    def test_valid_delta_has_no_errors(self):
        self.assertEqual(sdd.lint_delta(DELTA, "1234-limite-intentos"), [])

    def test_missing_status_is_reported(self):
        text = DELTA.replace("status: approved\n", "")
        self.assertIn("frontmatter: falta 'status'", sdd.lint_delta(text, "1234-limite-intentos"))

    def test_unknown_status_is_reported(self):
        text = DELTA.replace("status: approved", "status: done")
        self.assertIn("frontmatter: status 'done' no es draft, approved ni implemented", sdd.lint_delta(text, "1234-limite-intentos"))

    def test_bad_req_id_is_reported(self):
        text = DELTA.replace("### REQ-REG-004", "### REQ-reg-4")
        self.assertIn("ADDED: 'REQ-reg-4' no cumple REQ-<AREA>-NNN", sdd.lint_delta(text, "1234-limite-intentos"))

    def test_folder_must_start_with_pbi(self):
        self.assertIn("carpeta: '9-otro' debe empezar por el pbi 1234", sdd.lint_delta(DELTA, "9-otro"))

    def test_missing_section_is_reported(self):
        text = DELTA.replace("## REMOVED\n\n- REQ-REG-003\n\n", "")
        self.assertIn("falta la sección REMOVED", sdd.lint_delta(text, "1234-limite-intentos"))


class CheckTests(unittest.TestCase):
    def test_valid_delta_merges_cleanly(self):
        self.assertEqual(sdd.check_merge(DELTA, SPEC), [])

    def test_added_must_not_exist(self):
        text = DELTA.replace("REQ-REG-004", "REQ-REG-001")
        self.assertIn("ADDED: REQ-REG-001 ya existe en el spec", sdd.check_merge(text, SPEC))

    def test_modified_must_exist(self):
        text = DELTA.replace("### REQ-REG-002 Confirmación", "### REQ-REG-009 Confirmación")
        self.assertIn("MODIFIED: REQ-REG-009 no existe en el spec", sdd.check_merge(text, SPEC))

    def test_removed_must_exist(self):
        text = DELTA.replace("- REQ-REG-003", "- REQ-REG-008")
        self.assertIn("REMOVED: REQ-REG-008 no existe en el spec", sdd.check_merge(text, SPEC))


class MergeTests(unittest.TestCase):
    def merged(self) -> str:
        return sdd.merge(DELTA, SPEC, today="2026-11-02")

    def test_added_requirement_is_appended(self):
        self.assertIn("### REQ-REG-004 Límite de intentos\nGIVEN un usuario pendiente con 4 códigos incorrectos", self.merged())

    def test_modified_requirement_is_replaced(self):
        merged = self.merged()
        self.assertIn("GIVEN un usuario pendiente con menos de 5 intentos fallidos", merged)
        self.assertNotIn("GIVEN un usuario pendiente\nWHEN confirma con el código correcto", merged)

    def test_removed_requirement_disappears(self):
        self.assertNotIn("REQ-REG-003", self.merged())

    def test_history_row_is_added(self):
        self.assertIn("| 2026-11-02 | 1234 | Límite de intentos |", self.merged())

    def test_decisions_section_is_kept(self):
        self.assertIn("- La saga decide si el código es correcto.", self.merged())


class ArchiveTests(unittest.TestCase):
    def test_merge_and_archive_moves_the_change_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "docs" / "features" / "registro-usuario"
            change = feature / "changes" / "1234-limite-intentos"
            change.mkdir(parents=True)
            spec = write(feature, "spec.md", SPEC)
            delta = write(change, "delta.md", DELTA)

            archived = sdd.merge_and_archive(delta, today="2026-11-02")

            self.assertEqual(archived, feature / "changes" / "archive" / "2026-11-02-1234-limite-intentos")
            self.assertFalse(change.exists())
            self.assertTrue((archived / "delta.md").exists())
            self.assertIn("REQ-REG-004", spec.read_text(encoding="utf-8"))

    def test_merge_refuses_a_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "docs" / "features" / "registro-usuario"
            change = feature / "changes" / "1234-limite-intentos"
            change.mkdir(parents=True)
            write(feature, "spec.md", SPEC)
            delta = write(change, "delta.md", DELTA.replace("status: approved", "status: draft"))

            with self.assertRaises(sdd.SddError):
                sdd.merge_and_archive(delta, today="2026-11-02")


if __name__ == "__main__":
    unittest.main()
