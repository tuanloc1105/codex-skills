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

- Branch patterns may use only `{jira_id}`, `{task-slug}`, and `{task-title}`; they must not include a username. Every branch pattern must contain `{jira_id}`. Resolve the pattern separately with the representative issue fields and the working issue fields; the profile cannot collapse the required two branches into one.
- `permitted_prefixes` may narrow branch prefixes, but the resolved pattern must still contain Jira traceability.
- `advisory_changed_line_limit` must be a positive integer and remains advisory.
- `project_mapping` maps local Jira type labels only. The canonical Story-to-Epic hierarchy, verified Task-to-representative-Story relationship within the same Epic, and Subtask-to-Task hierarchy are fixed and may not be reconfigured. A Jira schema may express the Task-to-Story relationship through a supported parent or an explicit development/implementation relationship.
- `Pilot` remains the fixed base of Story branches. Task branches remain based on and targeted to their verified representative Story branches; Subtask branches remain based on and targeted to their direct-parent Task branches. A Task branch may be reused as the representative branch for its direct Subtasks. The profile cannot override this topology.
- `ai_attribution.mechanism` describes a repository-sanctioned mechanism or `none`. Resolve the details from `instruction_path`; never invent a trailer.
- `evidence.paths` contains repository-relative paths only. It points to evidence and grants no mutation authority.

## Resolution

1. Apply the precedence defined in [backend-policy.md](backend-policy.md).
2. If the profile exists, parse and validate the complete file before relying on it.
3. Compare profile claims with observed repository state and referenced evidence.
4. Fill omitted optional values from the canonical bundled defaults.
5. Record the resolved values and evidence in the `Backend Workflow Contract`.

Warn before source or Git mutation when:

- The version is unsupported.
- The profile has unknown keys, invalid placeholders, or invalid value types.
- A profile value weakens a hard Jira, authorization, evidence, or ownership gate.
- The profile conflicts with observed repository state or higher-priority policy.

Report the conflict as configuration drift. Do not silently ignore the profile or substitute an inferred value. Continue with bundled defaults only after the user explicitly overrides the affected profile gate; record the rejected profile value, warning, override scope, and residual risk. Do not override a higher-priority instruction, ambiguous repository/diff target, unsafe path, or ownership boundary.

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
