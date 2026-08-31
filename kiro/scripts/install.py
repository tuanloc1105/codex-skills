#!/usr/bin/env python3
"""Install or export the independent Kiro workflow distribution safely."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import sys
import tempfile
import time
from typing import Iterable
import uuid


SKILL_PATTERN = re.compile(r"^---\n.*?^name:\s*([^\s]+)\s*$.*?^---\n", re.MULTILINE | re.DOTALL)
REFERENCE_PATTERN = re.compile(r"\[[^\]]+\]\((references/[^)]+\.md)\)")
EXCLUDED = {".DS_Store", "__pycache__"}


class InstallError(RuntimeError):
    """Raised when validation or a safe replacement contract fails."""


@dataclass(frozen=True)
class InstallResult:
    changed: bool
    scope: str
    config_root: Path
    fingerprint: str
    backup: Path | None
    files: tuple[str, ...]


def source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_manifest(root: Path) -> dict[str, object]:
    try:
        data = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InstallError(f"invalid Kiro distribution manifest: {error}") from error
    required = {"name", "version", "recordVersion", "marker", "skills", "hookTemplate", "runtime"}
    if not required.issubset(data) or data.get("recordVersion") != 4:
        raise InstallError("manifest is incomplete or does not target workflow-record v4")
    return data


def reject_symlinks(root: Path) -> None:
    for path in (root, *root.rglob("*")):
        if path.is_symlink():
            raise InstallError(f"distribution must not contain symlinks: {path}")


def distributable_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED for part in path.parts):
            continue
        yield path


def validate_skill(root: Path, expected_name: str) -> None:
    skill = root / "SKILL.md"
    if not skill.is_file():
        raise InstallError(f"missing SKILL.md for {expected_name}")
    text = skill.read_text(encoding="utf-8")
    match = SKILL_PATTERN.search(text)
    if not match or match.group(1) != expected_name:
        raise InstallError(f"skill frontmatter name does not match {expected_name}")
    for reference in REFERENCE_PATTERN.findall(text):
        if not (root / reference).is_file():
            raise InstallError(f"missing reference {reference} for {expected_name}")


def validate_source(root: Path) -> dict[str, object]:
    reject_symlinks(root)
    manifest = load_manifest(root)
    skills = manifest.get("skills")
    runtime = manifest.get("runtime")
    if not isinstance(skills, list) or not all(isinstance(item, str) for item in skills):
        raise InstallError("manifest skills must be a string list")
    if not isinstance(runtime, list) or not all(isinstance(item, str) for item in runtime):
        raise InstallError("manifest runtime must be a string list")
    for name in skills:
        validate_skill(root / "skills" / name, name)
    for relative in runtime:
        if not (root / relative).is_file():
            raise InstallError(f"missing runtime file: {relative}")
    hook_path = root / str(manifest["hookTemplate"])
    try:
        hook_text = hook_path.read_text(encoding="utf-8")
        hook = json.loads(hook_text)
    except (OSError, json.JSONDecodeError) as error:
        raise InstallError(f"invalid hook template: {error}") from error
    if hook.get("version") != "v1" or not isinstance(hook.get("hooks"), list):
        raise InstallError("hook template must use standalone v1 schema")
    if "{{WORKFLOW_MODES_COMMAND}}" not in hook_text:
        raise InstallError("hook template is missing the command placeholder")
    return manifest


def render_command(scope: str, config_root: Path, platform: str) -> str:
    if scope not in {"global", "project"}:
        raise InstallError(f"unsupported scope: {scope}")
    if platform == "win32":
        script = (
            PureWindowsPath(config_root) / "workflow-modes/scripts/workflow_modes_hook.py"
            if scope == "global"
            else PureWindowsPath(".kiro/workflow-modes/scripts/workflow_modes_hook.py")
        )
        return f'set KIRO_WORKFLOW_SCOPE={scope}&& py -3 "{script}"'
    script = (
        config_root / "workflow-modes/scripts/workflow_modes_hook.py"
        if scope == "global"
        else Path(".kiro/workflow-modes/scripts/workflow_modes_hook.py")
    )
    return f'KIRO_WORKFLOW_SCOPE={scope} python3 "{script}"'


def render_hook(
    root: Path,
    manifest: dict[str, object],
    scope: str,
    config_root: Path,
    platform: str,
) -> bytes:
    template_path = root / str(manifest["hookTemplate"])
    template = json.loads(template_path.read_text(encoding="utf-8"))
    command = render_command(scope, config_root, platform)
    replaced = 0
    for hook in template.get("hooks", []):
        action = hook.get("action", {})
        if action.get("command") == "{{WORKFLOW_MODES_COMMAND}}":
            action["command"] = command
            replaced += 1
    if not replaced:
        raise InstallError("hook command placeholder was not rendered")
    return (json.dumps(template, indent=2) + "\n").encode("utf-8")


def payload(
    root: Path,
    manifest: dict[str, object],
    scope: str,
    config_root: Path,
    platform: str,
) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for name in manifest["skills"]:
        skill_root = root / "skills" / str(name)
        for path in distributable_files(skill_root):
            relative = path.relative_to(skill_root).as_posix()
            result[f"skills/{name}/{relative}"] = path.read_bytes()
    result["hooks/workflow-modes.json"] = render_hook(
        root, manifest, scope, config_root, platform
    )
    for relative in manifest["runtime"]:
        path = root / str(relative)
        result[f"workflow-modes/scripts/{path.name}"] = path.read_bytes()
    if scope == "project":
        result[str(manifest["projectMarker"])] = b"workflow-modes-v1\n"
    return result


def content_fingerprint(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(files):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(files[relative]).digest())
    return digest.hexdigest()


def installed_fingerprint(config_root: Path, files: Iterable[str]) -> str | None:
    installed: dict[str, bytes] = {}
    for relative in files:
        path = config_root / relative
        if not path.is_file() or path.is_symlink():
            return None
        installed[relative] = path.read_bytes()
    return content_fingerprint(installed)


def installation_manifest(
    source_manifest: dict[str, object], scope: str, fingerprint: str, files: Iterable[str]
) -> bytes:
    data = {
        "name": source_manifest["name"],
        "version": source_manifest["version"],
        "recordVersion": source_manifest["recordVersion"],
        "marker": source_manifest["marker"],
        "scope": scope,
        "fingerprint": fingerprint,
        "files": sorted(files),
    }
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


def remove_exact_file(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        raise InstallError(f"owned file path became a directory: {path}")


def rollback(backup: Path, config_root: Path) -> None:
    try:
        metadata = json.loads((backup / "rollback.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InstallError(f"invalid rollback metadata: {error}") from error
    for relative in reversed(metadata["installed"]):
        remove_exact_file(config_root / relative)
    for relative in metadata["backedUp"]:
        source = backup / "files" / relative
        destination = config_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source, destination)


def install_distribution(
    root: Path,
    config_root: Path,
    *,
    scope: str,
    platform: str = sys.platform,
    dry_run: bool = False,
    force_drift: bool = False,
) -> InstallResult:
    root = root.resolve()
    config_root = config_root.resolve()
    source_manifest = validate_source(root)
    core = payload(root, source_manifest, scope, config_root, platform)
    fingerprint = content_fingerprint(core)
    manifest_relative = "workflow-modes/manifest.json"
    files = tuple(sorted(core))
    installed_manifest_path = config_root / manifest_relative
    installed_manifest: dict[str, object] | None = None
    if installed_manifest_path.is_file():
        try:
            installed_manifest = json.loads(installed_manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise InstallError(f"installed manifest is invalid: {error}") from error
    actual = installed_fingerprint(config_root, files) if installed_manifest else None
    if installed_manifest and installed_manifest.get("version") == source_manifest["version"]:
        if actual == fingerprint and installed_manifest.get("fingerprint") == fingerprint:
            return InstallResult(False, scope, config_root, fingerprint, None, files)
        if not force_drift:
            raise InstallError("same-version workflow content drift detected; use --force-drift to replace")
    elif not installed_manifest:
        collisions = [relative for relative in files if (config_root / relative).exists()]
        if collisions and not force_drift:
            raise InstallError("unmanaged workflow-owned paths already exist: " + ", ".join(collisions))
    if dry_run:
        return InstallResult(True, scope, config_root, fingerprint, None, files)

    config_root.mkdir(parents=True, exist_ok=True)
    all_files = dict(core)
    all_files[manifest_relative] = installation_manifest(
        source_manifest, scope, fingerprint, files
    )
    backup_root = config_root.parent / f"{config_root.name}-workflow-backups"
    backup = backup_root / f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
    existing = [relative for relative in all_files if (config_root / relative).is_file()]
    if existing:
        backup.mkdir(parents=True, exist_ok=False)
    installed: list[str] = []
    backed_up: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="kiro-workflow-stage-", dir=config_root.parent) as temporary:
            stage = Path(temporary)
            for relative, content in all_files.items():
                staged = stage / relative
                staged.parent.mkdir(parents=True, exist_ok=True)
                staged.write_bytes(content)
            if content_fingerprint({key: (stage / key).read_bytes() for key in core}) != fingerprint:
                raise InstallError("staged distribution fingerprint mismatch")
            for relative in sorted(all_files):
                destination = config_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    if not destination.is_file() or destination.is_symlink():
                        raise InstallError(f"owned destination is not a regular file: {destination}")
                    backup_path = backup / "files" / relative
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(destination, backup_path)
                    backed_up.append(relative)
                os.replace(stage / relative, destination)
                installed.append(relative)
    except Exception:
        for relative in reversed(installed):
            remove_exact_file(config_root / relative)
        for relative in backed_up:
            backup_path = backup / "files" / relative
            destination = config_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(backup_path, destination)
        raise
    if existing:
        metadata = {"installed": installed, "backedUp": backed_up}
        (backup / "rollback.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return InstallResult(True, scope, config_root, fingerprint, backup if existing else None, files)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    install = subparsers.add_parser("install", help="install into global Kiro home")
    install.add_argument("--kiro-home")
    export = subparsers.add_parser("export", help="export into a project's .kiro directory")
    export.add_argument("--project", required=True)
    for command in (install, export):
        command.add_argument("--dry-run", action="store_true")
        command.add_argument("--force-drift", action="store_true")
        command.add_argument("--platform", choices=("linux", "darwin", "win32"), default=sys.platform)
    restore = subparsers.add_parser("rollback", help="restore an operation backup")
    restore.add_argument("--config-root", required=True)
    restore.add_argument("--backup", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "rollback":
            rollback(Path(args.backup).resolve(), Path(args.config_root).resolve())
            print(f"Restored workflow-owned paths from {args.backup}")
            return 0
        if args.command == "install":
            config_root = Path(args.kiro_home or os.environ.get("KIRO_HOME", Path.home() / ".kiro"))
            scope = "global"
        else:
            config_root = Path(args.project) / ".kiro"
            scope = "project"
        result = install_distribution(
            source_root(), config_root, scope=scope, platform=args.platform,
            dry_run=args.dry_run, force_drift=args.force_drift,
        )
        verb = "Would update" if args.dry_run else ("Updated" if result.changed else "Already current")
        print(f"{verb} {scope} Kiro workflow distribution at {result.config_root}")
        if result.backup:
            print(f"Backup: {result.backup}")
        return 0
    except InstallError as error:
        print(f"Kiro workflow install failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
