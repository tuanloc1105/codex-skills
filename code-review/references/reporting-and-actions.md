# Reporting and Actions

Use this reference when the caller requests JSON or structured output, typed findings, GitHub comments, fixes, or a shareable artifact. Complete the active mode's search and verification phases first. Before any typed, external, or mutating action, run focused action-safety validation on each affected finding even when the base search mode normally omits a separate verifier. This narrow validation does not expand candidate search, change the selected mode, or create a three-state verdict unless the active output contract requires one.

## Contents

- Output and action state machine
- Ranking and location
- JSON and structured output
- Typed ReportFindings output
- Human-readable output
- Fix application and re-verification
- GitHub inline comments
- Shareable review artifacts
- Action safety

## Output and Action State Machine

Resolve output and actions in this order:

1. Deduplicate, verify, and rank the complete surviving pool. Do not discard findings below the current mode cap yet.
2. When fixes were explicitly requested, select the highest-ranked safe action set under the mode cap, apply fixes, run narrow checks, re-verify affected findings, then rerank the complete pool with final dispositions.
3. Prepare exactly one primary report route:
   1. a caller-supplied JSON schema when no higher-priority active instruction requires another surface;
   2. a typed ReportFindings tool when active instructions require it;
   3. the canonical raw JSON array for an explicit raw-JSON request or a generic structured-output request without another schema;
   4. human-readable findings otherwise.
4. Build the final capped finding list from the complete reranked pool. Unresolved findings take precedence over fixed dispositions, and findings below the initial cutoff backfill slots opened by successful fixes.
5. When comments were explicitly requested, post only unresolved findings that still apply after fixes and re-verification.
6. When an artifact was explicitly requested, build it from the final dispositions and publish it only through an available, authorized publisher.
7. Deliver the selected primary report once, after requested tool actions complete. A final-channel response is always the last output action.

A caller-supplied JSON schema wins over mere tool availability and generic defaults, subject to higher-priority active instructions. Tool availability alone never selects typed reporting. Do not create an artifact, post comments, or edit code merely because the corresponding capability exists.

Treat an initial report and an explicitly requested post-fix re-report as separate reporting phases. Emit at most one primary report in each active phase. When fixes and one final report are requested together, defer that report until after fix application and re-verification.

## Rank and Locate Findings

Rank by user impact and urgency:

1. data loss, security bypass, unrecoverable corruption, or widespread outage;
2. crashes, wrong results, broken primary flows, or compatibility regressions;
3. partial failures, resource exhaustion, race conditions, and operationally significant inefficiency;
4. concrete reuse, simplification, altitude, or convention defects with observable maintenance or runtime consequences, plus exact applicable repository-instruction violations backed by the governing rule path and offending changed line.

Assign an internal severity after verification:

- `critical`: reachable data loss, security bypass, unrecoverable corruption, or widespread outage;
- `high`: crash, wrong result, primary-flow failure, or compatibility regression with material user impact;
- `medium`: partial failure, race, resource exhaustion, or operationally significant inefficiency;
- `low`: actionable maintenance or repository-rule defect with a concrete but bounded consequence.

Severity measures impact, while `verdict` measures evidentiary certainty and `category` identifies the failure class. Keep them independent: neither a `CONFIRMED` verdict nor multiple finder origins automatically raises severity, and a specific `PLAUSIBLE` catastrophic scenario may retain high impact while clearly displaying its uncertainty.

Point `line` at the smallest changed line that demonstrates the defect. Use a context line only when no changed line can represent the cause and the active reporting surface permits it. Keep titles concise and put the concrete failure mechanism in `failure_scenario` or the finding body.

Keep the complete verified survivor pool until all requested fixes and re-verification finish. The active mode cap limits each emitted finding list and the initial automatic-fix action set; it does not permanently discard lower-ranked survivors. After fixes, rerank and backfill from the complete pool so unresolved defects cannot disappear merely because higher-ranked findings were fixed.

