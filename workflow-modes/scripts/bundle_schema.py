"""Validate phase links and metadata shared by lifecycle and offline checks."""

from __future__ import annotations

from pathlib import PurePosixPath
import re


PHASE_PATH = re.compile(r"phases/P\d{2,}-[A-Za-z0-9_-]+\.md")
PHASE_FIELDS = ("Status", "Depends on", "Wave", "Subagent", "Owned scope", "Produces")


def phase_errors(files: dict[str, str]) -> list[str]:
    phases = {name: text for name, text in files.items() if name.startswith("phases/")}
    linked = set(PHASE_PATH.findall(files.get("plan.md", "")))
    if linked != set(phases):
        return [f"phase links differ from manifest: missing files={sorted(linked - set(phases))}, unlinked files={sorted(set(phases) - linked)}"]
    metadata: dict[str, dict[str, str]] = {}
    paths: dict[str, str] = {}
    errors: list[str] = []
    for path, text in phases.items():
        identity = re.fullmatch(r"(P\d{2,})-[A-Za-z0-9_-]+\.md", PurePosixPath(path).name)
        title = re.findall(r"^# (P\d{2,}): .+$", text, re.MULTILINE)
        if not identity or title != [identity.group(1)] or title[0] in metadata:
            errors.append(f"{path}: invalid or duplicate phase ID/title")
            continue
        phase_id = title[0]
        fields: dict[str, str] = {}
        for field in PHASE_FIELDS:
            values = re.findall(rf"^{re.escape(field)}:[ \t]*(.*)$", text, re.MULTILINE)
            if len(values) != 1 or not values[0].strip():
                errors.append(f"{path}: {field} must occur once with a value")
            else:
                fields[field] = values[0].strip()
        if len(fields) != len(PHASE_FIELDS):
            continue
        if fields["Status"] not in {"Pending", "In progress", "Completed", "Blocked", "Superseded"}:
            errors.append(f"{path}: invalid Status")
        if not re.fullmatch(r"[1-9]\d*", fields["Wave"]):
            errors.append(f"{path}: Wave must be a positive integer")
        if fields["Subagent"] != "Eligible" and not re.fullmatch(r"Not eligible(?:\s+[—-]\s+.+)?", fields["Subagent"]):
            errors.append(f"{path}: invalid Subagent eligibility")
        metadata[phase_id] = fields
        paths[phase_id] = path
    if errors:
        return errors
    dependencies: dict[str, list[str]] = {}
    for phase_id, fields in metadata.items():
        dependencies[phase_id] = [] if fields["Depends on"] == "None" else [part.strip() for part in fields["Depends on"].split(",")]
        deps = dependencies[phase_id]
        if len(deps) != len(set(deps)) or not set(deps).issubset(metadata):
            errors.append(f"{paths[phase_id]}: duplicate or unknown Depends on")
    if errors:
        return errors
    visiting: set[str] = set()
    waves: dict[str, int] = {}

    def wave(phase_id: str) -> int:
        if phase_id in visiting:
            raise ValueError(f"{paths[phase_id]}: dependency cycle")
        if phase_id not in waves:
            visiting.add(phase_id)
            waves[phase_id] = 1 + max((wave(dependency) for dependency in dependencies[phase_id]), default=0)
            visiting.remove(phase_id)
        return waves[phase_id]

    try:
        for phase_id, fields in metadata.items():
            if int(fields["Wave"]) != wave(phase_id):
                errors.append(f"{paths[phase_id]}: Wave must be {waves[phase_id]} for its dependencies")
    except ValueError as error:
        return [str(error)]

    # New plans keep metadata only in phase files. Validate duplicated fields in
    # existing v4 tables when present so their scheduling hints cannot contradict.
    headers: list[str] = []
    for line in files.get("plan.md", "").splitlines():
        if not line.strip().startswith("|"):
            headers = []
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if "Depends on" in cells or "Phase file" in cells:
            headers = cells
            continue
        if not headers or len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        phase_ids = re.findall(r"\bP\d{2,}\b", row.get("ID", row.get("Phase", "")))
        if not phase_ids:
            continue
        phase_id = phase_ids[0]
        if phase_id not in metadata:
            errors.append(f"plan.md: declared {phase_id} has no phase file")
            continue
        for field in PHASE_FIELDS:
            if field in row and row[field] != metadata[phase_id][field]:
                errors.append(f"plan.md: {phase_id} {field} differs from {paths[phase_id]}")
        if "Phase file" in row and paths[phase_id] not in row["Phase file"]:
            errors.append(f"plan.md: {phase_id} points to the wrong phase file")
    return errors
