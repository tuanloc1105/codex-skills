#!/usr/bin/env python3
"""Resolve the writable source of truth for a repository's Kiro steering docs.

Kiro (unlike Codex's single-file AGENTS.md convention) loads every Markdown file
under ``.kiro/steering/`` for a session scoped to that project. This resolver finds
(or proposes) the one file that should act as the top-level routing index, while
treating a root ``AGENTS.md``/``CLAUDE.md`` as read-only migration input rather than
an editable target, since Kiro sessions do not load those automatically.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


ROUTING_MARKERS = ("## Start Here", "## Task Routing", "## Read On Demand")
DEFAULT_STEERING_NAME = "00-project-guide.md"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def find_existing_routing_file(steering_dir: Path) -> Path | None:
    if not steering_dir.is_dir():
        return None
    candidates = sorted(p for p in steering_dir.rglob("*.md") if p.is_file())
    for candidate in candidates:
        content = read_text(candidate)
        if any(marker in content for marker in ROUTING_MARKERS):
            return candidate
    return None


def find_legacy_agent_docs(repo_root: Path) -> list[str]:
    legacy_names = [
        "AGENTS.md",
        "CLAUDE.md",
        "CLAUDE.local.md",
        ".cursorrules",
        ".windsurfrules",
        ".clinerules",
        "GEMINI.md",
    ]
    found = []
    for name in legacy_names:
        candidate = repo_root / name
        if candidate.exists():
            found.append(str(candidate))
    for legacy_dir in (".cursor/rules", ".github", ".devin/rules", ".windsurf/rules", ".gemini"):
        candidate = repo_root / legacy_dir
        if candidate.exists():
            found.append(str(candidate))
    return found


def with_repo_boundary(result: dict[str, object], repo_root: Path) -> dict[str, object]:
    target_path = Path(str(result["target_path"]))
    inside_repo = is_relative_to(target_path, repo_root)
    result["target_inside_repo"] = inside_repo
    result["requires_confirmation"] = not inside_repo
    if not inside_repo:
        result["warning"] = "Resolved target is outside the repository; get explicit user confirmation before editing it."
    return result


def resolve_steering_target(repo_root: Path) -> dict[str, object]:
    steering_dir = repo_root / ".kiro" / "steering"
    existing = find_existing_routing_file(steering_dir)
    legacy_docs = find_legacy_agent_docs(repo_root)

    if existing is not None:
        return with_repo_boundary({
            "mode": "refresh_existing_steering",
            "steering_dir": str(steering_dir),
            "target_path": str(existing),
            "target_exists": True,
            "legacy_agent_docs_found": legacy_docs,
            "reason": "Found an existing routing-shaped file under .kiro/steering/; refresh it in place.",
        }, repo_root)

    default_target = steering_dir / DEFAULT_STEERING_NAME
    return with_repo_boundary({
        "mode": "create_steering",
        "steering_dir": str(steering_dir),
        "target_path": str(default_target),
        "target_exists": default_target.exists(),
        "legacy_agent_docs_found": legacy_docs,
        "reason": (
            ".kiro/steering/ has no routing-shaped file yet; create "
            f"{DEFAULT_STEERING_NAME} as the top-level routing index."
            if not legacy_docs
            else (
                ".kiro/steering/ has no routing-shaped file yet; create "
                f"{DEFAULT_STEERING_NAME} as the routing index, and treat the found legacy "
                "agent-doc files as migration input (read-only, do not edit them as the target)."
            )
        ),
    }, repo_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", default=os.getcwd(), help="Repository root to resolve steering docs for")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    result = resolve_steering_target(repo_root)
    result["repo_root"] = str(repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
