# Repository Profile

## Purpose

Use `.ocb/deliver-frontend-change.yaml` only when a target repository needs explicit Frontend Developer overrides. Absence of the file means the defaults in [frontend-policy.md](frontend-policy.md) apply. Use that reference as the sole authority for precedence and default values.

## Schema

Require `version: 1`. Reject unknown keys rather than guessing their meaning. Allow only this structure:

```yaml
version: 1
branch:
  feature_pattern: "<pattern using documented placeholders>"
  hotfix_pattern: "<pattern using documented placeholders>"
  permitted_prefixes:
    - "<prefix>/"
mr:
  title_pattern: "<pattern using documented placeholders>"
  advisory_changed_line_limit: <positive integer>
jira:
  project_mapping:
    story_type: "<local story type>"
    task_type: "<local task type>"
    subtask_type: "<local subtask type>"
    epic_type: "<local epic type>"
frontend:
  application_roots:
    - "<repository-relative path>"
  design_system_paths:
    - "<repository-relative path>"
  generated_paths:
    - "<repository-relative path>"
verification:
  required_commands:
    - "<repository-owned command>"
  ui_evidence:
    - "<repository-relative instruction or evidence path>"
ai_attribution:
  mechanism: "<repository-defined or none>"
  instruction_path: "<repository-relative path>"
evidence:
  paths:
    - "<repository-relative path>"
```

All sections except `version` are optional. Within a present section, allow only the keys shown above.

## Field rules

- Patterns may use only `{jira_id}`, `{username}`, `{task-slug}`, and `{task-title}`. Every branch pattern must contain `{jira_id}`. Resolve the pattern separately with the representative issue fields and the working issue fields; the profile cannot collapse the required two branches into one.
- `permitted_prefixes` may narrow branch prefixes, but the resolved pattern must still contain Jira traceability.
- `advisory_changed_line_limit` must be a positive integer and remains advisory.
- `project_mapping` maps local Jira type labels only. The canonical Story-to-Epic, Task-to-Story-to-Epic, and Subtask-to-Task-to-Story-to-Epic ancestry is fixed and may not be reconfigured.
- `Pilot` remains the fixed base of the representative branch, and the representative branch remains the fixed base and MR target of the working branch. The profile cannot override this topology.
- `application_roots`, `design_system_paths`, `generated_paths`, `ui_evidence`, `instruction_path`, and `evidence.paths` contain repository-relative paths only. They grant no mutation authority.
- `required_commands` must match commands owned by repository manifests, scripts, CI, or documentation. The profile may select applicable checks but may not disable a higher-priority required check.
- `ai_attribution.mechanism` describes a repository-sanctioned mechanism or `none`. Resolve the details from `instruction_path`; never invent a trailer.

## Resolution

1. Apply the precedence defined in [frontend-policy.md](frontend-policy.md).
2. If the profile exists, parse and validate the complete file before relying on it.
3. Compare profile claims with observed repository state and referenced evidence.
4. Fill omitted optional values from the canonical bundled defaults.
5. Record the resolved values and evidence in the `Frontend Workflow Contract`.

Warn before source or Git mutation when:

- The version is unsupported.
- The profile has unknown keys, invalid placeholders, invalid value types, unsafe commands, or paths outside the repository.
- A profile value weakens a hard Jira, acceptance, verification, authorization, evidence, or ownership gate.
- The profile conflicts with observed repository state or higher-priority policy.

Report the conflict as configuration drift. Do not silently ignore the profile or substitute an inferred value. Continue with bundled defaults only after the user explicitly overrides the affected profile gate; record the rejected profile value, warning, override scope, and residual risk. Do not override a higher-priority instruction, ambiguous repository/diff target, unsafe path, or ownership boundary.

## Example: repository with local frontend routing

```yaml
version: 1
frontend:
  application_roots:
    - "apps/web"
  design_system_paths:
    - "packages/ui"
  generated_paths:
    - "apps/web/src/generated"
verification:
  required_commands:
    - "npm run lint"
    - "npm run typecheck"
  ui_evidence:
    - "docs/frontend/visual-review.md"
```

This example supplies repository routing and required checks only. It does not weaken the hard gates or authorize edits, Git delivery, approval, merge, or deployment.