Apply the final unresolved-first, sorted, capped set to JSON, typed reporting, human findings, comments, and artifacts. Report fixed or skipped dispositions only when the selected surface permits action metadata, and never let fixed dispositions displace unresolved findings from a capped final list.

## JSON and Structured Output

When the caller supplies an explicit JSON schema, follow that schema exactly and do not add fields it forbids. Do not call ReportFindings or append prose unless a higher-priority active instruction requires another reporting surface.

When the caller asks for raw JSON, a findings array, machine-readable output, or generic structured output without supplying a schema and without an active typed-tool requirement, use the canonical array below. Emit exactly one JSON array and no prose, Markdown wrapper, ReportFindings call, artifact link, action summary, or duplicate finding list.

The canonical array uses exactly these fields:

```json
[
  {
    "file": "path/to/file.ext",
    "line": 123,
    "summary": "One-sentence statement of the defect",
    "failure_scenario": "Concrete input or state and observable wrong behavior"
  }
]
```

Rank the final unresolved findings most severe first and enforce the active finding cap. Emit `[]` when nothing remains unresolved. Do not add internal evidence, verification notes, action outcomes, or convenience fields to the canonical contract. A caller-supplied schema may request fields such as `severity`, `category`, `verdict`, `evidence`, provenance, or action outcomes; populate only the requested fields.

Other explicitly authorized actions may still run before delivery, but they must not change or append to the JSON response. The canonical post-fix array contains only unresolved findings, so successful fixes disappear and skipped still-valid findings remain. When the caller needs fix dispositions, require a caller schema that includes them or use typed or human output. When a comment, fix, or artifact action cannot run, do not break the JSON contract with an explanatory prose suffix.

## Typed ReportFindings Output

Use a typed ReportFindings tool only when active host or review instructions require that tool for the current reporting phase. Mere tool availability, a generic request for structured output, or the existence of findings is insufficient; generic structured output without another schema uses the canonical JSON array above.

When `minimal` or a low mode reaches a required typed report, action-safety-validate each retained finding before the call even though the base search mode omits a separate verifier. This safety pass does not change the mode's search scope or finding cap and does not add `verdict` unless a three-state pass actually ran.

Call the required tool exactly once in that reporting phase with `{level, findings}`. Use this canonical finding shape unless the active tool schema is stricter:

```json
{
  "level": "medium",
  "findings": [
    {
      "file": "path/to/file.ext",
      "line": 123,
      "summary": "Concise defect title",
      "short_summary": "Short defect claim",
      "failure_scenario": "Trigger and observable wrong behavior",
      "category": "correctness",
      "verdict": "CONFIRMED"
    }
  ]
}
```

Make `short_summary` at most 60 characters and express only the claim, without rationale or a consequence clause. Include an additional `"severity": "critical|high|medium|low"` field only when the active tool schema accepts it. Use a short kebab-case `category`, such as `correctness`, `removed-behavior`, `cross-file-contract`, `language-pitfall`, `wrapper-proxy-correctness`, `reuse`, `simplification`, `efficiency`, `altitude`, or `conventions`.

Include `verdict` only when a three-state verification pass ran; action-safety validation alone does not produce a verdict. Do not fabricate one for an unverified minimal or low finding.

Pass findings most severe first, enforce the active cap, and pass an empty `findings` array when nothing survives. Do not print the findings again as prose or raw JSON after the tool call.

Add `outcome` to each finding only when active apply instructions explicitly request a post-fix typed re-report. Set it to the disposition that actually occurred and conform to the active tool schema; do not invent an outcome vocabulary. In that phase, the typed outcomes replace per-finding prose restatements of what was fixed or skipped. Report only non-finding operational metadata afterward when active instructions require it and doing so does not violate the tool contract.

## Human-Readable Output

Use human-readable output when no caller-schema, canonical JSON, or active typed-tool route applies.

Put findings before the summary. For each finding include:

