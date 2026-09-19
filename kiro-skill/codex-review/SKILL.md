---
name: kiro-codex-review
description: Launch an independent Codex CLI session to review findings in one exact workflow-record version 4 bundle produced by kiro-discuss, kiro-plan, or kiro-execute. Codex writes a durable review tracker into the bundle under a bounded ownership transfer; Kiro then validates and adjudicates it. Use when the user asks Kiro to obtain and track a Codex second opinion. Do not use for implementation handoff or ordinary Kiro subagent review.
---

# Codex Review (Kiro / Kiro Crew)

Act as the controlling Kiro session. Launch one independent Codex CLI reviewer only after preparing the exact active bundle for a bounded review write. Codex writes its assessment into that bundle; stdout is diagnostic output, not the review record. Never use `spawn_run`, another subagent mechanism, or an implementation handoff for this workflow.

This skill supplements the active `kiro-discuss`, `kiro-plan`, or `kiro-execute` lifecycle. It does not replace that mode or create a second workflow record. Keep the source mode's authorization, persistence, question, action, and recovery contracts in force.

## Required Skills and References

Read the complete entrypoint for the bundle's active Kiro workflow mode and every reference currently listed under its `Required references`. Validate `index.md` and every manifest file before preparing a review.

Before opening a review action or launching Codex, read [references/review-contract.md](references/review-contract.md). Read [references/recovery.md](references/recovery.md) before acting on an interrupted, failed, missing, malformed, or uncertain reviewer run.

## Core Boundary

- Accept only one exact workflow-record version 4 bundle with a stable tracker ID. Never choose a bundle by recency.
- The user's request for a Codex review authorizes the bounded bundle updates defined here. It does not authorize implementation, source edits, Git mutations, external changes, approval, or lifecycle transitions.
- Kiro remains the coordinator. Codex becomes the sole bundle writer only for the saved reviewer interval.
- Codex may write only `index.md`, `evidence.md`, and the predeclared `reviews/<review-id>.md` artifact. It must not change authoritative context, decisions, plan, phase, verification, source, Git, or external state.
- Codex records proposed assessments. Kiro alone adjudicates them and applies accepted corrections to authoritative bundle files through the active mode's normal record transaction.

## Workflow

1. Recover and validate the active mode, canonical bundle root, tracker ID, complete manifest, Active Snapshot, Resume Checkpoint, open actions, and live repository state.
2. Select a stable review ID such as `CR-001`. Through one source-mode-compliant transaction, create `reviews/<review-id>.md`, declare it in the manifest, open the matching workflow action in `evidence.md`, set `Active action`, and persist the review scope and ownership state. Do not launch while another action or writer is active.
3. Capture the bundle manifest fingerprint and, when repository evidence is in scope, the repository root, branch, `HEAD`, status, and diff boundaries. Verify the saved review action and artifact before transfer.
4. Resolve model settings from explicit user overrides, otherwise [config/reviewer.toml](config/reviewer.toml). Validate them against `codex debug models`; never silently substitute a model or reasoning effort.
5. Invoke [scripts/launch_reviewer.py](scripts/launch_reviewer.py) with the canonical bundle root, tracker ID, review ID, runtime directory, optional repository, and optional scope file. The launcher passes its prompt through stdin and runs Codex with the bundle as its workspace under `workspace-write`.
6. While Codex is active, Kiro must not write the bundle or start overlapping implementation, record updates, or delegated work. Monitoring the actual process and reading its output are allowed.
7. After termination, establish that the reviewer is inactive, reclaim ownership, and validate the complete bundle. Compare the allowed files with the pre-launch snapshot and verify that source, Git, external state, identity, lifecycle metadata, and every non-review manifest file are unchanged.
8. Treat the receipt and Codex-authored tracker as evidence, never automatic truth. Adjudicate each proposed finding as `Accepted`, `Rejected`, `Needs evidence`, `Needs user decision`, `Deferred`, or `Resolved`, then persist the adjudication and any accepted source-mode corrections through one or more normal Kiro record transactions.
9. Record reconciliation, discrepancies, receipt/log paths, and the next safe action. Preserve the review artifact in the manifest as durable tracker history.

## Result Boundary

A successful process exit is insufficient. The review is usable only when the predeclared artifact is readable, the action has a terminal marker, the bundle validates, writes stayed within the allowlist, and repository/source state did not change. If any condition fails, follow recovery and report the actual state without silently accepting or relaunching the review.

Do not automatically rerun Codex after a failed or uncertain attempt. A fresh run consumes additional quota and must use a new review action or an explicitly reconciled continuation of the existing one.
