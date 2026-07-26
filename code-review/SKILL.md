---
name: code-review
description: Claude-Code-inspired code review workflow for diffs, pull requests, branches, commits, or working-tree changes. Use for minimal, low, low-minimum/low-expanded, medium, high, extra-high/xhigh, or max/maximum-effort reviews; precision- or recall-biased bug finding; language/framework pitfalls; wrapper, proxy, decorator, or adapter correctness; three-state verification; raw JSON or typed ReportFindings output; GitHub inline comments; opt-in review artifacts; applying verified fixes with --fix; or explaining Claude-only ultra/ultrareview behavior.
---

# Claude Code Review

Review changed code for actionable defects a maintainer would fix. Prioritize crashes, wrong outputs, lost invariants, data loss, security-sensitive bypasses, broken async or control flow, compatibility regressions, and concrete reuse, simplification, efficiency, architectural-altitude, or repository-convention problems. Do not report style, naming, generic performance advice, missing tests by itself, or cleanup without an observable maintenance or runtime consequence. An exact violation of an applicable repository instruction is actionable only when the governing rule, source path, and offending changed line can be identified.

## Load References

After selecting the mode, read every reference required by the active row before reviewing. Do not load unrelated references.

| Trigger | Required References |
| --- | --- |
| `minimal`, `low`, `low-minimum`, or `low-expanded` | [mode-playbooks.md](references/mode-playbooks.md) |
| `medium` or `high` | [mode-playbooks.md](references/mode-playbooks.md), [finder-angles.md](references/finder-angles.md), [verification.md](references/verification.md) |
| `extra-high`, `xhigh`, `max`, or `maximum` | [mode-playbooks.md](references/mode-playbooks.md), [finder-angles.md](references/finder-angles.md), [verification.md](references/verification.md), [deep-sweep.md](references/deep-sweep.md) |
| `ultra` or `ultrareview` explanation | [mode-playbooks.md](references/mode-playbooks.md) |
| raw JSON, structured output, typed reporting, `--comment`, `--fix`, `--artifact`, or a shareable review | add [reporting-and-actions.md](references/reporting-and-actions.md) |

Apply the mode row and every matching action row. This file wins if a reference conflicts with it.

## Select the Mode

Infer the mode from the user's wording. Default to `medium`.

Normalize aliases before routing. Detailed behavior lives in the selected playbook.

| Mode | Candidate Search | Verification | Finding Cap |
| --- | --- | --- | --- |
| `minimal` | one contextual senior pass | no separate phase | 15 |
| `low` | one hunk-only diff pass | none | 4 |
| `low-minimum` / `low-expanded` | one hunk-only pass, then one focused extra pass if short of target | none | 8; search target `min(eligible_reviewed_files, 4)` |
| `medium` | 3 correctness + 5 supporting angles, up to 6 candidates each | three-state, precision-biased | 8 |
| `high` | 3 correctness + 5 supporting angles, up to 6 candidates each | three-state, recall-biased | 10 |
| `extra-high` / `xhigh` | 5 correctness + 5 supporting angles, up to 8 candidates each | three-state + gap sweep | 15 |
| `max` / `maximum` | 5 correctness + 5 supporting angles, up to 8 candidates each | three-state + gap sweep | 15 |

Use `low-minimum` or `low-expanded` only when the user explicitly requests a minimum number of findings, expanded low-effort output, or exhaustive low-effort coverage. Never invent findings to meet its target.

At `medium`, favor precision: every reported issue should be something a maintainer would act on. At `high`, `extra-high`/`xhigh`, and `max`/`maximum`, favor recall: pass every candidate with a nameable failure scenario into verification instead of silently dropping uncertain candidates.

`ultra` and `ultrareview` refer to Claude-host review capabilities, not executable local modes for this skill. Verify current alias, availability, fallback, and pricing details against official Claude documentation before explaining them. Explain the Git/PR prerequisites and syntax without attempting to launch the service from Codex, then offer local `max` as the closest executable alternative.

## Gather the Diff

Read the requested target before judging it. Honor an explicit base or target first. Treat user-provided scope restrictions, focus files, exclusions, and review instructions as hard constraints throughout the review, including any delegated work. Otherwise, for a local branch, cover both committed and uncommitted changes with the equivalent of:

```text
git diff @{upstream}...HEAD
```

