# Claude Code Review Upstream Crosswalk

Maintenance-only provenance for comparing extracted Claude Code review prompts with this skill. Do not load this reference during ordinary reviews; runtime instructions live in `SKILL.md` and the other routed references.

The comparison source used for this crosswalk contained Claude Code fragments with observed `ccVersion` values from `2.1.147` through `2.1.235`. Version metadata records provenance, not compatibility or authority. Local instructions intentionally win where the fragments conflict.

## Crosswalk

| Upstream fragment or family | Local authoritative section | Status or intentional difference |
| --- | --- | --- |
| `agent-prompt-code-review-minimal-mode.md` | `mode-playbooks.md` — Minimal | Ported contextual pass and 15-finding cap. Rejects the legacy instruction to duplicate typed findings in prose. |
| `agent-prompt-code-review-part-2-low-effort-mode.md` | `mode-playbooks.md` — Low | Ported one-call, hunk-only scope, skipped test/fixture hunks, four-finding cap, and exact `(none)` fallback. |
| `agent-prompt-code-review-part-2-low-effort-minimum-findings-mode.md`; `skill-code-review-low-effort-expanded-findings-mode.md` | `mode-playbooks.md` — Low Minimum | Reconciles conflicting skip behavior, excludes skipped files from the target, and treats the minimum as a search obligation rather than a quota. |
| `agent-prompt-code-review-part-6-medium-effort-mode.md`; `agent-prompt-code-review-part-7-high-effort-mode.md` | `mode-playbooks.md` — Medium and High | Ported 3+5 angles, caps, and precision/recall split. Local fallback retains a separate same-context self-check instead of dedup-only output. |
| `agent-prompt-code-review-part-3-extra-high-and-maximum-effort-modes.md`; `skill-code-review-inline-xhigh-mode.md` | `mode-playbooks.md` — Extra High and Maximum; `deep-sweep.md` | Ported 5+5 angles, recall verification, sweep, and cap. Local maximum spends effort on evidence rather than adding unsupported categories. |
| `agent-prompt-code-review-part-1-base-finder-angles.md`; `skill-code-review-correctness-finder-angles.md` | `finder-angles.md` — Correctness A-C | Ported and expanded with explicit candidate evidence and contract surfaces. |
| `skill-code-review-angle-b-removed-behavior-auditor.md` | `finder-angles.md` — Correctness B | Ported and expanded to cleanup, retries, normalization, rollback, and feature flags. |
| `skill-code-review-angle-c-cross-file-tracer.md` | `finder-angles.md` — Correctness C | Ported and expanded to schemas, migrations, stored data, cancellation, and configuration. |
| `skill-code-review-angle-d-language-pitfall-specialist.md` | `finder-angles.md` — Correctness D | Ported with a broader language-neutral checklist and concrete-instance gate. |
| `skill-code-review-angle-e-wrapper-proxy-correctness.md` | `finder-angles.md` — Correctness E | Ported and expanded to argument, result, error, state, re-entry, instrumentation, and interface-growth correctness. |
| `skill-code-review-efficiency-dimension.md` | `finder-angles.md` — Efficiency | Ported with realistic hot-path, scale, retention, and cheaper-alternative requirements. |
| `skill-code-review-altitude-dimension.md` | `finder-angles.md` — Altitude | Ported with a required concrete sibling path or shared boundary to prevent abstract architecture findings. |
| `skill-code-review-conventions-dimension.md` | `finder-angles.md` — Conventions | Generalized from Claude-specific files to every applicable repository instruction with path, rule, and offending-line evidence. |
| `agent-prompt-code-review-part-4-three-state-verification-phase.md`; `skill-code-review-phase-2-verify-3-state.md` | `verification.md` | Ported and strengthened with decisive evidence, reachability, and confirmation-needed records. |
| `agent-prompt-code-review-part-5-recall-biased-verification-phase.md`; `skill-code-review-phase-2-verify-recall-biased.md` | `verification.md` — Recall Bias | Ported without allowing vague uncertainty to survive. |
| `agent-prompt-code-review-inline-gap-sweep-phase.md`; `skill-code-review-phase-3-sweep-for-gaps.md` | `deep-sweep.md` | Ported and expanded into data, trust, lifecycle, persistence, concurrency, recovery, and compatibility domains. |
| `agent-prompt-code-review-unavailable-agent-inline-mode.md`; `skill-code-review-inline-medium-high-template.md` | `mode-playbooks.md` — Reviewer Orchestration | Ported sequential fallback but rejects the older `dedup only (no verify)` behavior. Same-context verification is disclosed, never called independent. |
| `skill-code-review-phase-0-gather-the-diff.md` | `SKILL.md` — Gather the Diff; `target-resolution.md` | Ported upstream/default/last-commit fallback and extended to exact target types, path filters, untracked additions, deduplication, and commentability. |
| `agent-prompt-code-review-part-10-reportfindings-output-format.md`; `skill-code-review-output-findings-json-array.md`; `tool-description-report-code-review-findings.md` | `reporting-and-actions.md` | Ported caps and no-duplication contract. Caller schema wins; tool availability alone does not select typed output. Severity is emitted only when accepted. |
| `agent-prompt-code-review-part-8-github-comment-posting.md` | `reporting-and-actions.md` — GitHub Inline Comments | Ported opt-in posting and fallbacks; adds duplicate suppression, post-fix revalidation, and commentability checks. |
| `agent-prompt-code-review-part-9-fix-application.md` | `reporting-and-actions.md` — Apply Fixes | Ported explicit opt-in but restricts automatic fixes to `CONFIRMED` findings, requires narrow checks, and preserves the complete survivor pool for backfill. |
| `system-prompt-explain-code-review-ultra.md` | `mode-playbooks.md` — Claude Ultra Compatibility | Keeps ultra Claude-host-only but rejects volatile cached claims such as alias deprecation; current official documentation must be checked. |

## Maintenance Rules

When comparing a newer upstream extraction:

1. Compare behavior, not wording or fragment count.
2. Record the newer observed `ccVersion` range and map only changed behavior.
3. Preserve local safety improvements unless current upstream evidence establishes a better reusable contract.
4. Reconcile contradictions by authority, recency, and observable workflow safety; do not copy both branches into runtime instructions.
5. Update this crosswalk only after the corresponding local instruction and its focused validation are complete.
