"""SDD tooling: lint a delta, check it merges into its spec, merge and archive it.

Usage:
  python sdd.py lint  <delta.md>
  python sdd.py check <delta.md>            (spec.md is two folders up: <feature>/spec.md)
  python sdd.py merge <delta.md> [--date YYYY-MM-DD]
  python sdd.py scan  [docs-root]           lint + check every changes/*/delta.md (archive excluded)
Exit code 1 when something is wrong.
"""

from __future__ import annotations

import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

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
    return archive


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
    if len(argv) < 2 or argv[1] not in ("lint", "check", "merge", "scan"):
        print(__doc__)
        return 2
    command = argv[1]
    try:
        if command == "scan":
            errors = scan(Path(argv[2] if len(argv) > 2 else "docs"))
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
