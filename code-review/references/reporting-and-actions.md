# Reporting and Actions

Use this reference when the caller requests structured findings, GitHub comments, or fixes. Complete candidate verification before performing external or mutating actions.

## Rank and Locate Findings

Rank by user impact and urgency:

1. data loss, security bypass, unrecoverable corruption, or widespread outage;
2. crashes, wrong results, broken primary flows, or compatibility regressions;
3. partial failures, resource exhaustion, race conditions, and operationally significant inefficiency;
4. concrete reuse, simplification, altitude, or convention defects with observable maintenance or runtime consequences.

Point `line` at the smallest changed line that demonstrates the defect. Use a context line only when no changed line can represent the cause and the reporting surface permits it. Keep titles concise and state the failure mechanism in the body.

Respect the active mode's finding cap. When more findings survive, keep the most severe and highest-confidence set.

## Human-Readable Findings

Put findings before the summary. For each finding include:

- file and line;
- severity when useful;
- concise defect title;
- triggering input or state and observable wrong behavior;
- why the change causes it;
- category;
- verification verdict when verification ran.

If nothing survives, say so clearly. Mention only meaningful residual risk and skipped verification; do not pad the response with compliments or a diff walkthrough.

## Structured Findings

When a ReportFindings-style tool exists or the caller requests structured output, call it exactly once with `{level, findings}`.

Use:

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

Make `short_summary` at most 60 characters and express only the claim, without rationale or a consequence clause. Use a short kebab-case `category`, such as `correctness`, `removed-behavior`, `cross-file-contract`, `language-pitfall`, `wrapper-proxy-correctness`, `reuse`, `simplification`, `efficiency`, `altitude`, or `conventions`.

Use an empty `findings` array when nothing survives. Do not print a duplicate textual findings list after the tool call.

## GitHub Inline Comments

When the user passes `--comment` or explicitly requests comments:

1. Confirm that the target is a GitHub pull request.
2. Produce and verify the final findings list first.
3. Post one inline comment per finding through the available GitHub inline-comment capability.
4. Attach the comment to the relevant changed line.
5. Include a suggestion block only when it fully fixes the issue without hidden edits elsewhere.
6. Avoid posting duplicate comments already present on the pull request.

If the preferred inline-comment capability is unavailable, use an appropriate configured GitHub API or CLI. If no posting capability is available, print the findings and state that posting was skipped. If the target is not a pull request, keep the findings local and state that commenting was ignored.

Do not post external comments unless the user explicitly requested them.

## Apply Fixes

When the user passes `--fix` or explicitly requests fixes:

1. Complete finding generation and verification before editing.
2. Apply each valid correctness, reuse, simplification, efficiency, altitude, and conventions fix to the working tree.
3. Keep every edit traceable to a verified finding.
4. Preserve intended behavior and repository conventions.
5. Skip a finding when the fix would change intended behavior, require changes well outside the reviewed diff, or the finding is false after deeper inspection.
6. Record a concise reason for every skipped finding.
7. Run the narrowest meaningful tests, type checks, lint, or reproduction for the applied fixes.
8. Report fixed findings, skipped findings, checks run, checks skipped, and residual risk.

When a structured findings tool is required, call it after applying fixes so the reported set reflects final dispositions. Do not duplicate its finding list in prose; report only fix status, skips, and verification results.

## Action Safety

- Do not expand `--fix` into unrelated cleanup.
- Do not post comments, push changes, create commits, or open pull requests unless the user requested those actions.
- Do not include a suggestion block for a partial fix.
- Do not hide an unverified behavioral decision inside an automatic fix.
- Re-read the working tree before reporting completion so unrelated user changes remain untouched.
