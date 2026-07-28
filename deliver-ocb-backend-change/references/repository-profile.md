# Repository Profile

## Purpose

Use `.ocb/deliver-backend-change.yaml` only when a target repository needs explicit Backend Developer overrides. Absence of the file means the defaults in [backend-policy.md](backend-policy.md) apply. Use that reference as the sole authority for precedence and default values.

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
ai_attribution:
  mechanism: "<repository-defined or none>"
  instruction_path: "<repository-relative path>"
evidence:
  paths:
    - "<repository-relative path>"
```

All sections except `version` are optional. Within a present section, allow only the keys shown above.

## Field rules

- Patterns may use only the documented placeholders: `{jira_id}`, `{username}`, `{task-slug}`, and `{task-title}`. Every branch pattern must contain `{jira_id}`.
- `permitted_prefixes` may narrow branch prefixes, but the resolved pattern must still contain Jira traceability.
- `advisory_changed_line_limit` must be a positive integer and remains advisory.
- `project_mapping` maps local Jira type labels only. The canonical Story-to-Epic, Task-to-Story-to-Epic, and Subtask-to-Task-to-Story-to-Epic ancestry is fixed and may not be reconfigured.
- `ai_attribution.mechanism` describes a repository-sanctioned mechanism or `none`. Resolve the details from `instruction_path`; never invent a trailer.
- `evidence.paths` contains repository-relative paths only. It points to evidence and grants no mutation authority.

## Resolution

1. Apply the precedence defined in [backend-policy.md](backend-policy.md).
2. If the profile exists, parse and validate the complete file before relying on it.
3. Compare profile claims with observed repository state and referenced evidence.
4. Fill omitted optional values from the canonical bundled defaults.
5. Record the resolved values and evidence in the `Backend Workflow Contract`.

Stop before source or Git mutation when:

- The version is unsupported.
- The profile has unknown keys, invalid placeholders, or invalid value types.
- A profile value weakens a hard Jira, authorization, evidence, or ownership gate.
- The profile conflicts with observed repository state or higher-priority policy.

Report the conflict as configuration drift. Do not silently ignore the profile or substitute an inferred value.

## Example: repository with a local Jira type name

```yaml
version: 1
jira:
  project_mapping:
    story_type: "User Story"
    task_type: "Technical Task"
    subtask_type: "Sub-task"
    epic_type: "Epic"
evidence:
  paths:
    - "docs/engineering/delivery.md"
```

This example changes labels only. The required ancestry and all hard gates remain intact.
