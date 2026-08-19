# Repository Profile

## Purpose

Use `.ocb/deliver-change.yaml` only for explicit OCB delivery routing and repository overrides. Absence means bundled defaults apply. Resolve precedence through [core-policy.md](core-policy.md).

## Schema

Require `version: 1`. Reject unknown keys. Allow only this structure:

```yaml
version: 1
delivery:
  mode: "<backend, frontend, or mixed>"
  routing:
    backend:
      - "<repository-relative glob>"
    frontend:
      - "<repository-relative glob>"
branch:
  feature_pattern: "<documented placeholders>"
  hotfix_pattern: "<documented placeholders>"
  permitted_prefixes:
    - "<prefix>/"
mr:
  title_pattern: "<documented placeholders>"
  maximum_changed_line_limit: <positive integer no greater than 400>
jira:
  project_mapping:
    story_type: "<local story type>"
    task_type: "<local task type>"
    subtask_type: "<local subtask type>"
    epic_type: "<local epic type>"
backend:
  application_roots:
    - "<repository-relative path>"
  generated_paths:
    - "<repository-relative path>"
frontend:
  application_roots:
    - "<repository-relative path>"
  design_system_paths:
    - "<repository-relative path>"
  generated_paths:
    - "<repository-relative path>"
verification:
  common:
    required_commands:
      - "<repository-owned command>"
  backend:
    required_commands:
      - "<repository-owned command>"
  frontend:
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

All sections except `version` are optional. Within a present section, allow only shown keys.

## Field rules

- `delivery.mode` may be `backend`, `frontend`, or `mixed`. Explicit current user intent and approved/current plans take precedence over it.
- Routing globs classify only authorized target paths. Reject routing that overlaps ambiguously for an affected path unless mode is `mixed` and both policies intentionally apply.
- Branch patterns may use `{jira_id}`, `{username}`, `{task-slug}`, and `{task-title}` only and must contain `{jira_id}` and `{username}`.
- `permitted_prefixes` may narrow prefixes but cannot remove Jira traceability.
- `maximum_changed_line_limit` must be positive and no greater than 400. It may make the default PR-size boundary stricter but cannot weaken or broaden the scoped artifact exception in core policy. Treat the former `advisory_changed_line_limit` key as invalid configuration drift because ordinary PR size is not advisory.
- Jira mapping changes labels only; it cannot change Story/Task/Subtask/Epic hierarchy.
- A profile cannot silently replace, create, or weaken the default Tech-Lead-owned Epic base topology. Any exception requires a recorded user override for the exact fallback branch and action.
- All paths and globs are repository relative and grant no mutation authority. Reject paths escaping the repository.
- Required commands must be owned by repository manifests, scripts, CI, or documentation. A profile cannot disable higher-priority checks.
- AI attribution must reference a repository-sanctioned mechanism; never invent a trailer.

## Resolution

1. Apply core-policy precedence.
2. Parse and validate the complete profile before relying on it.
3. Compare claims with repository state and authoritative evidence.
4. Resolve mode and affected paths using the order in `SKILL.md`.
5. Fill omitted values from bundled defaults.
6. Record values and sources in the `OCB Delivery Workflow Contract`.

Warn before planning or mutation when the version is unsupported; keys, types, placeholders, commands, paths, or routing are invalid; a profile weakens a gate; or it conflicts with observed evidence. Do not silently ignore drift. Continue with bundled defaults or an exact user-selected value only after an explicit scoped override records the warning and residual risk. The override must resolve mode and path classification to exact values rather than leave competing targets ambiguous.

## Legacy profile migration

Treat `.ocb/deliver-backend-change.yaml` and `.ocb/deliver-frontend-change.yaml` as legacy evidence, not authoritative current profiles. If exactly one exists and validates against its former schema, propose its equivalent `.ocb/deliver-change.yaml` values and require explicit approval before relying on them for mutation. If both exist, or legacy and current profiles conflict, report drift and resolve it before `$plan`.
