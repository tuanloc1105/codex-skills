#!/usr/bin/env python3
"""Resolve the writable source of truth for repository agent docs."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


INCLUDE_RE = re.compile(r"^@(?P<path>\S+)\s*$")


def resolve_include(path_text: str, source_path: Path) -> Path:
    include_path = Path(path_text).expanduser()
    if include_path.is_absolute():
        return include_path.resolve()
    return (source_path.parent / include_path).resolve()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def single_include_target(source_path: Path) -> tuple[str, Path] | None:
    if not source_path.exists() or not source_path.is_file():
        return None

    non_empty_lines = [line.strip() for line in read_text(source_path).splitlines() if line.strip()]
    if len(non_empty_lines) != 1:
        return None

    match = INCLUDE_RE.match(non_empty_lines[0])
    if not match:
        return None

    target_path = resolve_include(match.group("path"), source_path)
    if target_path.is_symlink():
        target_path = target_path.resolve()
    return non_empty_lines[0], target_path


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def with_repo_boundary(result: dict[str, object], repo_root: Path) -> dict[str, object]:
    target_path = Path(str(result["target_path"]))
    inside_repo = is_relative_to(target_path, repo_root)
    result["target_inside_repo"] = inside_repo
    result["requires_confirmation"] = not inside_repo
    if not inside_repo:
        result["warning"] = "Resolved target is outside the repository; get explicit user confirmation before editing it."
    return result


def classify_agents_file(repo_root: Path) -> dict[str, object]:
    agents_path = repo_root / "AGENTS.md"

    if not agents_path.exists() and not agents_path.is_symlink():
        return with_repo_boundary({
            "mode": "create",
            "agents_path": str(agents_path),
            "target_path": str(agents_path),
            "target_exists": False,
            "reason": "AGENTS.md does not exist; create it at the repository root.",
        }, repo_root)

    if agents_path.is_symlink():
        symlink_target = agents_path.resolve()
        include = single_include_target(symlink_target)
        if include:
            include_line, include_target = include
            return with_repo_boundary({
                "mode": "symlink_single_include",
                "agents_path": str(agents_path),
                "intermediate_path": str(symlink_target),
                "target_path": str(include_target),
                "target_exists": include_target.exists(),
                "include": include_line,
                "reason": "AGENTS.md is a symlink to a single @include file; edit the included file.",
            }, repo_root)

        return with_repo_boundary({
            "mode": "symlink",
            "agents_path": str(agents_path),
            "target_path": str(symlink_target),
            "target_exists": symlink_target.exists(),
            "reason": "AGENTS.md is a symlink; edit the resolved target.",
        }, repo_root)

    content = read_text(agents_path)

    non_empty_lines = [line.strip() for line in content.splitlines() if line.strip()]
    include = single_include_target(agents_path)
    if include:
        include_line, target_path = include
        return with_repo_boundary({
            "mode": "single_include",
            "agents_path": str(agents_path),
            "target_path": str(target_path),
            "target_exists": target_path.exists(),
            "include": include_line,
            "reason": "AGENTS.md contains a single @include directive; edit the included file.",
        }, repo_root)

    include_lines = [line for line in non_empty_lines if INCLUDE_RE.match(line)]
    if include_lines:
        first_target = resolve_include(INCLUDE_RE.match(include_lines[0]).group("path"), agents_path)
        return with_repo_boundary({
            "mode": "mixed_include",
            "agents_path": str(agents_path),
            "target_path": str(agents_path),
            "suggested_include_target": str(first_target),
            "target_exists": agents_path.exists(),
            "include_count": len(include_lines),
            "reason": "AGENTS.md contains @include-style lines plus other content; inspect before choosing the source of truth.",
        }, repo_root)

    return with_repo_boundary({
        "mode": "direct",
        "agents_path": str(agents_path),
        "target_path": str(agents_path),
        "target_exists": True,
        "reason": "AGENTS.md is a regular documentation file; edit it directly.",
    }, repo_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", default=os.getcwd(), help="Repository root containing AGENTS.md")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    result = classify_agents_file(repo_root)
    result["repo_root"] = str(repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
