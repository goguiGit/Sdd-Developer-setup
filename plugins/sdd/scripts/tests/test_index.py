import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sdd  # noqa: E402

SPEC_REG = """---
feature: registro-usuario
title: Registro de usuario
---
# Registro de usuario

## Requisitos

### REQ-REG-001 Alta pendiente
GIVEN un email válido
WHEN se registra
THEN el usuario queda pendiente
Publica: UserRegistered

### REQ-REG-002 Confirmación
GIVEN un usuario pendiente
WHEN confirma con el código correcto
THEN pasa a activo
Publica: UserActivated, SendWelcomeEmail

## Decisiones

- Ninguna.

## Historial

| Fecha | PBI | Cambio |
|---|---|---|
| 2026-10-30 | 1000 | Spec inicial |
| 2026-11-02 | 1234 | Límite de intentos |
"""

SPEC_NOT = """---
feature: notificaciones
title: Notificaciones
---
# Notificaciones

## Requisitos

### REQ-NOT-001 Bienvenida
GIVEN un usuario activado
WHEN llega UserActivated
THEN se envía el correo de bienvenida
Consume: UserActivated

## Decisiones

## Historial

| Fecha | PBI | Cambio |
|---|---|---|
| 2026-10-30 | 1001 | Spec inicial |
"""

DELTA_OPEN = """---
pbi: 1300
title: Reenvío del código
feature: registro-usuario
status: draft
---
## Por qué

Se pierde.

## ADDED

### REQ-REG-003 Reenvío
GIVEN un usuario pendiente
WHEN pide otro código
THEN recibe uno nuevo

## MODIFIED

## REMOVED

## Plan

- [ ] Test del reenvío
"""


def make_repo(tmp: str) -> Path:
    root = Path(tmp)
    reg = root / "docs" / "features" / "registro-usuario"
    (reg / "changes" / "1300-reenvio").mkdir(parents=True)
    (reg / "changes" / "archive" / "2026-11-02-1234-limite-intentos").mkdir(parents=True)
    (reg / "spec.md").write_text(SPEC_REG, encoding="utf-8")
    (reg / "changes" / "1300-reenvio" / "delta.md").write_text(DELTA_OPEN, encoding="utf-8")
    (reg / "changes" / "archive" / "2026-11-02-1234-limite-intentos" / "delta.md").write_text(
        DELTA_OPEN.replace("1300", "1234").replace("status: draft", "status: implemented").replace("REQ-REG-003", "REQ-REG-002"),
        encoding="utf-8",
    )
    noti = root / "docs" / "features" / "notificaciones"
    noti.mkdir(parents=True)
    (noti / "spec.md").write_text(SPEC_NOT, encoding="utf-8")
    tests = root / "tests"
    tests.mkdir()
    (tests / "RegistrationTests.cs").write_text("// REQ-REG-001\npublic void Register_PendingUser() {}\n// REQ-REG-002\n", encoding="utf-8")
    (root / "bin").mkdir()
    (root / "bin" / "ignored.cs").write_text("REQ-REG-001", encoding="utf-8")
    return root


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(self.tmp.name)
        self.docs = self.root / "docs"

    def tearDown(self):
        self.tmp.cleanup()

    def test_feature_index_has_one_row_per_feature(self):
        index = sdd.build_index(self.docs)
        self.assertIn("| notificaciones | Notificaciones | 1 | 0 | 2026-10-30 |", index["INDEX.md"])
        self.assertIn("| registro-usuario | Registro de usuario | 2 | 1 | 2026-11-02 |", index["INDEX.md"])

    def test_contracts_index_links_publishers_and_consumers(self):
        contracts = sdd.build_index(self.docs)["CONTRACTS.md"]
        self.assertIn("| UserActivated | REQ-REG-002 (registro-usuario) | REQ-NOT-001 (notificaciones) |", contracts)
        self.assertIn("| UserRegistered | REQ-REG-001 (registro-usuario) | |", contracts)

    def test_write_index_then_check_is_clean(self):
        sdd.write_index(self.docs)
        self.assertEqual(sdd.check_index(self.docs), [])

    def test_check_reports_stale_index(self):
        sdd.write_index(self.docs)
        (self.docs / "features" / "notificaciones" / "spec.md").write_text(
            SPEC_NOT.replace("### REQ-NOT-001 Bienvenida", "### REQ-NOT-001 Correo de bienvenida"), encoding="utf-8"
        )
        self.assertEqual(sdd.check_index(self.docs), ["docs/features/REQ-INDEX.md desactualizado: ejecuta sdd.py index"])

    def test_check_reports_missing_index(self):
        self.assertIn("docs/features/INDEX.md no existe: ejecuta sdd.py index", sdd.check_index(self.docs))


class WhereTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_where_finds_spec_block(self):
        report = sdd.where("REQ-REG-002", self.root / "docs")
        self.assertIn("### REQ-REG-002 Confirmación", report)
        self.assertIn("docs/features/registro-usuario/spec.md", report.replace("\\", "/"))

    def test_where_lists_deltas_that_touched_it(self):
        report = sdd.where("REQ-REG-002", self.root / "docs")
        self.assertIn("1234", report)
        self.assertIn("archive", report)

    def test_where_lists_tests_that_name_it(self):
        report = sdd.where("REQ-REG-002", self.root / "docs")
        self.assertIn("tests/RegistrationTests.cs", report.replace("\\", "/"))

    def test_where_unknown_requirement_says_so(self):
        report = sdd.where("REQ-REG-999", self.root / "docs")
        self.assertIn("REQ-REG-999 no está en ningún spec", report)


if __name__ == "__main__":
    unittest.main()
