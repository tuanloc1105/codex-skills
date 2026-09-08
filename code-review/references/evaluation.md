# Reliability Evaluation (Maintenance Only)

Do not load this file for ordinary reviews. Run these checks after changing target, fix, routing or reporting contracts. They use Python's standard library and a local Git executable; no network, provider credentials or paid model calls are needed.

## Reproduce

From the repository root (or replace code-review with the absolute installed skill path):

```sh
python3 -B -m unittest discover -s code-review/tests -p 'test_*.py'
python3 -B code-review/scripts/check_review_scenarios.py
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py code-review
```

The unittest suite creates and removes only its own temporary repositories beneath tests/. Git recipe tests exercise pushed-feature omission, two-/three-dot endpoints, cancellation, index/worktree separation, filtered additions, untracked recreation, rename/deletion/mode metadata and root/shallow/missing-ref behavior. They do not implement a production target resolver. Setup creates fixture refs/index entries; review recipe checks protect those entries. The checker tests inject unsafe recorded outputs to ensure validation rejects them.

## Response Scenarios

`tests/fixtures/*-cases.json` holds prompts, mode/target, expectations and contract data. `observed-responses.json` contains the coordinator's actual same-context dry-run answers and manual assessments from the implementation session. These are response/action-plan observations, not actual fix, comment or publication execution. Alternative R03 outputs represent separate caller requests, not duplicate delivery in one review. T01/T03 answers use the disposable Git cases as evidence.

For a new evaluation, read the current skill and applicable references, present each prompt, retain the actual response without rewriting it to the expected answer, and record mode, target, expected outcome, provenance, assessment and reason. Preserve failed responses when repairing instructions; add a rerun record in the execution evidence before replacing the checked-in baseline. Evaluate these rubrics manually:

| Cases | Pass criteria |
| --- | --- |
| T01/T03 | Merge destination retains pushed changes; cancellation removes stale findings. |
| F01/F02 | Explicit fixes add candidate-specific confirmation only; ordinary low stays hunk-only with exact output. |
| F03/F04/F05 | Repository/head/content correspond before any edit; mismatch and unsafe overlap cause zero planned edits; unrelated changes are preserved. |
| F06/R02 | Real mechanism and specific unknown premise support PLAUSIBLE; speculation is excluded, exact guards refute, uncertainty cannot auto-fix. |
| R01 | Medium/high keep eight angles and fold D/E; xhigh/max keep ten; broad reviewers can retrieve all scoped hunks. |
| R03 | Exact canonical keys; missing confirmation remains visible; caller schemas and required typed output win appropriately; final report delivered once. |
| R04 | Full survivor pool backfills slots; cap disclosure uses permitted fields; new locations are not suppressed by mechanism-only deduplication. |
| R05 | Only requested actions, safe fixes before re-verification and reports, unresolved comments, final once; failures do not corrupt exact JSON. |

The offline checker verifies fixture completeness, stale prompt detection, recorded assessments and machine-checkable output/action contracts. A passing checker does not independently judge the natural-language rationale or prove that a fresh assistant follows the instructions. Its specific text checks only protect the checked-in response examples. For independent model evaluation, retain separate provenance and raw outputs with the same manual rubric; this script deliberately does not relabel the baseline as independent. No latency, precision or recall improvement is measured here.

## Source and Mirror Gate

Read the repository's docs/agent/skill-maintenance.md before synchronization. Validate the full source skill, run focused checks, check local Markdown links and git diff --check, then inspect destination drift before copying. Sync the complete directory with the documented metadata/cache exclusions; validate and run focused checks in the mirror, then compare every non-excluded path and byte. Do not sync a failing source or remove unexplained destination-only content.
