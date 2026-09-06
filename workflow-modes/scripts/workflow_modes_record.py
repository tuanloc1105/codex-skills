"""Read-only version 4 record validation and revision helpers."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any

SNAPSHOT_START_PATTERN = re.compile(
    r"<!-- workflow-active-snapshot:start version:(?P<version>[12]) -->"
)
SNAPSHOT_END = "<!-- workflow-active-snapshot:end -->"
MANIFEST_START = "<!-- workflow-manifest:start -->"
MANIFEST_END = "<!-- workflow-manifest:end -->"
MAX_RECORD_BYTES = 2 * 1024 * 1024
PROFILES = {"lightweight", "durable", "audited"}
MODES = {"discuss", "plan", "execute"}
MODE_REFERENCES = {
    "discuss": ("references/tracker.md", "references/actions.md"),
    "plan": ("references/plan-record.md", "references/phase-planning.md"),
    "execute": ("references/implementation.md", "references/completion.md"),
}


class BundleError(ValueError):
    def __init__(self, code: str, path: str, detail: str, next_step: str):
        self.code, self.path, self.detail, self.next_step = code, path, detail, next_step
        super().__init__(f"{code}: {path}: {detail}")

    def as_dict(self) -> dict[str, str]:
        return dict(code=self.code, path=self.path, detail=self.detail, next_step=self.next_step)


def invalid(code: str, path: str, detail: str, next_step: str = "Repair this field through the permitted record write transaction, then retry write-close.") -> None:
    raise BundleError(code, path, detail, next_step)


def safe_member(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if (not name or relative.is_absolute() or ".." in relative.parts or "\\" in name
            or ":" in name or relative.suffix.lower() != ".md" or relative.as_posix() != name):
        invalid("WORKFLOW_MANIFEST_PATH_INVALID", name, "Expected a normalized relative Markdown path inside the bundle.")
    candidate = root.joinpath(*relative.parts)
    for part in (candidate, *candidate.parents):
        if part.is_symlink():
            invalid("WORKFLOW_RECORD_PATH_UNSAFE", name, "Symlink paths are not eligible for record writes.", "Ask the owner to restore a regular bundle path; do not follow or replace the symlink automatically.")
        if part == root:
            break
    return candidate


def read_bytes(root: Path, name: str) -> bytes:
    path = safe_member(root, name)
    try:
        if not path.is_file():
            invalid("WORKFLOW_RECORD_FILE_MISSING", name, "Manifest file is missing or is not a regular file.", "Restore this file within an open normal/recovery record write; if no trusted baseline exists, ask the owner to restore it.")
        with path.open("rb") as stream:
            data = stream.read(MAX_RECORD_BYTES + 1)
    except OSError as error:
        invalid("WORKFLOW_RECORD_FILE_IO", name, f"Cannot read file ({type(error).__name__}).", "Check file ownership and permissions from a terminal; restore access without deleting session state.")
    if len(data) > MAX_RECORD_BYTES:
        invalid("WORKFLOW_RECORD_TOO_LARGE", name, "Record exceeds the 2 MiB bundle limit.")
    return data


def read_text(root: Path, name: str) -> str:
    try:
        # Preserve the existing universal-newline revision algorithm.
        return read_bytes(root, name).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeError:
        invalid("WORKFLOW_RECORD_ENCODING_INVALID", name, "Expected UTF-8 text.")


def read_index(path: str | None) -> str | None:
    if not isinstance(path, str):
        return None
    try:
        return read_text(Path(path), "index.md")
    except BundleError:
        return None


def parse_manifest(text: str) -> tuple[str, ...]:
    if text.count(MANIFEST_START) != 1 or text.count(MANIFEST_END) != 1:
        invalid("WORKFLOW_MANIFEST_INVALID", "index.md", "Expected exactly one manifest start and end marker.")
    start = text.index(MANIFEST_START) + len(MANIFEST_START)
    end = text.find(MANIFEST_END, start)
    if end < start:
        invalid("WORKFLOW_MANIFEST_INVALID", "index.md", "Manifest end must follow its start.")
    entries = tuple(line.strip() for line in text[start:end].splitlines() if line.strip())
    if not entries or entries[0] != "index.md" or len(entries) != len(set(entries)):
        invalid("WORKFLOW_MANIFEST_INVALID", "index.md", "Manifest must begin with index.md and contain unique paths.")
    return entries


def observed_files(root: Path) -> dict[str, bytes]:
    """Bounded raw observation, also available for semantically invalid bundles."""
    if root.is_symlink() or not root.is_dir():
        invalid("WORKFLOW_RECORD_PATH_UNSAFE", str(root), "Bundle root must be an existing regular directory.", "Ask the owner to restore the original bundle directory.")
    files: dict[str, bytes] = {}
    total = 0
    def walk_error(error):
        invalid("WORKFLOW_RECORD_FILE_IO", str(root), f"Cannot enumerate bundle ({type(error).__name__}).")
    for directory, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                invalid("WORKFLOW_RECORD_PATH_UNSAFE", str(Path(directory) / name), "Bundle contains a symlink directory.", "Ask the owner to restore regular bundle paths before recovery.")
        for name in sorted(names):
            if Path(name).suffix.lower() != ".md":
                continue
            relative = (Path(directory) / name).relative_to(root).as_posix()
            data = read_bytes(root, relative)
            total += len(data)
            if total > MAX_RECORD_BYTES or len(files) >= 4096:
                invalid("WORKFLOW_RECORD_TOO_LARGE", str(root), "Bundle exceeds 2 MiB or 4096 Markdown files.")
            files[relative] = data
    return files


def observation_revision(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name, data in sorted(files.items()):
        digest.update(name.encode("utf-8") + b"\0" + hashlib.sha256(data).digest())
    return "observed-sha256:" + digest.hexdigest()


def manifest_paths(path: str | None, text: str | None = None) -> tuple[str, ...] | None:
    if not isinstance(path, str):
        return None
    try:
        entries = parse_manifest(read_text(Path(path), "index.md") if text is None else text)
        total = sum(len(read_bytes(Path(path), entry)) for entry in entries)
        if total > MAX_RECORD_BYTES:
            return None
        return entries
    except BundleError:
        return None


def load_bundle(path: str, mode: str | None = None) -> dict[str, str]:
    root = Path(path)
    text = read_text(root, "index.md")
    entries = parse_manifest(text)
    for name in entries:
        read_bytes(root, name)
    raw = observed_files(root)
    extra = sorted(set(raw) - set(entries))
    if extra:
        invalid("WORKFLOW_MANIFEST_EXTRA_FILE", extra[0], "Markdown file is not owned by the manifest.", "Ask the file owner to reconcile it; do not delete another session's files. Normal writes may explicitly declare an authorized addition; recovery cannot expand the baseline manifest.")
    files = {name: read_text(root, name) for name in entries}
    validate_contents(files, mode)
    return files


def record_files(path: str | None) -> dict[str, str] | None:
    if not isinstance(path, str):
        return None
    try:
        return load_bundle(path)
    except BundleError:
        return None


def validate_contents(files: dict[str, str], mode: str | None = None) -> None:
    index = files.get("index.md", "")
    header = re.search(r"workflow-record[^\n>]*version:4[^\n>]*kind:(discuss|plan)[^\n>]*tracker-id:([^\s>]+)", index)
    if not header:
        invalid("WORKFLOW_RECORD_HEADER_INVALID", "index.md", "Expected version:4, kind:discuss|plan and tracker-id in the record header.")
    kind = header.group(1)
    required = {"index.md", "context.md", "decisions.md", "evidence.md"}
    required.update({"actions.md"} if kind == "discuss" else {"plan.md", "verification.md"})
    missing = sorted(required - files.keys())
    if missing:
        invalid("WORKFLOW_RECORD_REQUIRED_FILE", missing[0], "Required bundle member is absent from the manifest.")
    phases: dict[str, str] = {}
    dependencies: dict[str, set[str]] = {}
    for name in sorted(files):
        if not name.startswith("phases/") or not name.endswith(".md"):
            continue
        file_id = Path(name).name.split("-", 1)[0]
        match = re.search(r"^#\s+(P\d{2}):\s+.+$", files[name], re.MULTILINE)
        if not match or match.group(1) != file_id or file_id in phases:
            invalid("WORKFLOW_PHASE_ID_INVALID", name, f"Heading must have unique ID {file_id}, matching the filename.")
        depends = re.search(r"^Depends on:[ \t]*(.*?)[ \t]*$", files[name], re.MULTILINE)
        missing = missing_markers(files[name], ("Status:", "Wave:", "Subagent:", "Owned scope:", "Produces:"))
        if not depends or missing:
            invalid("WORKFLOW_PHASE_METADATA_MISSING", name, "Missing fields: " + ", ".join(missing + ([] if depends else ["Depends on:"])))
        if name not in files.get("plan.md", ""):
            invalid("WORKFLOW_PHASE_LINK_MISSING", "plan.md", f"Missing reference to {name}.")
        phases[file_id] = name
        dependencies[file_id] = set() if depends.group(1) == "None" else {v.strip() for v in depends.group(1).split(",") if v.strip()}
    for phase, values in dependencies.items():
        unknown = sorted(values - phases.keys())
        if unknown:
            invalid("WORKFLOW_PHASE_DEPENDENCY_UNKNOWN", phases[phase], "Unknown dependencies: " + ", ".join(unknown))
    pending = dict(dependencies)
    while pending:
        ready = {phase for phase, values in pending.items() if not values.intersection(pending)}
        if not ready:
            invalid("WORKFLOW_PHASE_DEPENDENCY_CYCLE", phases[sorted(pending)[0]], "Dependency cycle among: " + ", ".join(sorted(pending)))
        for phase in ready:
            del pending[phase]
    opened = re.findall(r"<!-- workflow-action:([A-Z][A-Z0-9_-]{2,63}) status:open -->", files["evidence.md"])
    active = re.search(r"^Active action:[ \t]*([^\s]+)", index, re.MULTILINE)
    if len(opened) > 1 or (opened and (not active or active.group(1) != opened[0])) or (not opened and active and active.group(1) != "None"):
        invalid("WORKFLOW_ACTION_SUMMARY_MISMATCH", "index.md / evidence.md", "Active action must match the single open evidence marker, or be None when none is open.")
    # Rules are mode-specific at write-close/rules-sync. Transitions legitimately
    # carry the old mode's references until the new skill updates the snapshot.
    if mode is not None:
        expected, valid = required_reference_spec(mode, index)
        if not valid:
            invalid("WORKFLOW_RULES_RECORD_INVALID", "index.md: Required references", "Unknown or duplicate references in the active snapshot.", "Repair Required references to None or a unique subset of " + ", ".join(expected) + "; read the selected references and run rules-sync after closing the record write.")


def validate_bundle(files: dict[str, str]) -> bool:
    try:
        validate_contents(files)
        return True
    except BundleError:
        return False


def diagnose_bundle(path: str) -> dict:
    root = Path(path).expanduser().absolute()
    if root.name == "index.md":
        root = root.parent
    report = {"record": str(root), "valid": False, "observed_revision": None, "issues": []}
    try:
        report["observed_revision"] = observation_revision(observed_files(root))
        index = read_index(str(root)) or ""
        mode = "execute" if "Execute mode: Active" in index else ("discuss" if "kind:discuss" in index else "plan")
        load_bundle(str(root), mode)
        report["valid"] = True
    except BundleError as error:
        report["issues"].append(error.as_dict())
    return report


def record_revision(path: str | None) -> str | None:
    files = record_files(path)
    if files is None:
        return None
    return files_revision(files)


def files_revision(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name in sorted(files):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(files[name].encode("utf-8")).digest())
    return "sha256:" + digest.hexdigest()


def content_revision(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_snapshot(text: str | None) -> str | None:
    if text is None or len(SNAPSHOT_START_PATTERN.findall(text)) != 1 or text.count(SNAPSHOT_END) != 1:
        return None
    marker = SNAPSHOT_START_PATTERN.search(text)
    assert marker is not None
    start = marker.end()
    end = text.find(SNAPSHOT_END, start)
    if end < start:
        return None
    snapshot = text[start:end]
    if len(snapshot.encode("utf-8")) > 64 * 1024:
        return None
    return snapshot


def record_revisions(path: str | None) -> tuple[str | None, str | None, str | None]:
    files = record_files(path)
    if files is None:
        return None, None, None
    text = files["index.md"]
    revision = files_revision(files)
    snapshot = record_snapshot(text)
    if snapshot is None:
        return revision, None, None
    marker = SNAPSHOT_START_PATTERN.search(text)
    assert marker is not None
    index_outside = text[:marker.start()] + text[text.index(SNAPSHOT_END, marker.end()) + len(SNAPSHOT_END):]
    outside_digest = hashlib.sha256(index_outside.encode("utf-8") + b"\0")
    for name in sorted(files):
        if name != "index.md":
            outside_digest.update(name.encode("utf-8"))
            outside_digest.update(b"\0")
            outside_digest.update(hashlib.sha256(files[name].encode("utf-8")).digest())
    return revision, content_revision(snapshot), "sha256:" + outside_digest.hexdigest()


def record_profile(path: str | None) -> str:
    if not isinstance(path, str):
        return "audited"
    snapshot = record_snapshot(read_index(path))
    if snapshot is None:
        return "audited"
    match = re.search(r"^Profile:\s*(\S+)\s*$", snapshot, flags=re.MULTILINE)
    profile = match.group(1).lower() if match else "audited"
    return profile if profile in PROFILES else "audited"


def required_reference_spec(mode: str, text: str | None) -> tuple[tuple[str, ...], bool]:
    """Return the snapshot allowlist, using the full-mode safe legacy fallback."""
    allowed = MODE_REFERENCES[mode]
    snapshot = record_snapshot(text)
    marker = SNAPSHOT_START_PATTERN.search(text or "")
    if snapshot is None or marker is None or marker.group("version") == "1":
        return allowed, True
    match = re.search(r"^Required references:\s*(.*?)\s*$", snapshot, re.MULTILINE)
    if not match:
        return allowed, True
    value = match.group(1)
    if value == "None":
        return (), True
    references = tuple(part.strip() for part in value.split(",") if part.strip())
    if len(references) != len(set(references)) or not set(references).issubset(allowed):
        return allowed, False
    return tuple(reference for reference in allowed if reference in references), True


def required_references(mode: str, text: str | None) -> tuple[str, ...]:
    return required_reference_spec(mode, text)[0]


def refresh_required_references(state: dict[str, Any]) -> bool:
    references, valid = required_reference_spec(
        str(state["mode"]), read_index(str(state.get("record")))
    )
    changed = list(references) != state.get("required_references")
    state["required_references"] = list(references)
    state["required_references_valid"] = valid
    if changed:
        state["rules_sync_required"] = True
    return changed


def record_tracker_id(path: str | None) -> str | None:
    if not isinstance(path, str):
        return None
    text = read_index(path)
    if text is None:
        return None
    header = re.search(r"workflow-record[^\n>]*tracker-id:([^\s>]+)", text)
    if header:
        return header.group(1)
    metadata = re.search(r"^Tracker ID:\s*(\S+)\s*$", text, flags=re.MULTILINE)
    return metadata.group(1) if metadata else None




def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]
