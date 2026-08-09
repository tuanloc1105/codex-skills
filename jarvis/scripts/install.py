#!/usr/bin/env python3
"""Install the Jarvis Codex plugin on Windows, Linux, or macOS."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


PLUGIN_NAME = "jarvis"
DEFAULT_MARKETPLACE_NAME = "personal"
REQUIRED_PATHS = (
    Path(".codex-plugin/plugin.json"),
    Path("hooks/hooks.json"),
    Path("scripts/jarvis_control.py"),
    Path("scripts/jarvis_hook.py"),
    Path("skills/jarvis/SKILL.md"),
    Path("skills/jarvis/agents/openai.yaml"),
    Path("skills/jarvis/references/supervisor-prompt.md"),
)
EXCLUDED_DIRECTORIES = {".git", ".serena", "__pycache__"}
EXCLUDED_FILES = {".DS_Store"}


class InstallError(RuntimeError):
    """Raised when Jarvis cannot be installed safely."""


@dataclass(frozen=True)
class BundleInstallResult:
    changed: bool
    backup: Optional[Path] = None


def reject_symlinks(root: Path) -> None:
    """Reject links so the copied bundle is self-contained and Windows-safe."""
    for current_root, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current_root)
        for name in (*directory_names, *file_names):
            path = current_path / name
            if path.is_symlink():
                raise InstallError(f"Jarvis bundle must not contain symlinks: {path}")


def validate_bundle(root: Path) -> None:
    """Verify that a directory contains the complete Jarvis plugin bundle."""
    missing = [str(path) for path in REQUIRED_PATHS if not (root / path).is_file()]
    if missing:
        raise InstallError(
            f"Jarvis bundle is incomplete at {root}. Missing: {', '.join(missing)}"
        )
    reject_symlinks(root)


def ignored_bundle_entries(_directory: str, names: Iterable[str]) -> set[str]:
    """Return generated or local-only entries that must not be distributed."""
    return {
        name
        for name in names
        if name in EXCLUDED_DIRECTORIES
        or name in EXCLUDED_FILES
        or name.endswith((".pyc", ".pyo"))
    }


def backup_path_for(path: Path) -> Path:
    """Choose a non-conflicting, human-readable backup path."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = path.with_name(f"{path.name}.backup-{stamp}")
    suffix = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.backup-{stamp}-{suffix}")
        suffix += 1
    return candidate


def install_bundle(source: Path, destination: Path) -> BundleInstallResult:
    """Atomically replace the installed plugin and retain the previous copy."""
    source = source.resolve()
    destination = destination.expanduser().absolute()
    validate_bundle(source)

    if destination.is_symlink():
        raise InstallError(f"Jarvis destination must not be a symlink: {destination}")
    if source == destination.resolve():
        return BundleInstallResult(changed=False)

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(
        tempfile.mkdtemp(prefix=".jarvis-stage-", dir=str(destination.parent))
    )
    staged_bundle = staging_root / PLUGIN_NAME
    backup: Optional[Path] = None

    try:
        shutil.copytree(
            source,
            staged_bundle,
            ignore=ignored_bundle_entries,
            symlinks=False,
        )
        validate_bundle(staged_bundle)

        if destination.exists():
            backup = backup_path_for(destination)
            os.replace(destination, backup)

        try:
            os.replace(staged_bundle, destination)
        except Exception:
            if backup is not None and backup.exists() and not destination.exists():
                os.replace(backup, destination)
            raise
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)

    return BundleInstallResult(changed=True, backup=backup)


def rollback_bundle(destination: Path, result: BundleInstallResult) -> None:
    """Restore the pre-install bundle after a local transaction failure."""
    if not result.changed:
        return
    if destination.is_dir():
        shutil.rmtree(destination)
    elif destination.exists() or destination.is_symlink():
        destination.unlink()
    if result.backup is not None and result.backup.exists():
        os.replace(result.backup, destination)


