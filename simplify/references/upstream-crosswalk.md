# Claude Simplify Upstream Crosswalk

Maintenance-only provenance for comparing extracted Claude Code simplify prompts with this skill. Do not load it during ordinary simplification work.

The compared extraction contained `agent-prompt-simplify-slash-command.md` at observed `ccVersion` `2.1.154` and `agent-prompt-simplify-unavailable-agent-inline-mode.md` at observed `ccVersion` `2.1.213`. Local instructions intentionally win where safety or host capabilities differ.

| Upstream behavior | Local authority | Status or intentional difference |
| --- | --- | --- |
| Four cleanup angles | `review-angles.md` | Reuse, simplification, efficiency, and altitude are preserved. |
| Four agents launched concurrently | `SKILL.md` — Review Independently | Preserves independent angles but schedules within actual concurrency; no fixed worker count is claimed or required. |
| Inline fallback when agents are unavailable | `SKILL.md` — Review Independently | Preserved as separate sequential passes with provenance disclosure. |
| Findings include concrete cleanup cost | `SKILL.md` candidate record | Preserved and expanded with invariants, evidence needs, recommendation, and origin. |
| Apply every non-skipped finding | `behavior-preservation.md`; `application-and-verification.md` | Strengthened: only proposals with established behavior preservation are applied automatically. |
| Do not hunt correctness bugs | `SKILL.md` introduction | Preserved. Behavior checks verify transformations rather than running a separate bug-finder angle. |
| Skip fixes that change intent or expand scope | `target-and-scope.md`; `behavior-preservation.md` | Preserved and strengthened with target manifests, ownership baselines, and explicit decision handling. |
| Brief applied/skipped summary | `application-and-verification.md` — Output | Preserved with checks and residual-risk evidence. |

When a newer extraction is available, compare behavior rather than wording, record its observed version, and update runtime instructions before this crosswalk. Do not copy contradictory prompt fragments into the workflow.
