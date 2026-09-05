#!/usr/bin/env python3
"""Install the Workflow Modes Codex plugin on Windows, Linux, or macOS."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable


PLUGIN_NAME = "workflow-modes"
MARKETPLACE_NAME = "personal"
SKILL_NAMES = ("discuss", "plan", "execute")
REQUIRED_PATHS = (
    Path(".codex-plugin/plugin.json"),
    Path("hooks/hooks.json"),
    Path("scripts/workflow_modes_control.py"),
    Path("scripts/workflow_modes_hook.py"),
    Path("scripts/tool_policy.py"),
    Path("scripts/bundle_schema.py"),
)
EXCLUDED_DIRECTORIES = {".git", ".serena", "__pycache__"}
EXCLUDED_FILES = {".DS_Store"}


class InstallError(RuntimeError):
    """Raised when the plugin cannot be installed safely."""


@dataclass(frozen=True)
class BundleInstallResult:
    changed: bool
    backup: Path | None = None


def reject_symlinks(root: Path) -> None:
    for current_root, directories, files in os.walk(root, followlinks=False):
        current = Path(current_root)
        for name in (*directories, *files):
            if (current / name).is_symlink():
                raise InstallError(f"Plugin bundle must not contain symlinks: {current / name}")


def read_version(root: Path) -> str:
    path = root / ".codex-plugin" / "plugin.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InstallError(f"Cannot read plugin manifest {path}: {error}") from error
    if not isinstance(data, dict) or data.get("name") != PLUGIN_NAME:
        raise InstallError(f"Plugin manifest must declare name '{PLUGIN_NAME}'")
    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        raise InstallError("Plugin manifest must declare a non-empty version")
    return version


def validate_bundle(root: Path) -> None:
    missing = [str(path) for path in REQUIRED_PATHS if not (root / path).is_file()]
    if missing:
        raise InstallError(f"Incomplete plugin bundle at {root}. Missing: {', '.join(missing)}")
    reject_symlinks(root)
    read_version(root)


def validate_skill_bundle(root: Path, expected_name: str) -> None:
    if root.name != expected_name:
        raise InstallError(
            f"Skill source directory must be named '{expected_name}': {root}"
        )
    required = (root / "SKILL.md", root / "agents" / "openai.yaml")
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise InstallError(
            f"Incomplete {expected_name} skill bundle. Missing: {', '.join(missing)}"
        )
    reject_symlinks(root)


def ignored_entries(_directory: str, names: Iterable[str]) -> set[str]:
    return {
        name for name in names
        if name in EXCLUDED_DIRECTORIES
        or name in EXCLUDED_FILES
        or name.endswith((".pyc", ".pyo"))
    }


def fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root)
        if any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
            continue
        if path.name in EXCLUDED_FILES or path.name.endswith((".pyc", ".pyo")):
            continue
        if path.is_file():
            digest.update(relative.as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def backup_path(destination: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = destination.with_name(f"{destination.name}.backup-{stamp}")
    index = 1
    while candidate.exists():
        candidate = destination.with_name(f"{destination.name}.backup-{stamp}-{index}")
        index += 1
    return candidate


def install_bundle(source: Path, destination: Path) -> BundleInstallResult:
    source = source.resolve()
    destination = destination.expanduser().absolute()
    validate_bundle(source)
    if destination.is_symlink():
        raise InstallError(f"Plugin destination must not be a symlink: {destination}")
    if source == destination.resolve():
        return BundleInstallResult(changed=False)
    if destination.exists():
        reject_symlinks(destination)
        if fingerprint(source) == fingerprint(destination):
            return BundleInstallResult(changed=False)
        if read_version(source) == read_version(destination):
            raise InstallError(
                "Installed contents differ but use the same version. Update the manifest "
                "cachebuster before rerunning the installer."
            )

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(prefix=".workflow-modes-stage-", dir=destination.parent))
    staged = staging_root / PLUGIN_NAME
    backup: Path | None = None
    try:
        shutil.copytree(source, staged, ignore=ignored_entries, symlinks=False)
        validate_bundle(staged)
        if destination.exists():
            backup = backup_path(destination)
            os.replace(destination, backup)
        try:
            os.replace(staged, destination)
        except Exception:
            if backup and backup.exists() and not destination.exists():
                os.replace(backup, destination)
            raise
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
    return BundleInstallResult(changed=True, backup=backup)


def install_skill_bundle(
    source: Path, destination: Path, expected_name: str
) -> BundleInstallResult:
    source = source.resolve()
    destination = destination.expanduser().absolute()
    validate_skill_bundle(source, expected_name)
    if destination.is_symlink():
        raise InstallError(f"Skill destination must not be a symlink: {destination}")
    if source == destination.resolve():
        return BundleInstallResult(changed=False)
    if destination.exists():
        reject_symlinks(destination)
        if fingerprint(source) == fingerprint(destination):
            return BundleInstallResult(changed=False)

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(
        tempfile.mkdtemp(prefix=f".{expected_name}-stage-", dir=destination.parent)
    )
    staged = staging_root / expected_name
    backup: Path | None = None
    try:
        shutil.copytree(source, staged, ignore=ignored_entries, symlinks=False)
        validate_skill_bundle(staged, expected_name)
        if destination.exists():
            backup = backup_path(destination)
            os.replace(destination, backup)
        try:
            os.replace(staged, destination)
        except Exception:
            if backup and backup.exists() and not destination.exists():
                os.replace(backup, destination)
            raise
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
    return BundleInstallResult(changed=True, backup=backup)


def rollback_bundle(destination: Path, result: BundleInstallResult) -> None:
    if not result.changed:
        return
    if destination.is_dir():
        shutil.rmtree(destination)
    elif destination.exists() or destination.is_symlink():
        destination.unlink()
    if result.backup and result.backup.exists():
        os.replace(result.backup, destination)


def load_marketplace(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "name": MARKETPLACE_NAME,
            "interface": {"displayName": "Personal"},
            "plugins": [],
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InstallError(f"Cannot read marketplace {path}: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("plugins", []), list):
        raise InstallError(f"Marketplace {path} has an invalid structure")
    return data


def marketplace_entry() -> dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "source": {"source": "local", "path": f"./plugins/{PLUGIN_NAME}"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }


def updated_marketplace(data: dict[str, Any]) -> dict[str, Any]:
    updated = dict(data)
    updated.setdefault("name", MARKETPLACE_NAME)
    updated.setdefault("interface", {"displayName": "Personal"})
    plugins = [
        entry for entry in updated.get("plugins", [])
        if isinstance(entry, dict) and entry.get("name") != PLUGIN_NAME
    ]
    plugins.append(marketplace_entry())
    updated["plugins"] = plugins
    return updated


def write_json_atomically(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def find_codex(explicit: str | None) -> str:
    if explicit:
        candidate = Path(explicit).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        resolved = shutil.which(explicit)
        if resolved:
            return resolved
        raise InstallError(f"Codex CLI was not found at: {explicit}")
    for command in ("codex", "codex.exe", "codex.cmd"):
        resolved = shutil.which(command)
        if resolved:
            return resolved
    raise InstallError("Codex CLI was not found on PATH; use --codex PATH")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", metavar="PATH")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = Path(__file__).resolve().parents[1]
    destination = Path.home() / "plugins" / PLUGIN_NAME
    skills_source_root = source.parent
    skills_destination_root = Path.home() / ".codex" / "skills"
    marketplace_path = Path.home() / ".agents" / "plugins" / "marketplace.json"
    try:
        validate_bundle(source)
        skill_sources = {
            name: skills_source_root / name
            for name in SKILL_NAMES
        }
        for name, skill_source in skill_sources.items():
            validate_skill_bundle(skill_source, name)
        codex = find_codex(args.codex)
        marketplace = updated_marketplace(load_marketplace(marketplace_path))
        marketplace_name = marketplace.get("name")
        if not isinstance(marketplace_name, str) or not marketplace_name:
            raise InstallError("Marketplace name must be a non-empty string")
        if args.dry_run:
            print("Workflow Modes installer dry run passed.")
            print(f"  Source:      {source}")
            print(f"  Destination: {destination}")
            for name, skill_source in skill_sources.items():
                print(
                    f"  Skill {name}: {skill_source} -> "
                    f"{skills_destination_root / name}"
                )
            print(f"  Marketplace: {marketplace_path}")
            print(f"  Codex CLI:   {codex}")
            return 0

        bundle_result = install_bundle(source, destination)
        skill_results: dict[str, BundleInstallResult] = {}
        try:
            for name, skill_source in skill_sources.items():
                skill_results[name] = install_skill_bundle(
                    skill_source, skills_destination_root / name, name
                )
            write_json_atomically(marketplace_path, marketplace)
        except Exception:
            for name in reversed(SKILL_NAMES):
                result = skill_results.get(name)
                if result is not None:
                    rollback_bundle(skills_destination_root / name, result)
            rollback_bundle(destination, bundle_result)
            raise
        result = subprocess.run(
            [codex, "plugin", "add", f"{PLUGIN_NAME}@{marketplace_name}"],
            check=False,
        )
        if result.returncode != 0:
            raise InstallError(
                "Codex could not add the plugin. Files and marketplace entry are ready; "
                "fix the CLI error and rerun this installer."
            )
    except (InstallError, OSError) as error:
        print(f"Workflow Modes installation failed: {error}", file=sys.stderr)
        return 1

    print("Workflow Modes installed successfully.")
    print(f"  Plugin:      {destination}")
    for name in SKILL_NAMES:
        result = skill_results[name]
        suffix = f" (backup: {result.backup})" if result.backup else ""
        print(f"  Skill:       {skills_destination_root / name}{suffix}")
    print(f"  Marketplace: {marketplace_path}")
    if bundle_result.backup:
        print(f"  Backup:      {bundle_result.backup}")
    print("Next: open a new Codex task, run /hooks, review and trust the Workflow Modes hooks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
