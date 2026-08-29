#!/usr/bin/env python3
"""Validate the closed Jira REST registry and its documentation contracts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references" / "rest-capability-registry.json"
REQUIRED_FIELDS = {
    "id", "family", "mcp_probe", "method", "path", "classic_scope",
    "granular_scopes", "tier", "target", "authorization", "bounds",
    "retry", "verification",
}
REQUIRED_IDS = {
    "attachment.metadata", "attachment.content", "issue.get",
    "issue.changelog.list", "comment.list", "comment.get", "worklog.list",
    "worklog.get", "issue-link.get", "watcher.list", "board.list",
    "board.get", "board.issue.list", "board.backlog.list",
    "board.sprint.list", "sprint.get", "sprint.issue.list",
    "project.version.list", "version.get", "board.version.list",
    "comment.add", "issue-link.create", "watcher.add", "issue.assign",
    "issue.transition.list", "issue.transition", "issue.editmeta", "issue.edit",
}
PATH_RE = re.compile(r"^/rest/(?:api/3|agile/1\.0|software/1\.0)/[A-Za-z0-9{}._/-]*$")
LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    data = json.loads(REGISTRY.read_text())
    entries = data.get("capabilities", [])
    if data.get("default") != "deny":
        fail(errors, "registry default must be deny")

    ids: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    for index, entry in enumerate(entries):
        label = entry.get("id", f"entry[{index}]")
        missing = REQUIRED_FIELDS - entry.keys()
        if missing:
            fail(errors, f"{label}: missing fields {sorted(missing)}")
        if label in ids:
            fail(errors, f"duplicate capability ID: {label}")
        ids.add(label)
        pair = (entry.get("method", ""), entry.get("path", ""))
        if pair in pairs:
            fail(errors, f"duplicate method/path pair: {pair}")
        pairs.add(pair)
        if not PATH_RE.fullmatch(entry.get("path", "")):
            fail(errors, f"{label}: invalid exact path template")
        if entry.get("tier") not in {"A", "B"}:
            fail(errors, f"{label}: only tiers A and B are registered")
        if entry.get("tier") == "A" and entry.get("method") != "GET":
            fail(errors, f"{label}: Tier A must be GET")
        if entry.get("tier") == "B":
            if entry.get("method") not in {"POST", "PUT"}:
                fail(errors, f"{label}: Tier B must be POST or PUT")
            if "explicit" not in entry.get("authorization", "").lower():
                fail(errors, f"{label}: Tier B requires explicit authorization")
            if "never automatically retry" not in entry.get("retry", "").lower():
                fail(errors, f"{label}: Tier B must prohibit automatic retries")
            if "re-read" not in entry.get("verification", "").lower() and "get returned" not in entry.get("verification", "").lower():
                fail(errors, f"{label}: Tier B must re-read verification state")
        if not entry.get("granular_scopes") or not entry.get("classic_scope"):
            fail(errors, f"{label}: scopes must be non-empty")

    if ids != REQUIRED_IDS:
        fail(errors, f"capability set mismatch; missing={sorted(REQUIRED_IDS - ids)} extra={sorted(ids - REQUIRED_IDS)}")

    markdown = list(ROOT.rglob("*.md"))
    for document in markdown:
        text = document.read_text()
        for link in LINK_RE.findall(text):
            target = link.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (document.parent / target).resolve().exists():
                fail(errors, f"{document.relative_to(ROOT)}: broken local link {link}")

    skill = (ROOT / "SKILL.md").read_text()
    registry_doc = (ROOT / "references" / "rest-capability-registry.md").read_text()
    attachments = (ROOT / "references" / "rest-attachments.md").read_text()
    platform = (ROOT / "references" / "rest-platform-issues.md").read_text()
    mcp = (ROOT / "references" / "mcp-workflows.md").read_text()
    required_contracts = {
        "SKILL default deny": "defaults to deny" in skill,
        "no Tier C registry": "no Tier C entries" in skill,
        "no arbitrary REST": "arbitrary REST execution" in skill,
        "ACLI approval": "requires a task-scoped user request or approval" in skill,
        "registry generic execution denial": "generic REST execution" in registry_doc,
        "attachment atomic rename": "Atomically rename" in attachments,
        "attachment no overwrite": "refuse existing targets" in attachments,
        "comment explicit target": "one explicit issue" in platform,
        "comment 201 and reread": "require `201`, then GET returned comment ID" in platform,
        "runtime MCP authority": "live server tool list" in mcp,
    }
    for contract, present in required_contracts.items():
        if not present:
            fail(errors, f"missing preservation/default-deny contract: {contract}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated {len(entries)} closed Jira REST capabilities and documentation contracts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
