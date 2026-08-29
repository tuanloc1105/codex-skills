# Mode Playbooks

Use the playbook selected by the user's requested effort. Default to `medium`. Preserve the user's target, base, focus files, exclusions, and extra instructions in every delegated task and verification pass.

`Verification` below means the mode's contextual candidate-verification phase and may produce a three-state verdict. A focused `action-safety validation` required before a typed, external, or mutating action is narrower: it checks that the affected claim is still supported without widening candidate search, changing the mode, or fabricating a verdict that the output contract does not request.

## Contents

- Minimal
- Low and low expanded
- Medium, high, extra high, and maximum
- Claude ultra compatibility
- Execution backend routing
- Reviewer orchestration and inline fallback

## Minimal

Use this mode for one careful contextual pass without the multi-angle or separate-verifier pipeline.

1. Read the complete unified diff and every changed hunk.
2. Inspect enclosing functions and use focused search, history, blame, callers, callees, tests, or contracts only when they establish intent or reachability.
3. Keep only findings with a concrete triggering input or state and an observable wrong result.
4. Check wrong or inverted conditions, boundaries, nullish paths, missing `await` or return propagation, removed guards or validation, swallowed errors, broken callers, and races; keep only concrete failures.
5. Do not split the work into independent finder angles or claim three-state verification.
6. Keep at most fifteen findings, most severe first.

Use the normal output-selection rules. A typed reporting call is never followed by a duplicate textual list; that canonical no-duplication rule overrides legacy minimal-mode restatement behavior.

## Low

Use this mode for a fast, hunk-only review.

1. Read the changed-file summary and unified diff once.
2. Cover the explicit target first. Otherwise cover committed and uncommitted branch changes.
3. Skip test and fixture hunks under `test/`, `spec/`, `__tests__/`, `fixtures/`, and `testdata/`, plus `*_test.*` and `*.test.*` files.
4. Do not read full files, inspect callers, spawn reviewers, or run verification.
5. Flag only hunk-visible runtime defects, duplicated helpers visible in the diff context, and dead code left by the diff. Check wrong or inverted conditions, off-by-one boundaries, nullish values, falsy zero, missing `await` or return propagation, wrong variables, swallowed errors, and missing escaping only when the failure is visible in the hunk.
6. Apply the normal output-selection rules. The human fallback returns at most four findings, most severe first, as contiguous lines with no heading, bullets, blank separators, or summary:

   ```text
   path/to/file.ext:123 — what's wrong and the concrete failure
   ```

7. The human fallback returns exactly `(none)` when nothing qualifies. A required typed report is called once with the capped findings or an empty array and is not duplicated in prose.

Do not infer behavior from code outside the hunk. Do not report style, naming, generic performance advice, missing tests by itself, or speculative contract drift.

## Low Minimum

Use this mode, also called `low-expanded`, only when the user explicitly requests a minimum number of findings, expanded low output, or exhaustive low-effort coverage.

1. Reuse the `low` scope and search rules, replacing its cap and output steps with the rules below.
2. Target `min(eligible_reviewed_files, 4)` findings without lowering the evidence bar. Exclude skipped test and fixture files from this count.
3. When short of the target, make one additional hunk-only pass over the largest eligible reviewed file and every removed block in eligible hunks.
4. Keep at most eight findings, most severe first.
5. Apply the normal output-selection rules with the eight-finding cap. The human fallback returns contiguous one-line findings with no heading, bullets, blank separators, or summary, or exactly `(none)` when no qualifying finding remains after the extra pass.

Treat the target as a search obligation, never as permission to invent findings.

## Medium

Use this mode for precision-biased review.

1. Gather the diff and inspect enclosing functions, callers, callees, tests, schemas, migrations, flags, config, and contracts only as needed.
2. Run correctness angles A-C and all five supporting angles from `finder-angles.md` independently.
3. Let each angle produce up to six candidates with a nameable failure scenario.
4. Deduplicate candidates after all finder passes.
5. Verify every remaining candidate with the precision-biased rules in `verification.md`.
6. Keep at most eight verified findings, most severe first.

Every reported issue should be something a maintainer would act on. Do not let finders silently drop half-believed candidates; verification owns the final decision.

## High

Use this mode for recall-biased review within the same finder scope as `medium`.

1. Gather contextual evidence and run correctness angles A-C plus all five supporting angles exactly as in `medium`.
2. Let each angle produce up to six candidates.
3. Deduplicate only after all finder passes complete.
4. Pass every candidate with a nameable scenario into recall-biased verification.
5. Default realistic uncertainty to `PLAUSIBLE` unless code refutes it.
6. Keep at most ten verified findings, most severe first.

