#!/usr/bin/env python3
"""Launch an independent Codex CLI worker for an accepted execution record."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = SKILL_ROOT / "config" / "worker.toml"
RECEIPT_SCHEMA = SKILL_ROOT / "references" / "worker-receipt.schema.json"
ALLOWED_EFFORTS = {"low", "medium", "high", "xhigh", "max"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch a Codex worker for one exact bundle.")
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--tracker-id", required=True)
    parser.add_argument("--worktree", required=True, type=Path)
    parser.add_argument("--runtime-dir", required=True, type=Path)
    parser.add_argument("--constraints-file", type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--model")
    parser.add_argument("--reasoning-effort")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def existing_directory(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_dir():
        raise ValueError(f"{label} is not a readable directory: {resolved}")
    return resolved


def load_settings(config_path: Path, model: str | None, effort: str | None) -> tuple[str, str]:
    with config_path.expanduser().resolve().open("rb") as handle:
        data = tomllib.load(handle)
    effective_model = model or data.get("model")
    effective_effort = effort or data.get("model_reasoning_effort")
    if not isinstance(effective_model, str) or not effective_model.strip():
        raise ValueError("worker model is missing or invalid")
    if effective_effort not in ALLOWED_EFFORTS:
        raise ValueError(f"unsupported reasoning effort: {effective_effort!r}")
    return effective_model, effective_effort


def model_catalog(codex_bin: str) -> dict[str, set[str]]:
    result = subprocess.run(
        [codex_bin, "debug", "models"], check=True, capture_output=True, text=True
    )
    payload = json.loads(result.stdout)
    entries = payload.get("models", []) if isinstance(payload, dict) else payload
    catalog: dict[str, set[str]] = {}
    for entry in entries:
        slug = entry.get("slug") or entry.get("id")
        if not isinstance(slug, str):
            continue
        levels = entry.get("supported_reasoning_levels", [])
        catalog[slug] = {
            level["effort"]
            for level in levels
            if isinstance(level, dict) and isinstance(level.get("effort"), str)
        }
    return catalog


def validate_model(codex_bin: str, model: str, effort: str) -> None:
    catalog = model_catalog(codex_bin)
    if model not in catalog:
        raise ValueError(f"model is unavailable in the local Codex catalog: {model}")
    if effort not in catalog[model]:
        supported = ", ".join(sorted(catalog[model])) or "none reported"
        raise ValueError(f"{model} does not support {effort}; supported: {supported}")


def validate_runtime(runtime_dir: Path, protected: list[Path]) -> None:
    for path in protected:
        if runtime_dir == path or runtime_dir.is_relative_to(path) or path.is_relative_to(runtime_dir):
            raise ValueError(f"runtime directory must be separate from protected path: {path}")


def constraints_text(path: Path | None) -> str:
    if path is None:
        return "No additional READY_WITH_CONSTRAINTS items were supplied."
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"constraints file is not readable: {resolved}")
    return resolved.read_text(encoding="utf-8")


def worker_prompt(bundle: Path, tracker_id: str, worktree: Path, constraints: str) -> str:
    return f"""Invoke $execute, not $handoff-execute.

Adopt and execute only this exact workflow-record version 4 bundle:
- Canonical bundle root: {bundle}
- Tracker ID: {tracker_id}
- Dedicated implementation worktree: {worktree}

You are the sole writer of the execution bundle and implementation worktree for this bounded worker interval. Read the complete $execute skill, every required reference, every manifest file, repository instructions, and the full accepted record before mutation. Implement the entire authorized scope, update the original bundle transactionally, create only authorized local incremental commits, and run required verification.

Do not invoke $handoff-execute, spawn subagents, or delegate implementation to another agent or session. Do not create another plan or execution bundle. Do not push, deploy, merge, rewrite history, perform destructive or external mutations, broaden scope, or modify unrelated user work unless the record and current authorization explicitly permit the exact action.

Before handoff, complete the full $execute quality workflow, including its required $simplify pass. Apply and commit verified simplify fixes when authorized, run the affected checks again, and record the simplify results and residual risks in the execution bundle. The controlling parent session will independently reconcile your work and run a second $simplify acceptance pass; do not defer your own quality gate to it.

Additional parent constraints:
{constraints}

Before returning, reconcile all workflow-action markers and emit exactly one JSON receipt matching the supplied output schema. Report actual incomplete work, blockers, failed checks, and risks; do not claim completion from process success alone.
"""


def main() -> int:
    args = parse_args()
    try:
        bundle = existing_directory(args.bundle, "bundle")
        worktree = existing_directory(args.worktree, "worktree")
        if not (bundle / "index.md").is_file():
            raise ValueError(f"bundle does not contain index.md: {bundle}")
        runtime_dir = args.runtime_dir.expanduser().resolve()
        validate_runtime(runtime_dir, [bundle, worktree])
        runtime_dir.mkdir(parents=True, exist_ok=True)
        model, effort = load_settings(args.config, args.model, args.reasoning_effort)
        validate_model(args.codex_bin, model, effort)
        prompt = worker_prompt(bundle, args.tracker_id, worktree, constraints_text(args.constraints_file))
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        print(f"handoff-execute: {error}", file=sys.stderr)
        return 2

    receipt = runtime_dir / "worker-receipt.json"
    log_path = runtime_dir / "worker.log"
    command = [
        args.codex_bin,
        "exec",
        "-C",
        os.fspath(worktree),
        "--add-dir",
        os.fspath(bundle),
        "-c",
        f"model={json.dumps(model)}",
        "-c",
        f"model_reasoning_effort={json.dumps(effort)}",
        "--output-schema",
        os.fspath(RECEIPT_SCHEMA),
        "--output-last-message",
        os.fspath(receipt),
        "-",
    ]
    metadata = {
        "command": command,
        "bundle": os.fspath(bundle),
        "tracker_id": args.tracker_id,
        "worktree": os.fspath(worktree),
        "runtime_dir": os.fspath(runtime_dir),
        "log": os.fspath(log_path),
        "receipt": os.fspath(receipt),
        "model": model,
        "model_reasoning_effort": effort,
    }
    print(json.dumps(metadata, indent=2))
    if args.dry_run:
        return 0

    try:
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            if process.stdin is None or process.stdout is None:
                raise RuntimeError("failed to open Codex process pipes")
            process.stdin.write(prompt)
            process.stdin.close()
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                log.write(line)
                log.flush()
            return process.wait()
    except (OSError, RuntimeError) as error:
        print(f"handoff-execute: failed to launch worker: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
