---
name: code-review
description: Claude-Code-inspired code review workflow for diffs, pull requests, branches, commits, or working-tree changes. Use for low, medium, high, extra-high, or maximum-effort reviews; minimum-findings low mode; precision- or recall-biased bug finding; language/framework pitfalls; wrapper, proxy, decorator, or adapter correctness; three-state verification; structured ReportFindings output; GitHub inline comments; or applying verified fixes with --fix.
---

# Claude Code Review

Review changed code for actionable defects a maintainer would fix. Prioritize crashes, wrong outputs, lost invariants, data loss, security-sensitive bypasses, broken async or control flow, compatibility regressions, and concrete reuse, simplification, efficiency, architectural-altitude, or repository-convention problems. Do not report style, naming, generic performance advice, missing tests by itself, or cleanup without an observable maintenance or runtime consequence.

## Load References

After selecting the mode, read every reference required by the active row before reviewing. Do not load unrelated references.

| Trigger | Required References |
| --- | --- |
| `low` or `low-minimum` | [mode-playbooks.md](references/mode-playbooks.md) |
| `medium` or `high` | [mode-playbooks.md](references/mode-playbooks.md), [finder-angles.md](references/finder-angles.md), [verification.md](references/verification.md) |
| `extra-high`, `max`, or `maximum` | [mode-playbooks.md](references/mode-playbooks.md), [finder-angles.md](references/finder-angles.md), [verification.md](references/verification.md), [deep-sweep.md](references/deep-sweep.md) |
| structured output, `--comment`, or `--fix` | add [reporting-and-actions.md](references/reporting-and-actions.md) |

Apply the mode row and every matching action row. This file wins if a reference conflicts with it.

## Select the Mode

Infer the mode from the user's wording. Default to `medium`.

| Mode | Candidate Search | Verification | Finding Cap |
| --- | --- | --- | --- |
| `low` | one hunk-only diff pass | none | 4 |
| `low-minimum` | one hunk-only pass, then one focused extra pass if short | none | target `min(files_changed, 4)` |
| `medium` | 3 correctness + 5 supporting angles, up to 6 candidates each | three-state, precision-biased | 8 |
| `high` | 3 correctness + 5 supporting angles, up to 6 candidates each | three-state, recall-biased | 10 |
| `extra-high` | 5 correctness + 5 supporting angles, up to 8 candidates each | three-state + gap sweep | 15 |
| `max` / `maximum` | 5 correctness + 5 supporting angles, up to 8 candidates each | three-state + gap sweep | 15 |

Use `low-minimum` only when the user explicitly requests a minimum number of findings or exhaustive low-effort coverage. Never invent findings to meet its target.

At `medium`, favor precision: every reported issue should be something a maintainer would act on. At `high`, `extra-high`, and `max`, favor recall: pass every candidate with a nameable failure scenario into verification instead of silently dropping uncertain candidates.

## Gather the Diff

Read the requested target before judging it. Honor an explicit base or target first. Treat user-provided scope restrictions, focus files, exclusions, and review instructions as hard constraints throughout the review, including any delegated work. Otherwise, for a local branch, cover both committed and uncommitted changes with the equivalent of:

```text
git diff @{upstream}...HEAD
git diff HEAD
```

Fall back to the repository's main branch or the working tree when no upstream exists. Gather the changed-file summary and unified diff, then inspect enclosing functions, callers, callees, tests, fixtures, schemas, generated types, migrations, feature flags, config, and documented contracts only as needed to establish behavior. Keep large raw outputs out of the conversation; index or summarize them and retrieve focused sections.

For `low` and `low-minimum`, make one diff-reading call, skip test and fixture hunks (`test/`, `spec/`, `__tests__/`, `*_test.*`, `*.test.*`, `fixtures/`, `testdata/`), do not read full files, and judge only what is visible in the hunk.

## Generate Candidates Independently

Follow the selected playbook and the detailed angle checklist. Keep finder passes independent, preserve distinct failure mechanisms on the same line, and deduplicate only after candidate generation. Pass every candidate with a nameable failure scenario into verification; verification, not finder intuition, owns the final verdict.

## Low-Effort Output

Follow the exact hunk-only scope and one-line output contract in the active low-effort playbook. Never invent findings to meet a requested minimum.

## Verify Candidates

For `medium` and above, deduplicate candidates with the same defect, location, and mechanism, then give each survivor a focused verification pass. Keep `CONFIRMED` and `PLAUSIBLE`; discard `REFUTED`. Use the active mode's precision or recall bias without weakening the requirement for a concrete trigger and wrong effect.

## Run the Gap Sweep

For `extra-high` and `max`, run the complete deep sweep after initial verification. Search only for defect classes missing from the deduplicated list and verify every new sweep candidate before reporting it.

## Report Findings

Rank findings most severe first and respect the mode cap. For human-readable output, put findings before the summary. Include the file and line, severity when useful, concise title, concrete failure scenario, why the change causes it, category, and verification verdict when a verify pass ran. If none survive, say so clearly and mention only meaningful residual risk or skipped checks.

For structured output, GitHub comments, or fixes, follow the required reporting and action reference. Do not duplicate a textual findings list after using a reporting tool.

## Post GitHub Comments

Post comments only when the user passes `--comment` or explicitly requests them. Produce and verify findings before posting. If the target is not a GitHub pull request, keep the findings local and state that commenting was ignored.

## Apply Fixes

Apply fixes only when the user passes `--fix` or explicitly requests them. Produce and verify findings before editing, keep every change traceable to a finding, run narrow verification, and report fixes, skips, and residual risk.