Favor catching real defects over suppressing uncertain but reachable failure mechanisms.

## Extra High

Use this mode, including the `xhigh` alias, for broad recall with specialist angles and a fresh gap sweep.

1. Run correctness angles A-E and all five supporting angles independently.
2. Let each angle produce up to eight candidates.
3. Deduplicate only after all finder passes complete.
4. Run recall-biased three-state verification for every candidate.
5. Run the complete fresh-review sweep in `deep-sweep.md` against the deduplicated surviving list and accept no more than eight new sweep candidates.
6. Verify every new sweep candidate before reporting it.
7. Keep at most fifteen verified findings, most severe first.

## Maximum

Use the `extra-high` playbook with the same fifteen-finding cap. Spend the additional effort on broader repository evidence, more complete caller and contract tracing, and stronger verification rather than inventing more categories or lowering the evidence bar.

## Claude Ultra Compatibility

Treat `ultra` and `/ultrareview` as requests to explain Claude-host review behavior, not as local effort aliases. Verify volatile availability, alias, fallback, authentication, and pricing details against the current [official Claude ultrareview documentation](https://code.claude.com/docs/en/ultrareview) before answering.

- `/code-review ultra` is a user-triggered, multi-agent Claude cloud operation when the user's account and host expose it. Current plans may include free runs before usage-credit billing.
- `/ultrareview` is a supported alias when the host exposes ultrareview; do not label it deprecated unless current official documentation does.
- With no target it reviews the current local branch bundle; a GitHub pull-request number selects that pull request.
- It requires a Git repository. If the current directory is not one, offer `git init` but do not run it automatically.
- A no-target local-branch review does not require a GitHub remote.
- When cloud ultrareview is unavailable, the Claude host may fall back to its local review behavior.
- Do not attempt to launch a Claude-host review through a tool, subprocess, or shell command from Codex on the user's behalf.
- Offer local `max` when the user wants the closest executable review in this skill.

## Execution Backend Routing

Choose the backend after normalizing the mode and preserving every hard user constraint.

1. Stop after the compatibility explanation for `ultra` or `ultrareview`; never route either name to a local or background execution backend.
2. Use a dedicated background review workflow only when active host instructions expose or require that exact capability and its contract supports the normalized mode. Pass the effort followed by the explicit target and all conversation-level focus, exclusion, and scope instructions. Wait for and consume its final findings payload—verified where the mode requires verification—instead of duplicating the review locally.
3. Without a dedicated workflow, run `minimal` and low modes inline.
4. For `medium` and above, use independent subagents when available and permitted, following the orchestration rules below; otherwise use the same-context inline fallback. Backend availability changes evidence provenance, not the selected mode's finding cap or verification requirement.

Do not treat a generic task, thread, or workflow tool as a dedicated code-review workflow unless its active contract says so.

## Reviewer Orchestration

For `medium` and above, when parallel reviewers are available and permitted:

1. Assign each selected finder angle to an independent reviewer.
2. Give each reviewer the target, user constraints, and a raw diff only when it is small; otherwise give a shared ephemeral indexed diff source plus focused excerpts so every reviewer sees the same scope without duplicating large output. This is internal evidence, not a published review artifact.
3. Do not give a finder another finder's conclusions.
4. Run independent finder tasks concurrently within the available concurrency limit.
5. Assign each deduplicated candidate to a verifier that did not originate it when practical. Preserve finder identifiers internally so this separation can be checked rather than assumed.
6. Give a gap-sweep reviewer the same scoped diff source or excerpts plus the deduplicated findings so it searches only for defects not already listed, including uncovered instances at other locations.

For `medium` and above, when independent reviewers are unavailable:

1. Run the same angles sequentially in one context.
2. Reset the question and evidence for each angle; do not let an earlier conclusion suppress later candidate generation.
3. Deduplicate and re-check each candidate in a separate self-contained pass; do not silently remove the verification phase merely because an independent verifier is unavailable.
4. For `extra-high`, `xhigh`, `max`, and `maximum`, re-read the diff and enclosing functions in a fresh same-context gap sweep for defects not already listed, including uncovered instances of a represented class or mechanism at another location.
5. Do not claim independent verification when only a same-context self-check ran.
6. Disclose in the final response that finder and verification passes ran in the same context because independent reviewers were unavailable.
