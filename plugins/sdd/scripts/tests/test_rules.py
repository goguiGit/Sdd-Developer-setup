import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sdd  # noqa: E402
from test_index import DELTA_OPEN, SPEC_NOT, SPEC_REG, make_repo  # noqa: E402
from test_sdd import DELTA, SPEC  # noqa: E402


class RemovedSectionTests(unittest.TestCase):
    def test_removed_item_with_title_is_accepted(self):
        text = DELTA.replace("- REQ-REG-003", "- REQ-REG-003 Caducidad")
        self.assertEqual(sdd.lint_delta(text, "1234-limite-intentos"), [])
        self.assertEqual(sdd.parse_delta(text).removed(), ["REQ-REG-003"])

    def test_removed_heading_style_is_rejected(self):
        text = DELTA.replace("- REQ-REG-003", "### REQ-REG-003 Caducidad")
        self.assertIn("REMOVED: '### REQ-REG-003 Caducidad' debe ser '- REQ-<AREA>-NNN [título]'", sdd.lint_delta(text, "1234-limite-intentos"))

    def test_removed_with_title_is_merged_out(self):
        text = DELTA.replace("- REQ-REG-003", "- REQ-REG-003 Caducidad")
        self.assertNotIn("REQ-REG-003", sdd.merge(text, SPEC, today="2026-11-02"))


class DuplicateTests(unittest.TestCase):
    def test_duplicate_id_inside_a_section_is_reported(self):
        text = DELTA.replace(
            "## MODIFIED",
            "### REQ-REG-004 Otra vez\nGIVEN a\nWHEN b\nTHEN c\n\n## MODIFIED",
        )
        self.assertIn("ADDED: REQ-REG-004 aparece dos veces", sdd.lint_delta(text, "1234-limite-intentos"))

    def test_same_id_in_two_sections_is_reported(self):
        text = DELTA.replace("- REQ-REG-003", "- REQ-REG-002")
        self.assertIn("REQ-REG-002 está en MODIFIED y REMOVED a la vez", sdd.lint_delta(text, "1234-limite-intentos"))


class ApprovalTests(unittest.TestCase):
    def test_approved_requires_approved_by(self):
        text = DELTA.replace("status: approved\n", "status: approved\n").replace("approved_by: ana\n", "")
        self.assertIn("frontmatter: falta 'approved_by' (obligatorio cuando status no es draft)", sdd.lint_delta(text, "1234-limite-intentos"))

    def test_draft_does_not_require_approved_by(self):
        text = DELTA.replace("status: approved", "status: draft")
        self.assertEqual(sdd.lint_delta(text, "1234-limite-intentos"), [])

    def test_approved_with_approved_by_is_valid(self):
        text = DELTA.replace("status: approved\n", "status: approved\napproved_by: ana\n")
        self.assertEqual(sdd.lint_delta(text, "1234-limite-intentos"), [])


class EncodingTests(unittest.TestCase):
    def test_bom_is_ignored(self):
        self.assertEqual(sdd.lint_delta("﻿" + DELTA.replace("status: approved", "status: draft"), "1234-limite-intentos"), [])


class MergeLayoutTests(unittest.TestCase):
    def test_added_goes_before_history_when_there_is_no_decisions_section(self):
        spec = SPEC.replace("## Decisiones\n\n- La saga decide si el código es correcto.\n\n", "")
        merged = sdd.merge(DELTA, spec, today="2026-11-02")
        self.assertLess(merged.index("### REQ-REG-004"), merged.index("## Historial"))

    def test_history_row_lands_inside_the_table_even_with_a_trailing_section(self):
        spec = SPEC + "\n## Notas\n\nAlgo al final.\n"
        merged = sdd.merge(DELTA, spec, today="2026-11-02")
        history = merged[merged.index("## Historial"):merged.index("## Notas")]
        self.assertIn("| 2026-11-02 | 1234 | Límite de intentos |", history)

    def test_spec_without_history_gets_one(self):
        spec = SPEC[: SPEC.index("## Historial")]
        merged = sdd.merge(DELTA, spec, today="2026-11-02")
        self.assertIn("## Historial\n\n| Fecha | PBI | Cambio |\n|---|---|---|\n| 2026-11-02 | 1234 | Límite de intentos |", merged)


class ScanCollisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_two_open_deltas_adding_the_same_id_are_reported(self):
        other = self.root / "docs" / "features" / "registro-usuario" / "changes" / "1400-otro"
        other.mkdir()
        (other / "delta.md").write_text(DELTA_OPEN.replace("1300", "1400").replace("Reenvío", "Otro"), encoding="utf-8")
        errors = sdd.scan(self.root / "docs")
        self.assertTrue(any("REQ-REG-003 lo añaden dos deltas abiertos" in e for e in errors), errors)

    def test_same_id_in_two_features_is_reported(self):
        noti = self.root / "docs" / "features" / "notificaciones" / "spec.md"
        noti.write_text(noti.read_text(encoding="utf-8").replace("REQ-NOT-001", "REQ-REG-001"), encoding="utf-8")
        errors = sdd.scan(self.root / "docs")
        self.assertTrue(any("REQ-REG-001 está en dos specs" in e for e in errors), errors)


class IndexWithoutCountsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(self.tmp.name)
        self.docs = self.root / "docs"

    def tearDown(self):
        self.tmp.cleanup()

    def test_requirement_index_has_no_file_count(self):
        reqs = sdd.build_index(self.docs)["REQ-INDEX.md"]
        self.assertIn("| REQ-REG-001 | Alta pendiente | registro-usuario |\n", reqs)
        self.assertNotIn("| Tests |", reqs)

    def test_check_passes_when_there_are_no_features_yet(self):
        with tempfile.TemporaryDirectory() as empty:
            (Path(empty) / "docs" / "features").mkdir(parents=True)
            self.assertEqual(sdd.check_index(Path(empty) / "docs"), [])


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(self.tmp.name)
        hidden = self.root / ".sdd-tooling" / "tests"
        hidden.mkdir(parents=True)
        (hidden / "test_x.py").write_text("REQ-NOT-001", encoding="utf-8")
        modules = self.root / "node_modules" / "pkg"
        modules.mkdir(parents=True)
        (modules / "index.js").write_text("REQ-NOT-001", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_uncovered_requirements_ignore_hidden_and_dependency_folders(self):
        self.assertEqual(sdd.uncovered(self.root / "docs"), ["REQ-NOT-001"])

    def test_mentions_use_word_boundaries(self):
        (self.root / "tests" / "Other.cs").write_text("// REQ-REG-0010\n", encoding="utf-8")
        mentions = sdd.mentions(self.root, {"REQ-REG-001", "REQ-REG-0010"}, sdd.default_settings())
        self.assertEqual(sorted(str(p.name) for p in mentions["REQ-REG-0010"]), ["Other.cs"])
        self.assertEqual(sorted(str(p.name) for p in mentions["REQ-REG-001"]), ["RegistrationTests.cs"])


class WhereBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_prefix_of_an_id_matches_nothing(self):
        report = sdd.where("REQ-REG-00", self.root / "docs")
        self.assertIn("REQ-REG-00 no está en ningún spec", report)
        self.assertNotIn("RegistrationTests.cs", report)

    def test_delta_that_only_mentions_the_id_in_prose_is_not_listed(self):
        change = self.root / "docs" / "features" / "registro-usuario" / "changes" / "1300-reenvio" / "delta.md"
        change.write_text(change.read_text(encoding="utf-8").replace("Se pierde.", "Se pierde, ver REQ-REG-001."), encoding="utf-8")
        report = sdd.where("REQ-REG-001", self.root / "docs")
        self.assertNotIn("1300", report)


class SelfServiceTests(unittest.TestCase):
    def test_files_outside_the_allowed_globs_are_listed(self):
        outside = sdd.outside_self_service(["docs/a.md", "src/Res/Strings.resx", "src/App.cs"], ["docs/**", "**/*.resx"])
        self.assertEqual(outside, ["src/App.cs"])

    def test_no_globs_means_everything_is_outside(self):
        self.assertEqual(sdd.outside_self_service(["docs/a.md"], []), ["docs/a.md"])


class LanguageSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(self.tmp.name)
        self.docs = self.root / "docs"

    def tearDown(self):
        self.tmp.cleanup()

    def test_defaults_cover_the_main_ecosystems(self):
        settings = sdd.default_settings()
        for ext in (".cs", ".ts", ".tsx", ".py", ".java", ".go", ".rs", ".vue"):
            self.assertIn(ext, settings.extensions)
        for folder in ("bin", "obj", "node_modules", "target", "vendor", ".next"):
            self.assertIn(folder, settings.skip_dirs)

    def test_active_language_packs_narrow_extensions(self):
        (self.root / "sdd.json").write_text(json.dumps({"languages": ["csharp"]}), encoding="utf-8")
        packs = self.root / "docs" / "sdd" / "languages"
        packs.mkdir(parents=True)
        (packs / "csharp.md").write_text("---\nname: csharp\nowner: equipo-backend\nextensions: .cs, .razor\nskipDirs: bin, obj, TestResults\n---\n# C#\n", encoding="utf-8")
        settings = sdd.load_settings(self.docs)
        self.assertEqual(settings.extensions, {".cs", ".razor"})
        self.assertIn("TestResults", settings.skip_dirs)
        self.assertIn("node_modules", settings.skip_dirs)

    def test_unknown_language_pack_is_reported(self):
        (self.root / "sdd.json").write_text(json.dumps({"languages": ["cobol"]}), encoding="utf-8")
        self.assertIn("paquete de lenguaje 'cobol' no encontrado (docs/sdd/languages/cobol.md ni en el plugin)", sdd.check_settings(self.docs))

    def test_pack_without_owner_is_reported(self):
        (self.root / "sdd.json").write_text(json.dumps({"languages": ["go"]}), encoding="utf-8")
        packs = self.root / "docs" / "sdd" / "languages"
        packs.mkdir(parents=True)
        (packs / "go.md").write_text("---\nname: go\nextensions: .go\n---\n", encoding="utf-8")
        self.assertIn("paquete de lenguaje 'go' sin owner", sdd.check_settings(self.docs))


if __name__ == "__main__":
    unittest.main()