- file and line;
- severity when useful;
- concise defect title;
- triggering input or state and observable wrong behavior;
- why the change causes it;
- category;
- verification verdict when verification ran.

If nothing survives, say so clearly in one line. Preserve the active low-effort playbook's exact `(none)` contract when it applies. Mention only meaningful residual risk, skipped checks, or authorized actions that could not run. Do not pad the response with compliments, a diff walkthrough, or alternate restatements of the same findings.

## Apply Fixes and Re-verify

When the user passes `--fix` or explicitly requests fixes:

1. Complete finding generation and verification before editing.
2. Select the highest-ranked action set under the active mode cap and auto-fix only `CONFIRMED` findings in that set.
3. For a `PLAUSIBLE` finding, either obtain an explicit user decision about the uncertain behavior or perform focused re-verification that upgrades it to `CONFIRMED`; otherwise leave it unresolved.
4. Keep every edit traceable to one finding and preserve intended behavior, repository conventions, and unrelated user changes.
5. Skip a finding when the fix would change intended behavior, require changes well outside the reviewed diff, or prove false during deeper inspection.
6. Record the actual disposition and a concise reason for every non-applied finding.
7. Run the narrowest meaningful test, type check, lint check, or reproduction for each applied fix.
8. Re-read the working tree, re-verify every affected finding, rerank the complete survivor pool, and backfill the final list from findings below the initial cutoff before selecting the report route.

Do not report before fixes when the active contract asks for one final report. If active instructions separately require an initial typed report and a post-fix typed re-report, call the tool once in each phase and include actual `outcome` values only in the post-fix call.

## GitHub Inline Comments

When the user passes `--comment` or explicitly requests comments:

1. Confirm that the target is a GitHub pull request.
2. Complete any requested fixes and re-verification first.
3. Build the comment set from unresolved final findings only.
4. Inspect existing review comments and suppress duplicates before posting.
5. Attach each comment to the relevant changed line.
6. Include a suggestion block only when it completely fixes the issue without hidden edits elsewhere.
7. Post through the first available authorized capability in this order:
   1. the purpose-built GitHub inline-comment capability;
   2. an already-authenticated `gh api` call to the pull-request review-comments endpoint;
   3. the selected local report route as the fallback, with a concise skip reason only when that route permits prose.

If the target is not a pull request, keep the findings local and treat commenting as skipped. Never append a fallback explanation to a raw JSON response or duplicate findings after a typed tool call.

Do not post external comments unless the user explicitly requested them. Do not post comments for findings that were fixed locally and no longer apply.

## Shareable Review Artifacts

Create a review artifact only when the user explicitly passes `--artifact`, asks for a shareable review, or active instructions explicitly require one. Do not create or publish an artifact by default.

Use utilitarian HTML suitable for a review document. Include one section per final finding with:

- repository-relative file path and line;
- one-line summary;
- concrete failure scenario;
- the relevant code snippet.

When no finding survives, make the page body a one-line no-findings state. Do not invent a footer or reproduce a variable placeholder; include an iteration footer only when active instructions provide its exact text.

Publish only when an artifact publisher is available and the request authorizes publishing. If publishing is unavailable, retain the explicitly requested local artifact and report its path only when the selected output route permits prose. Skip artifact creation entirely when the review exists only to feed another tool or workflow that owns its output.

## Action Safety

- Do not expand `--fix` into unrelated cleanup.
- Do not auto-fix a merely `PLAUSIBLE` finding.
- Do not include a suggestion block for a partial fix.
- Do not hide an unverified behavioral decision inside an automatic fix.
- Do not post comments, publish artifacts, push changes, create commits, or open pull requests unless the user explicitly requested that action.
- A request to fix, comment, or publish does not authorize pushing the working tree.
- Preserve unrelated working-tree changes and re-read the tree before reporting completion.
- When output contracts conflict, honor a caller-supplied JSON schema subject to higher-priority active instructions, then required typed reporting, then canonical JSON for generic structured output, then human-readable output; never emit duplicate findings in multiple formats.
