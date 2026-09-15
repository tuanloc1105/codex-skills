# Simplify Port Crosswalk (Codex → Kiro)

Maintenance-only provenance for comparing this Kiro `kiro-simplify` skill with the Codex `simplify` skill it was ported from. Do not load it during ordinary simplification work.

Source: `/Users/locvotuan/git/codex-skills/simplify/` (Codex skill), itself derived from an extracted Claude Code simplify prompt per its own `references/upstream-crosswalk.md`. Local Kiro instructions intentionally win where the runtime differs.

| Codex behavior | Kiro authority | Status or intentional difference |
| --- | --- | --- |
| Four cleanup angles | `review-angles.md` | Unchanged: reuse, simplification, efficiency, and altitude. |
| Independent-review subagents via Codex's generic subagent mechanism | `SKILL.md` — Review Independently | Delegation now goes through Kiro Crew's `spawn_run` (batched `tasks`, end-turn-and-wait pattern), gated by `resource_status` for a wide wave. No fixed worker count is claimed or required. |
| Inline fallback when agents are unavailable | `SKILL.md` — Review Independently | Preserved as separate sequential passes with provenance disclosure. |
| Findings include concrete cleanup cost | `SKILL.md` candidate record | Preserved and expanded with invariants, evidence needs, recommendation, and origin. |
| Apply every non-skipped finding | `behavior-preservation.md`; `application-and-verification.md` | Unchanged: only proposals with established behavior preservation are applied automatically. |
| Do not hunt correctness bugs | `SKILL.md` introduction | Unchanged. Behavior checks verify transformations rather than running a separate bug-finder angle. |
| Skip fixes that change intent or expand scope | `target-and-scope.md`; `behavior-preservation.md` | Unchanged, with target manifests, ownership baselines, and explicit decision handling. |
| Brief applied/skipped summary | `application-and-verification.md` — Output | Unchanged, with checks and residual-risk evidence. |
| Question style for `NEEDS_DECISION` | `SKILL.md` — Reconcile and Verify Proposals | Routed through `ask_question` on a dashboard session (ending the turn), or the numbered fallback plus `[OPTIONS: ...]` otherwise, instead of Codex's plain-text question convention. |
| Invoked automatically by the plan/execute workflow | `kiro-execute/references/completion.md` — Required Simplify Pass | Unchanged role: `kiro-execute` calls `kiro-simplify` as its required post-implementation review pass, same scoping rules (session commit range / working-tree diff). |

When the source Codex skill changes, compare behavior rather than wording, and update this Kiro port's runtime instructions accordingly before touching this crosswalk. Do not copy contradictory prompt fragments into the workflow.