def load_marketplace(path: Path) -> dict[str, Any]:
    """Load an existing personal marketplace without discarding user entries."""
    if not path.exists():
        return {
            "name": DEFAULT_MARKETPLACE_NAME,
            "interface": {"displayName": "Personal"},
            "plugins": [],
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallError(f"Cannot read marketplace file {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise InstallError(f"Marketplace file {path} must contain a JSON object")
    if not isinstance(data.get("plugins", []), list):
        raise InstallError(f"Marketplace field 'plugins' must be a JSON array in {path}")
    if any(not isinstance(entry, dict) for entry in data.get("plugins", [])):
        raise InstallError(
            f"Marketplace field 'plugins' must contain only JSON objects in {path}"
        )
    return data


def jarvis_marketplace_entry() -> dict[str, Any]:
    """Return the personal marketplace entry expected by Codex."""
    return {
        "name": PLUGIN_NAME,
        "source": {"source": "local", "path": "./plugins/jarvis"},
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }


def update_marketplace_document(data: dict[str, Any]) -> dict[str, Any]:
    """Add or replace only Jarvis while preserving other marketplace content."""
    updated = dict(data)
    updated.setdefault("name", DEFAULT_MARKETPLACE_NAME)
    updated.setdefault("interface", {"displayName": "Personal"})

    plugins = list(updated.get("plugins", []))
    plugins = [entry for entry in plugins if entry.get("name") != PLUGIN_NAME]
    plugins.append(jarvis_marketplace_entry())
    updated["plugins"] = plugins
    return updated


def write_json_atomically(path: Path, data: dict[str, Any]) -> None:
    """Write JSON in the same directory so os.replace remains atomic."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def find_codex_cli(explicit_path: Optional[str] = None) -> str:
    """Resolve Codex CLI on Unix or Windows."""
    if explicit_path:
        candidate = Path(explicit_path).expanduser()
        if candidate.is_file():
            return str(candidate.resolve())
        resolved = shutil.which(explicit_path)
        if resolved:
            return resolved
        raise InstallError(f"Codex CLI was not found at: {explicit_path}")

    for command in ("codex", "codex.exe", "codex.cmd"):
        resolved = shutil.which(command)
        if resolved:
            return resolved
    raise InstallError(
        "Codex CLI was not found on PATH. Install Codex or pass --codex PATH."
    )


def add_plugin(codex_cli: str, marketplace_name: str) -> None:
    """Ask Codex to install or refresh Jarvis from the personal marketplace."""
    result = subprocess.run(
        [codex_cli, "plugin", "add", f"{PLUGIN_NAME}@{marketplace_name}"],
        check=False,
    )
    if result.returncode != 0:
        raise InstallError(
            "Codex could not add Jarvis. The plugin files and marketplace entry "
            "are ready; fix the CLI error above, then run this installer again."
        )


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install the Jarvis Codex plugin for the current user."
    )
    parser.add_argument(
        "--codex",
        metavar="PATH",
        help="Codex CLI executable when it is not available on PATH",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and print the planned actions without changing the machine",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    source = Path(__file__).resolve().parents[1]
    user_home = Path.home()
    destination = user_home / "plugins" / PLUGIN_NAME
    marketplace_path = user_home / ".agents" / "plugins" / "marketplace.json"

    try:
        validate_bundle(source)
        marketplace = load_marketplace(marketplace_path)
        updated_marketplace = update_marketplace_document(marketplace)
        marketplace_name = updated_marketplace.get("name", DEFAULT_MARKETPLACE_NAME)
        if not isinstance(marketplace_name, str) or not marketplace_name.strip():
            raise InstallError("Marketplace field 'name' must be a non-empty string")

        codex_cli = find_codex_cli(args.codex)
        if args.dry_run:
            print("Jarvis installer dry run passed.")
            print(f"  Source:      {source}")
            print(f"  Destination: {destination}")
            print(f"  Marketplace: {marketplace_path}")
            print(f"  Codex CLI:   {codex_cli}")
            return 0

        bundle_result = install_bundle(source, destination)
        try:
            write_json_atomically(marketplace_path, updated_marketplace)
        except Exception:
            rollback_bundle(destination, bundle_result)
            raise
        add_plugin(codex_cli, marketplace_name)
    except (InstallError, OSError) as exc:
        print(f"Jarvis installation failed: {exc}", file=sys.stderr)
        return 1

    print("Jarvis installed successfully.")
    print(f"  Plugin:      {destination}")
    print(f"  Marketplace: {marketplace_path}")
    if bundle_result.backup is not None:
        print(f"  Backup:      {bundle_result.backup}")
    print("Next: open a new Codex task, run /hooks, trust the Jarvis hooks, then invoke $jarvis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