Gather the range diff first. Fall back to the repository's default or main branch, then `HEAD~1`, when no upstream exists. When the worktree is dirty or the range diff is empty, also gather `git diff HEAD`; low modes may gather both ranges in their single diff-reading call. List non-ignored untracked files with the equivalent of `git ls-files --others --exclude-standard` and include each as an addition hunk so working-tree scope does not omit new files. Gather the changed-file summary and unified diff, then inspect enclosing functions, callers, callees, tests, fixtures, schemas, generated types, migrations, feature flags, config, history, blame, and documented contracts only as needed to establish behavior. Keep large raw outputs out of the conversation; share an ephemeral indexed diff source or focused excerpt with reviewers instead of duplicating a large raw diff. This internal evidence source is not a published review artifact.

For `low`, `low-minimum`, and `low-expanded`, make one diff-reading call, skip test and fixture hunks (`test/`, `spec/`, `__tests__/`, `*_test.*`, `*.test.*`, `fixtures/`, `testdata/`), do not read full files, and judge only what is visible in the hunk.

## Select the Execution Backend

For `ultra` or `ultrareview`, stop after the compatibility explanation; do not enter execution routing.

Use a dedicated background code-review workflow only when active host instructions expose or require one and its contract supports the normalized mode. Serialize the mode, target, and every user scope restriction into its arguments, wait for its final findings payload—verified where the selected mode requires verification—and do not rerun the same finder pipeline locally.

Without a dedicated workflow, run `minimal` and low modes inline. For `medium` and above, use independent subagents when available and permitted. If they are unavailable, run the same selected angles sequentially in the current context and disclose in the final response that candidate generation and checking were same-context rather than independently verified. Never claim an independent vote for a same-context self-check.

## Generate Candidates Independently

Follow the selected playbook and the detailed angle checklist. Keep finder passes independent, preserve distinct failure mechanisms on the same line, and deduplicate only after candidate generation. For `medium` and above, pass every candidate with a nameable failure scenario into verification; verification, not finder intuition, owns the final verdict. For `minimal`, retain only evidence-backed findings from the single contextual pass without claiming a separate verifier. Low modes follow their hunk-only playbooks and skip verification.

## Low-Effort Output

Follow the exact hunk-only scope and output routing in the active low-effort playbook. Never invent findings to meet a requested minimum.

## Verify Candidates

For `medium` and above, deduplicate candidates with the same defect, location, and mechanism, then give each survivor a focused verification pass. Keep `CONFIRMED` and `PLAUSIBLE`; discard `REFUTED`. Use the active mode's precision or recall bias without weakening the requirement for a concrete trigger and wrong effect. Survival through recall-biased verification does not by itself make a `PLAUSIBLE` finding safe to auto-fix.

## Run the Gap Sweep

For `extra-high`, `xhigh`, `max`, and `maximum`, run the complete deep sweep after initial verification. Search only for defects not already listed, including uncovered instances of a represented class or mechanism at another location; do not restate duplicates. Verify every new sweep candidate before reporting it.

## Report Findings

Rank findings most severe first and respect the mode cap. For human-readable output, put findings before the summary. Include the file and line, severity when useful, concise title, concrete failure scenario, why the change causes it, category, and verification verdict when a verify pass ran. If none survive, say so clearly and mention only meaningful residual risk or skipped checks.

For raw JSON, structured output, typed reporting, artifacts, GitHub comments, or fixes, follow the required reporting and action reference. A caller-supplied JSON schema wins over tool availability; generic structured output defaults to the canonical raw JSON array when no active typed schema is required. A typed reporting tool is used only when active instructions require it, and its findings are not duplicated in prose.

## Post GitHub Comments

Post comments only when the user passes `--comment` or explicitly requests them. Produce and verify findings before posting. If fixes were also requested, comment only on unresolved findings that still apply after re-verification. If the target is not a GitHub pull request, keep the findings local and state that commenting was ignored.

## Apply Fixes

Apply fixes only when the user passes `--fix` or explicitly requests them. Produce and verify findings before editing, auto-fix only `CONFIRMED` findings unless the user explicitly approves the uncertain behavior, keep every change traceable to a finding, and run narrow verification. Report fixes, skips, and residual risk when the selected output contract permits action metadata; an exact raw JSON findings contract instead returns the final unresolved findings in its requested schema without prose or outcome fields.

When multiple actions are requested, use this order: find and verify; apply safe fixes; reverify and rebuild the final capped finding set from the complete verified pool; prepare the selected report; post comments for unresolved PR findings; create or publish an explicitly requested artifact; then deliver the final report once as the last output action. Never emit a final-channel response before requested tool actions complete. Never emit a pre-fix report when fixes are requested unless active host instructions explicitly require a separate initial reporting phase. Do not create or publish a review artifact by default.
