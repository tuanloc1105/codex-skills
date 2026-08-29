# Agent Guide

## Start Here

- Each top-level directory containing `SKILL.md` is a skill. Read that file completely before editing the skill, then open linked references, scripts, or assets as needed.
- Each top-level directory containing `.codex-plugin/plugin.json` is a plugin. Treat its complete directory as one installable unit; nested `skills/` are plugin-owned unless explicitly dual-published.
- Treat the repository copy as authoritative. For the complete maintenance workflow, read [docs/agent/skill-maintenance.md](docs/agent/skill-maintenance.md).

## Skill Synchronization

- In the same task that adds or updates a standalone `<skill-name>/`, mirror the complete skill directory to `~/.codex/skills/<skill-name>/` before finishing. Include `SKILL.md`, `agents/`, `references/`, `scripts/`, and assets; exclude only VCS metadata, local-tool metadata, and generated caches. Never update only the installed mirror.
- Validate both copies and verify all non-excluded paths and contents match after syncing.
- Install plugin-owned skills through the complete plugin; do not separately mirror a nested `<plugin>/skills/<skill-name>/` unless the skill is intentionally published in both forms.
- Jarvis exception: after changing `jarvis/`, do not mirror `jarvis/skills/jarvis/` to `~/.codex/skills/jarvis/`; keep the repository plugin as the source of truth and synchronize it only when the user explicitly requests installation or distribution.
- Workflow Modes exception: after changing `workflow-modes/`, keep the change source-only by default. Do not update its cachebuster, copy it to `~/plugins/workflow-modes/`, modify its marketplace entry, run its installer, or invoke `codex plugin add` unless the user explicitly requests sync or installation. Active tasks may still reference the previous versioned hook cache, so an unsolicited reinstall can break both `PreToolUse` and `Stop`.

## Read On Demand

- Before adding, updating, syncing, or validating a skill, read [docs/agent/skill-maintenance.md](docs/agent/skill-maintenance.md) for the exact workflow, checks, and nested-repository handling.
- For database inspection or troubleshooting, use [data-debug/SKILL.md](data-debug/SKILL.md); keep database operations read-only by default and use only its bundled `db-debug:latest` image workflow.
- Before changing `jarvis/` or another plugin, read [docs/agent/plugin-maintenance.md](docs/agent/plugin-maintenance.md). For Jarvis behavior or distribution, read [jarvis/skills/jarvis/SKILL.md](jarvis/skills/jarvis/SKILL.md), [jarvis/hooks/hooks.json](jarvis/hooks/hooks.json), [jarvis/scripts/install.py](jarvis/scripts/install.py), and its focused tests before editing.
- Before changing a skill-specific workflow under `.github/workflows/`, read [docs/agent/skill-maintenance.md](docs/agent/skill-maintenance.md) and the corresponding skill manifest and test scripts.
- For the direct discussion-to-execution handoff contract, read [discuss/SKILL.md](discuss/SKILL.md), [execute/SKILL.md](execute/SKILL.md), and [plan/SKILL.md](plan/SKILL.md) together; an execution-ready discussion tracker is the single execution record and does not require a duplicate plan file.
- For OCB Jira-to-MR delivery, use [deliver-ocb-change/SKILL.md](deliver-ocb-change/SKILL.md) for backend, web frontend, or mixed work; resolve the delivery mode before planning or mutation and load the applicable domain policy.
- For Jira Cloud work through Atlassian Rovo MCP, the closed REST registry, or Atlassian CLI `acli`, read [interact-with-jira/SKILL.md](interact-with-jira/SKILL.md) first. After changing the registry or its safety contracts, run `python3 interact-with-jira/scripts/validate_rest_registry.py` before the standard source/mirror checks.
