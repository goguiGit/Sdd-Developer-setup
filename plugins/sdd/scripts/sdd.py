"""SDD tooling: lint a delta, check it merges into its spec, merge and archive it.

Usage:
  python sdd.py lint  <delta.md>
  python sdd.py check <delta.md>            (spec.md is two folders up: <feature>/spec.md)
  python sdd.py merge <delta.md> [--date YYYY-MM-DD]
  python sdd.py scan  [docs-root]           lint + check every changes/*/delta.md (archive excluded)
  python sdd.py index [docs-root] [--check] write docs/features/INDEX.md, REQ-INDEX.md and CONTRACTS.md (or verify them)
  python sdd.py where <REQ-ID> [docs-root]  spec block, deltas, tests and commits that mention a requirement
Exit code 1 when something is wrong.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

INDEX_HEADER = "Generado por `sdd.py index`; no editar a mano.\n"
CODE_EXTENSIONS = {".cs", ".ts", ".tsx", ".js", ".py", ".java", ".kt", ".go", ".rb", ".php", ".feature", ".sql", ".ps1", ".sh"}
SKIP_DIRS = {".git", "bin", "obj", "node_modules", "dist", ".venv", "__pycache__", ".idea", ".vs"}
CONTRACT_LINE = re.compile(r"^(Publica|Consume):\s*(.+)$", re.MULTILINE)
HISTORY_ROW = re.compile(r"^\| (\d{4}-\d{2}-\d{2}) \|", re.MULTILINE)

STATUSES = ("draft", "approved", "implemented")
SECTIONS = ("ADDED", "MODIFIED", "REMOVED")
REQ_ID = re.compile(r"^REQ-[A-Z][A-Z0-9]*-\d{3}$")
REQ_HEADING = re.compile(r"^### (REQ-\S+)(.*)$", re.MULTILINE)
REMOVED_ITEM = re.compile(r"^- (REQ-\S+)\s*$", re.MULTILINE)


class SddError(Exception):
    pass


@dataclass
class Delta:
    frontmatter: dict[str, str]
    sections: dict[str, str] = field(default_factory=dict)

    def requirements(self, section: str) -> dict[str, str]:
        return split_requirements(self.sections.get(section, ""))

    def removed(self) -> list[str]:
        return REMOVED_ITEM.findall(self.sections.get("REMOVED", ""))


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
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
    """Maps each REQ id to its full block (heading included), in order of appearance."""
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
    pbi = delta.frontmatter.get("pbi")
    if pbi and not folder_name.startswith(f"{pbi}-"):
        errors.append(f"carpeta: '{folder_name}' debe empezar por el pbi {pbi}")
    for section in SECTIONS:
        if section not in delta.sections:
            errors.append(f"falta la sección {section}")
    for section in ("ADDED", "MODIFIED"):
        for req_id in delta.requirements(section):
            if not REQ_ID.match(req_id):
                errors.append(f"{section}: '{req_id}' no cumple REQ-<AREA>-NNN")
    for req_id in delta.removed():
        if not REQ_ID.match(req_id):
            errors.append(f"REMOVED: '{req_id}' no cumple REQ-<AREA>-NNN")
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

    for req_id, block in delta.requirements("MODIFIED").items():
        spec_text = spec_text.replace(split_requirements(spec_text)[req_id], block)
    for req_id in delta.removed():
        spec_text = spec_text.replace(split_requirements(spec_text)[req_id], "")
    added = "".join("\n" + block for block in delta.requirements("ADDED").values())
    if added:
        spec_text = insert_before_section(spec_text, "## Decisiones", added)
    row = f"| {today} | {delta.frontmatter.get('pbi', '')} | {delta.frontmatter.get('title', '')} |\n"
    spec_text = spec_text.rstrip("\n") + "\n" + row
    return re.sub(r"\n{3,}", "\n\n", spec_text)


def insert_before_section(text: str, heading: str, insertion: str) -> str:
    index = text.find(f"\n{heading}")
    if index < 0:
        return text.rstrip("\n") + "\n" + insertion
    return text[:index].rstrip("\n") + "\n" + insertion + "\n" + text[index:]


def spec_path_for(delta_path: Path) -> Path:
    return delta_path.parent.parent.parent / "spec.md"


def merge_and_archive(delta_path: Path, today: str | None = None) -> Path:
    today = today or date.today().isoformat()
    delta_text = delta_path.read_text(encoding="utf-8")
    delta = parse_delta(delta_text)
    if delta.frontmatter.get("status") not in ("approved", "implemented"):
        raise SddError(f"el delta está en '{delta.frontmatter.get('status')}'; solo se fusiona approved o implemented")
    spec_path = spec_path_for(delta_path)
    if not spec_path.exists():
        raise SddError(f"no existe {spec_path}")
    merged = merge(delta_text, spec_path.read_text(encoding="utf-8"), today)
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
    open_deltas: list[Delta]
    last_change: str


def load_features(docs: Path) -> list[Feature]:
    features: list[Feature] = []
    for spec_path in sorted((docs / "features").glob("*/spec.md")):
        text = spec_path.read_text(encoding="utf-8")
        frontmatter, _ = parse_frontmatter(text)
        open_deltas = [
            parse_delta(path.read_text(encoding="utf-8"))
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


def row(*cells: str) -> str:
    return "|" + "|".join(f" {cell} " if cell else " " for cell in cells) + "|"


def requirement_title(block: str) -> str:
    match = REQ_HEADING.match(block)
    return match.group(2).strip() if match else ""


def code_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in CODE_EXTENSIONS and not (SKIP_DIRS & set(path.parts)) and "docs" not in path.parts:
            yield path


def files_mentioning(root: Path, needle: str) -> list[Path]:
    found: list[Path] = []
    for path in code_files(root):
        try:
            if needle in path.read_text(encoding="utf-8", errors="ignore"):
                found.append(path)
        except OSError:
            continue
    return found


def build_index(docs: Path) -> dict[str, str]:
    features = load_features(docs)
    root = docs.parent

    rows = ["| Feature | Título | Requisitos | Deltas abiertos | Último cambio |", "|---|---|---|---|---|"]
    rows += [f"| {f.slug} | {f.title} | {len(f.requirements)} | {len(f.open_deltas)} | {f.last_change} |" for f in features]
    open_rows = ["| PBI | Título | Feature | Estado |", "|---|---|---|---|"]
    for f in features:
        open_rows += [f"| {d.frontmatter.get('pbi', '')} | {d.frontmatter.get('title', '')} | {f.slug} | {d.frontmatter.get('status', '')} |" for d in f.open_deltas]
    index = "# Índice de features\n\n" + INDEX_HEADER + "\n" + "\n".join(rows) + "\n"
    if len(open_rows) > 2:
        index += "\n## Deltas abiertos\n\n" + "\n".join(open_rows) + "\n"

    req_rows = ["| Requisito | Título | Feature | Tests |", "|---|---|---|---|"]
    contracts: dict[str, dict[str, list[str]]] = {}
    for f in features:
        for req_id, block in f.requirements.items():
            tests = len(files_mentioning(root, req_id))
            req_rows.append(f"| {req_id} | {requirement_title(block)} | {f.slug} | {tests} |")
            for kind, names in CONTRACT_LINE.findall(block):
                for name in (n.strip() for n in names.split(",") if n.strip()):
                    entry = contracts.setdefault(name, {"Publica": [], "Consume": []})
                    entry[kind].append(f"{req_id} ({f.slug})")
    req_index = "# Índice de requisitos\n\n" + INDEX_HEADER + "\n" + "\n".join(req_rows) + "\n"

    result = {"INDEX.md": index, "REQ-INDEX.md": req_index}
    if contracts:
        contract_rows = ["| Mensaje | Publica | Consume |", "|---|---|---|"]
        contract_rows += [row(name, ", ".join(c["Publica"]), ", ".join(c["Consume"])) for name, c in sorted(contracts.items())]
        result["CONTRACTS.md"] = "# Contratos entre features\n\n" + INDEX_HEADER + "\nLíneas `Publica:` y `Consume:` de los requisitos.\n\n" + "\n".join(contract_rows) + "\n"
    return result


def write_index(docs: Path) -> list[Path]:
    written: list[Path] = []
    for name, content in build_index(docs).items():
        path = docs / "features" / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def check_index(docs: Path) -> list[str]:
    problems: list[str] = []
    for name, content in build_index(docs).items():
        path = docs / "features" / name
        shown = f"{docs.name}/features/{name}"
        if not path.exists():
            problems.append(f"{shown} no existe: ejecuta sdd.py index")
        elif path.read_text(encoding="utf-8").replace("\r\n", "\n") != content:
            problems.append(f"{shown} desactualizado: ejecuta sdd.py index")
    return problems


def where(req_id: str, docs: Path) -> str:
    root = docs.parent
    rel = lambda p: str(p.relative_to(root)).replace("\\", "/")  # noqa: E731
    lines: list[str] = []
    owner = next((f for f in load_features(docs) if req_id in f.requirements), None)
    if owner is None:
        lines.append(f"{req_id} no está en ningún spec de {rel(docs / 'features')}")
    else:
        lines.append(f"Spec: {rel(owner.path)}")
        lines.append(owner.requirements[req_id].rstrip())

    deltas = []
    for path in sorted((docs / "features").rglob("changes/**/delta.md")):
        if req_id in path.read_text(encoding="utf-8"):
            delta = parse_delta(path.read_text(encoding="utf-8"))
            state = "archive" if "archive" in path.parts else delta.frontmatter.get("status", "")
            deltas.append(f"  {delta.frontmatter.get('pbi', '')} {delta.frontmatter.get('title', '')} [{state}] {rel(path)}")
    lines.append("\nDeltas:" if deltas else "\nDeltas: ninguno")
    lines += deltas

    tests = [f"  {rel(p)}" for p in files_mentioning(root, req_id)]
    lines.append("\nCódigo y tests que lo nombran:" if tests else "\nCódigo y tests que lo nombran: ninguno")
    lines += tests

    try:
        log = subprocess.run(["git", "log", "--oneline", f"--grep={req_id}"], cwd=root, capture_output=True, text=True, check=False).stdout.strip()
    except OSError:
        log = ""
    lines.append("\nCommits:" if log else "\nCommits: ninguno")
    lines += [f"  {line}" for line in log.splitlines()]
    return "\n".join(lines)


def scan(root: Path) -> list[str]:
    errors: list[str] = []
    for delta_path in sorted(root.rglob("changes/*/delta.md")):
        if "archive" in delta_path.parts:
            continue
        text = delta_path.read_text(encoding="utf-8")
        found = lint_delta(text, delta_path.parent.name)
        spec_path = spec_path_for(delta_path)
        if spec_path.exists():
            found += check_merge(text, spec_path.read_text(encoding="utf-8"))
        else:
            found.append(f"no existe {spec_path}")
        errors += [f"{delta_path}: {problem}" for problem in found]
    return errors


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) < 2 or argv[1] not in ("lint", "check", "merge", "scan", "index", "where"):
        print(__doc__)
        return 2
    command = argv[1]
    positional = [a for a in argv[2:] if not a.startswith("--")]
    try:
        if command == "scan":
            errors = scan(Path(positional[0] if positional else "docs"))
        elif command == "index":
            docs = Path(positional[0] if positional else "docs")
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
            print(where(positional[0], Path(positional[1] if len(positional) > 1 else "docs")))
            return 0
        else:
            delta_path = Path(argv[2])
            text = delta_path.read_text(encoding="utf-8")
            if command == "lint":
                errors = lint_delta(text, delta_path.parent.name)
            elif command == "check":
                errors = check_merge(text, spec_path_for(delta_path).read_text(encoding="utf-8"))
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
