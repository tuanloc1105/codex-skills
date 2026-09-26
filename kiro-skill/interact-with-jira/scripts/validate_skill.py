#!/usr/bin/env python3
"""Check skill resources and local links; assess workflow behavior separately."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+)\)")
REQUIRED_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/mcp-workflows.md",
    "references/official-sources.md",
    "references/wowocb-metadata.md",
    "references/wowocb-metadata.json",
)


def heading_ids(text: str) -> set[str]:
    result: set[str] = set()
    for heading in re.findall(r"^#{1,6}\s+(.+)$", text, re.MULTILINE):
        slug = re.sub(r"[^\w\s-]", "", heading.lower()).replace(" ", "-")
        candidate = slug
        suffix = 0
        while candidate in result:
            suffix += 1
            candidate = f"{slug}-{suffix}"
        result.add(candidate)
    return result


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required resource: {relative}")

    obsolete = list((root / "references").glob("rest-*.md"))
    obsolete.extend((root / "references").glob("rest-*.json"))
    obsolete.extend(
        root / relative
        for relative in (
            "references/command-workflows.md",
            "scripts/validate_rest_registry.py",
        )
        if (root / relative).exists()
    )
    for path in obsolete:
        errors.append(f"obsolete fallback resource: {path.relative_to(root)}")

    for document in root.rglob("*.md"):
        for link in LINK_RE.findall(document.read_text()):
            if "://" in link or link.startswith("mailto:"):
                continue
            target, _, fragment = unquote(link).partition("#")
            path = (document.parent / target).resolve() if target else document
            label = f"{document.relative_to(root)}: {link}"
            if not path.is_file():
                errors.append(f"broken local link: {label}")
            elif fragment and path.suffix == ".md":
                if fragment not in heading_ids(path.read_text()):
                    errors.append(f"broken local heading link: {label}")
    return errors


def main() -> int:
    errors = validate(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated MCP skill resources and local links; workflow behavior needs scenario review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
