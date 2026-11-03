"""SDD tooling: lint a delta, check it merges into its spec, merge and archive it, index and trace requirements.

Usage:
  python3 sdd.py lint  <delta.md>
  python3 sdd.py check <delta.md>            (spec.md is two folders up: <feature>/spec.md)
  python3 sdd.py merge <delta.md> [--date YYYY-MM-DD]
  python3 sdd.py scan  [docs-root]           lint + check every open delta, collisions between deltas, settings
  python3 sdd.py index [docs-root] [--check] write docs/features/INDEX.md, REQ-INDEX.md and CONTRACTS.md (or verify them)
  python3 sdd.py where <REQ-ID> [docs-root]  spec block, deltas, code files and commits that name a requirement
  python3 sdd.py coverage [docs-root]        requirements that no code file names
  python3 sdd.py selfservice [docs-root]     reads changed paths from stdin, prints those outside sdd.json selfService
  python3 sdd.py settings [docs-root]        validates sdd.json and the active language packs
Exit code 1 when something is wrong.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

STATUSES = ("draft", "approved", "implemented")
SECTIONS = ("ADDED", "MODIFIED", "REMOVED")
REQ_ID = re.compile(r"^REQ-[A-Z][A-Z0-9]*-\d{3}$")
REQ_HEADING = re.compile(r"^### (REQ-\S+)(.*)$", re.MULTILINE)
REMOVED_ITEM = re.compile(r"^- (REQ-\S+)(?:\s+.*)?$")
CONTRACT_LINE = re.compile(r"^(Publica|Consume):\s*(.+)$", re.MULTILINE)
HISTORY_ROW = re.compile(r"^\| (\d{4}-\d{2}-\d{2}) \|", re.MULTILINE)
INDEX_HEADER = "Generado por `sdd.py index`; no editar a mano.\n"
HISTORY_TABLE_HEADER = "| Fecha | PBI | Cambio |\n|---|---|---|\n"

DEFAULT_EXTENSIONS = {
    ".cs", ".fs", ".vb", ".razor", ".cshtml",
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte",
    ".py", ".java", ".kt", ".kts", ".scala", ".go", ".rs", ".rb", ".php", ".swift", ".dart",
    ".feature", ".sql", ".ps1", ".sh",
}
DEFAULT_SKIP_DIRS = {
    "bin", "obj", "TestResults", "node_modules", "dist", "build", "out", "coverage", "target", "vendor",
    "venv", "__pycache__", "packages",
    ".git", ".next", ".nuxt", ".svelte-kit", ".gradle", ".pytest_cache", ".mypy_cache", ".tox", ".venv", ".idea", ".vs",
}
PLUGIN_LANGUAGES = Path(__file__).resolve().parent.parent / "skills" / "sdd" / "references" / "languages"


class SddError(Exception):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


@dataclass
class Delta:
    frontmatter: dict[str, str]
    sections: dict[str, str] = field(default_factory=dict)

    def requirements(self, section: str) -> dict[str, str]:
        return split_requirements(self.sections.get(section, ""))

    def removed(self) -> list[str]:
        ids: list[str] = []
        for line in self.sections.get("REMOVED", "").splitlines():
            match = REMOVED_ITEM.match(line.strip())
            if match:
                ids.append(match.group(1))
        return ids

    def touches(self, req_id: str) -> bool:
        return req_id in self.requirements("ADDED") or req_id in self.requirements("MODIFIED") or req_id in self.removed()


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    data: dict[str, str] = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data, text[end + 4 :]


def split_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    for line in body.splitlines(keepends=True):
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = ""
        elif current is not None:
            sections[current] += line
    return sections


def split_requirements(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    boundaries = [match.start() for match in re.finditer(r"^##(?!#) ", text, re.MULTILINE)]
    matches = list(REQ_HEADING.finditer(text))
    for index, match in enumerate(matches):
        candidates = [len(text)] + [b for b in boundaries if b > match.start()]
        if index + 1 < len(matches):
            candidates.append(matches[index + 1].start())
        blocks[match.group(1)] = text[match.start() : min(candidates)].rstrip() + "\n"
    return blocks


def parse_delta(text: str) -> Delta:
    frontmatter, body = parse_frontmatter(text)
    return Delta(frontmatter, split_sections(body))


def lint_delta(text: str, folder_name: str) -> list[str]:
    errors: list[str] = []
    delta = parse_delta(text)
    for key in ("pbi", "title", "feature", "status"):
        if key not in delta.frontmatter:
            errors.append(f"frontmatter: falta '{key}'")
    status = delta.frontmatter.get("status")
    if status is not None and status not in STATUSES:
        errors.append(f"frontmatter: status '{status}' no es draft, approved ni implemented")
    if status in ("approved", "implemented") and not delta.frontmatter.get("approved_by"):
        errors.append("frontmatter: falta 'approved_by' (obligatorio cuando status no es draft)")
    pbi = delta.frontmatter.get("pbi")
    if pbi and not folder_name.startswith(f"{pbi}-"):
        errors.append(f"carpeta: '{folder_name}' debe empezar por el pbi {pbi}")
    for section in SECTIONS:
        if section not in delta.sections:
            errors.append(f"falta la sección {section}")

    ids_by_section: dict[str, set[str]] = {}
    for section in ("ADDED", "MODIFIED"):
        headings = REQ_HEADING.findall(delta.sections.get(section, ""))
        counts = Counter(req_id for req_id, _ in headings)
        for req_id, count in counts.items():
            if not REQ_ID.match(req_id):
                errors.append(f"{section}: '{req_id}' no cumple REQ-<AREA>-NNN")
            if count > 1:
                errors.append(f"{section}: {req_id} aparece dos veces")
        ids_by_section[section] = set(counts)
    removed: set[str] = set()
    for line in delta.sections.get("REMOVED", "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = REMOVED_ITEM.match(stripped)
        if not match:
            errors.append(f"REMOVED: '{stripped}' debe ser '- REQ-<AREA>-NNN [título]'")
            continue
        if not REQ_ID.match(match.group(1)):
            errors.append(f"REMOVED: '{match.group(1)}' no cumple REQ-<AREA>-NNN")
        removed.add(match.group(1))
    ids_by_section["REMOVED"] = removed
    for first, second in (("ADDED", "MODIFIED"), ("ADDED", "REMOVED"), ("MODIFIED", "REMOVED")):
        for req_id in sorted(ids_by_section[first] & ids_by_section[second]):
            errors.append(f"{req_id} está en {first} y {second} a la vez")
    return errors


def check_merge(delta_text: str, spec_text: str) -> list[str]:
    delta = parse_delta(delta_text)
    existing = split_requirements(spec_text)
    errors: list[str] = []
    for req_id in delta.requirements("ADDED"):
        if req_id in existing:
            errors.append(f"ADDED: {req_id} ya existe en el spec")
    for req_id in delta.requirements("MODIFIED"):
        if req_id not in existing:
            errors.append(f"MODIFIED: {req_id} no existe en el spec")
    for req_id in delta.removed():
        if req_id not in existing:
            errors.append(f"REMOVED: {req_id} no existe en el spec")
    return errors


def merge(delta_text: str, spec_text: str, today: str | None = None) -> str:
    problems = check_merge(delta_text, spec_text)
    if problems:
        raise SddError("; ".join(problems))
    delta = parse_delta(delta_text)
    today = today or date.today().isoformat()
    spec_text = spec_text.lstrip("﻿").replace("\r\n", "\n")

    for req_id, block in delta.requirements("MODIFIED").items():
        spec_text = spec_text.replace(split_requirements(spec_text)[req_id], block)
    for req_id in delta.removed():
        spec_text = spec_text.replace(split_requirements(spec_text)[req_id], "")
    added = "".join("\n" + block for block in delta.requirements("ADDED").values())
    if added:
        spec_text = insert_before_sections(spec_text, ("## Decisiones", "## Historial"), added)
    row_text = f"| {today} | {delta.frontmatter.get('pbi', '')} | {delta.frontmatter.get('title', '')} |"
    spec_text = append_history_row(spec_text, row_text)
    return re.sub(r"\n{3,}", "\n\n", spec_text)


def insert_before_sections(text: str, headings: tuple[str, ...], insertion: str) -> str:
    positions = [p for p in (text.find(f"\n{heading}") for heading in headings) if p >= 0]
    if not positions:
        return text.rstrip("\n") + "\n" + insertion
    index = min(positions)
    return text[:index].rstrip("\n") + "\n" + insertion + "\n" + text[index:]


def append_history_row(text: str, row_text: str) -> str:
    lines = text.split("\n")
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "## Historial")
    except StopIteration:
        return text.rstrip("\n") + "\n\n## Historial\n\n" + HISTORY_TABLE_HEADER + row_text + "\n"
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    table_rows = [i for i in range(start + 1, end) if lines[i].startswith("|")]
    if table_rows:
        lines.insert(table_rows[-1] + 1, row_text)
    else:
        lines[start + 1 : start + 1] = ["", *HISTORY_TABLE_HEADER.rstrip("\n").split("\n"), row_text]
    return "\n".join(lines)


def spec_path_for(delta_path: Path) -> Path:
    return delta_path.parent.parent.parent / "spec.md"


def merge_and_archive(delta_path: Path, today: str | None = None) -> Path:
    today = today or date.today().isoformat()
    delta_text = read_text(delta_path)
    delta = parse_delta(delta_text)
    if delta.frontmatter.get("status") not in ("approved", "implemented"):
        raise SddError(f"el delta está en '{delta.frontmatter.get('status')}'; solo se fusiona approved o implemented")
    spec_path = spec_path_for(delta_path)
    if not spec_path.exists():
        raise SddError(f"no existe {spec_path}")
    merged = merge(delta_text, read_text(spec_path), today)
    spec_path.write_text(merged, encoding="utf-8")
    change_dir = delta_path.parent
    archive = change_dir.parent / "archive" / f"{today}-{change_dir.name}"
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(change_dir), str(archive))
    write_index(spec_path.parent.parent.parent)
    return archive


@dataclass
class Feature:
    slug: str
    title: str
    path: Path
    requirements: dict[str, str]
    open_deltas: list[tuple[Path, Delta]]
    last_change: str


def load_features(docs: Path) -> list[Feature]:
    features: list[Feature] = []
    for spec_path in sorted((docs / "features").glob("*/spec.md")):
        text = read_text(spec_path)
        frontmatter, _ = parse_frontmatter(text)
        open_deltas = [
            (path, parse_delta(read_text(path)))
            for path in sorted(spec_path.parent.glob("changes/*/delta.md"))
            if "archive" not in path.parts
        ]
        dates = HISTORY_ROW.findall(text)
        features.append(Feature(
            slug=spec_path.parent.name,
            title=frontmatter.get("title", spec_path.parent.name),
            path=spec_path,
            requirements=split_requirements(text),
            open_deltas=open_deltas,
            last_change=max(dates) if dates else "",
        ))
    return features


def requirement_title(block: str) -> str:
    match = REQ_HEADING.match(block)
    return match.group(2).strip() if match else ""


def row(*cells: str) -> str:
    return "|" + "|".join(f" {cell} " if cell else " " for cell in cells) + "|"


@dataclass
class Settings:
    extensions: set[str]
    skip_dirs: set[str]
    languages: list[str] = field(default_factory=list)
    self_service: list[str] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


def default_settings() -> Settings:
    return Settings(extensions=set(DEFAULT_EXTENSIONS), skip_dirs=set(DEFAULT_SKIP_DIRS))


def split_list(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def find_language_pack(docs: Path, language: str) -> Path | None:
    for candidate in (docs / "sdd" / "languages" / f"{language}.md", PLUGIN_LANGUAGES / f"{language}.md"):
        if candidate.exists():
            return candidate
    return None


def load_settings(docs: Path) -> Settings:
    settings = default_settings()
    config = docs.parent / "sdd.json"
    if config.exists():
        try:
            settings.raw = json.loads(read_text(config))
        except json.JSONDecodeError as error:
            raise SddError(f"sdd.json no es JSON válido: {error}") from error
    settings.self_service = list(settings.raw.get("selfService", []))
    settings.languages = list(settings.raw.get("languages", []))
    extensions: set[str] = set()
    for language in settings.languages:
        pack = find_language_pack(docs, language)
        if pack is None:
            continue
        frontmatter, _ = parse_frontmatter(read_text(pack))
        extensions |= set(split_list(frontmatter.get("extensions")))
        settings.skip_dirs |= set(split_list(frontmatter.get("skipDirs")))
    if extensions:
        settings.extensions = extensions
    return settings


def check_settings(docs: Path) -> list[str]:
    config = docs.parent / "sdd.json"
    if not config.exists():
        return []
    try:
        raw = json.loads(read_text(config))
    except json.JSONDecodeError as error:
        return [f"sdd.json no es JSON válido: {error}"]
    errors: list[str] = []
    for language in raw.get("languages", []):
        pack = find_language_pack(docs, language)
        if pack is None:
            errors.append(f"paquete de lenguaje '{language}' no encontrado (docs/sdd/languages/{language}.md ni en el plugin)")
            continue
        frontmatter, _ = parse_frontmatter(read_text(pack))
        if not frontmatter.get("owner"):
            errors.append(f"paquete de lenguaje '{language}' sin owner")
        if not split_list(frontmatter.get("extensions")):
            errors.append(f"paquete de lenguaje '{language}' sin extensions")
    return errors


def describe_settings(settings: Settings) -> list[str]:
    return [
        "extensiones: " + " ".join(sorted(settings.extensions)),
        "carpetas saltadas: " + " ".join(sorted(settings.skip_dirs)),
    ]


def mentions(root: Path, ids: set[str], settings: Settings, docs: Path | None = None) -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {req_id: [] for req_id in ids}
    if not ids:
        return found
    docs_folder = (docs or root / "docs").resolve()
    alternatives = "|".join(re.escape(i).replace(r"\-", "[-_]") for i in sorted(ids, key=len, reverse=True))
    pattern = re.compile(r"(?<![A-Za-z0-9-])(" + alternatives + r")(?![0-9])", re.IGNORECASE)
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(
            d for d in dirs
            if d not in settings.skip_dirs and not d.startswith(".") and (Path(current) / d).resolve() != docs_folder
        )
        for name in sorted(files):
            path = Path(current) / name
            if path.suffix not in settings.extensions:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for req_id in {match.upper().replace("_", "-") for match in pattern.findall(text)}:
                found[req_id].append(path)
    return found


def uncovered(docs: Path) -> list[str]:
    ids = {req_id for f in load_features(docs) for req_id in f.requirements}
    found = mentions(docs.parent, ids, load_settings(docs), docs)
    return sorted(req_id for req_id, paths in found.items() if not paths)


def build_index(docs: Path) -> dict[str, str]:
    features = load_features(docs)

    rows = ["| Feature | Título | Requisitos | Deltas abiertos | Último cambio |", "|---|---|---|---|---|"]
    rows += [row(f.slug, f.title, str(len(f.requirements)), str(len(f.open_deltas)), f.last_change) for f in features]
    open_rows = ["| PBI | Título | Feature | Estado |", "|---|---|---|---|"]
    for f in features:
        open_rows += [row(d.frontmatter.get("pbi", ""), d.frontmatter.get("title", ""), f.slug, d.frontmatter.get("status", "")) for _, d in f.open_deltas]
    index = "# Índice de features\n\n" + INDEX_HEADER + "\n" + "\n".join(rows) + "\n"
    if len(open_rows) > 2:
        index += "\n## Deltas abiertos\n\n" + "\n".join(open_rows) + "\n"

    req_rows = ["| Requisito | Título | Feature |", "|---|---|---|"]
    contracts: dict[str, dict[str, list[str]]] = {}
    for f in features:
        for req_id, block in f.requirements.items():
            req_rows.append(row(req_id, requirement_title(block), f.slug))
            for kind, names in CONTRACT_LINE.findall(block):
                for name in split_list(names):
                    contracts.setdefault(name, {"Publica": [], "Consume": []})[kind].append(f"{req_id} ({f.slug})")
    req_index = (
        "# Índice de requisitos\n\n" + INDEX_HEADER
        + "\nQué ficheros nombran cada requisito: `sdd.py where <REQ>`; requisitos sin ningún fichero: `sdd.py coverage`.\n\n"
        + "\n".join(req_rows) + "\n"
    )

    result = {"INDEX.md": index, "REQ-INDEX.md": req_index}
    if contracts:
        contract_rows = ["| Mensaje | Publica | Consume |", "|---|---|---|"]
        contract_rows += [row(name, ", ".join(c["Publica"]), ", ".join(c["Consume"])) for name, c in sorted(contracts.items())]
        result["CONTRACTS.md"] = "# Contratos entre features\n\n" + INDEX_HEADER + "\nLíneas `Publica:` y `Consume:` de los requisitos.\n\n" + "\n".join(contract_rows) + "\n"
    return result


def write_index(docs: Path) -> list[Path]:
    written: list[Path] = []
    (docs / "features").mkdir(parents=True, exist_ok=True)
    for name, content in build_index(docs).items():
        path = docs / "features" / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def check_index(docs: Path) -> list[str]:
    if not load_features(docs):
        return []
    problems: list[str] = []
    for name, content in build_index(docs).items():
        path = docs / "features" / name
        shown = f"{docs.name}/features/{name}"
        if not path.exists():
            problems.append(f"{shown} no existe: ejecuta sdd.py index")
        elif read_text(path).replace("\r\n", "\n") != content:
            problems.append(f"{shown} desactualizado: ejecuta sdd.py index")
    return problems


def where(req_id: str, docs: Path) -> str:
    root = docs.parent
    def rel(p: Path) -> str:
        return str(p.relative_to(root)).replace("\\", "/")

    lines: list[str] = []
    owner = next((f for f in load_features(docs) if req_id in f.requirements), None)
    if owner is None:
        lines.append(f"{req_id} no está en ningún spec de {rel(docs / 'features')}")
    else:
        lines.append(f"Spec: {rel(owner.path)}")
        lines.append(owner.requirements[req_id].rstrip())

    deltas = []
    for path in sorted((docs / "features").rglob("changes/**/delta.md")):
        delta = parse_delta(read_text(path))
        if delta.touches(req_id):
            state = "archive" if "archive" in path.parts else delta.frontmatter.get("status", "")
            deltas.append(f"  {delta.frontmatter.get('pbi', '')} {delta.frontmatter.get('title', '')} [{state}] {rel(path)}")
    lines.append("\nDeltas:" if deltas else "\nDeltas: ninguno")
    lines += deltas

    files = [f"  {rel(p)}" for p in mentions(root, {req_id}, load_settings(docs), docs)[req_id]]
    lines.append("\nCódigo y tests que lo nombran:" if files else "\nCódigo y tests que lo nombran: ninguno")
    lines += files

    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "--perl-regexp", f"--grep={re.escape(req_id)}(?![0-9])"],
            cwd=root, capture_output=True, text=True, check=False,
        ).stdout.strip()
    except OSError:
        log = ""
    lines.append("\nCommits:" if log else "\nCommits: ninguno")
    lines += [f"  {line}" for line in log.splitlines()]
    return "\n".join(lines)


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    parts: list[str] = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            parts.append("(?:.*/)?")
            index += 3
        elif pattern.startswith("**", index):
            parts.append(".*")
            index += 2
        elif pattern[index] == "*":
            parts.append("[^/]*")
            index += 1
        elif pattern[index] == "?":
            parts.append("[^/]")
            index += 1
        else:
            parts.append(re.escape(pattern[index]))
            index += 1
    return re.compile("".join(parts) + r"\Z")


def outside_self_service(files: list[str], globs: list[str]) -> list[str]:
    patterns = [glob_to_regex(g.replace("\\", "/")) for g in globs]
    return [f for f in files if not any(p.match(f.replace("\\", "/")) for p in patterns)]


def scan(root: Path) -> list[str]:
    errors: list[str] = []
    added: dict[str, list[Path]] = {}
    modified: dict[str, list[Path]] = {}
    for delta_path in sorted(root.rglob("changes/*/delta.md")):
        if "archive" in delta_path.parts:
            continue
        text = read_text(delta_path)
        found = lint_delta(text, delta_path.parent.name)
        spec_path = spec_path_for(delta_path)
        if spec_path.exists():
            found += check_merge(text, read_text(spec_path))
        else:
            found.append(f"no existe {spec_path}")
        errors += [f"{delta_path}: {problem}" for problem in found]
        delta = parse_delta(text)
        for req_id in delta.requirements("ADDED"):
            added.setdefault(req_id, []).append(delta_path)
        for req_id in delta.requirements("MODIFIED"):
            modified.setdefault(req_id, []).append(delta_path)
    for req_id, paths in sorted(added.items()):
        if len(paths) > 1:
            errors.append(f"{req_id} lo añaden dos deltas abiertos: " + ", ".join(str(p) for p in paths))
    for req_id, paths in sorted(modified.items()):
        if len(paths) > 1:
            errors.append(f"{req_id} lo modifican dos deltas abiertos: " + ", ".join(str(p) for p in paths))
    owners: dict[str, list[str]] = {}
    if (root / "features").exists():
        for feature in load_features(root):
            for req_id in feature.requirements:
                owners.setdefault(req_id, []).append(feature.slug)
    for req_id, slugs in sorted(owners.items()):
        if len(slugs) > 1:
            errors.append(f"{req_id} está en dos specs: " + ", ".join(slugs))
    errors += check_settings(root)
    return errors


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    commands = ("lint", "check", "merge", "scan", "index", "where", "coverage", "selfservice", "settings")
    if len(argv) < 2 or argv[1] not in commands:
        print(__doc__)
        return 2
    command = argv[1]
    positional = [a for a in argv[2:] if not a.startswith("--")]
    if command == "where":
        docs = Path(positional[1]) if len(positional) > 1 else Path("docs")
    else:
        docs = Path(positional[0]) if positional else Path("docs")
    try:
        if command == "scan":
            errors = scan(docs)
        elif command == "index":
            if "--check" in argv:
                errors = check_index(docs)
            else:
                for path in write_index(docs):
                    print(f"escrito {path}")
                return 0
        elif command == "where":
            if not positional:
                print("falta el id del requisito")
                return 2
            print(where(positional[0], docs))
            return 0
        elif command == "coverage":
            errors = [f"{req_id} sin ningún fichero de código que lo nombre" for req_id in uncovered(docs)]
        elif command == "selfservice":
            files = [line.strip() for line in sys.stdin.read().splitlines() if line.strip()]
            errors = [f"fuera de selfService: {f}" for f in outside_self_service(files, load_settings(docs).self_service)]
        elif command == "settings":
            errors = check_settings(docs)
            if not errors:
                print("\n".join(describe_settings(load_settings(docs))))
        else:
            delta_path = Path(argv[2])
            text = read_text(delta_path)
            if command == "lint":
                errors = lint_delta(text, delta_path.parent.name)
            elif command == "check":
                errors = check_merge(text, read_text(spec_path_for(delta_path)))
            else:
                today = argv[argv.index("--date") + 1] if "--date" in argv else None
                archive = merge_and_archive(delta_path, today)
                print(f"fusionado en {spec_path_for(delta_path)} y archivado en {archive}")
                return 0
    except (SddError, OSError) as error:
        print(f"error: {error}")
        return 1
    for error in errors:
        print(error)
    print("ok" if not errors else f"{len(errors)} problema(s)")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
