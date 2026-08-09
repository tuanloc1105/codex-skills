# Agent Guide

## Start Here

- Each top-level directory containing `SKILL.md` is a skill. Read that file completely before editing the skill, then open linked references, scripts, or assets as needed.
- Each top-level directory containing `.codex-plugin/plugin.json` is a plugin. Treat its complete directory as one installable unit; nested `skills/` are plugin-owned unless explicitly dual-published.
- Treat the repository copy as authoritative. For the complete maintenance workflow, read [docs/agent/skill-maintenance.md](docs/agent/skill-maintenance.md).

## Skill Synchronization

- In the same task that adds or updates a standalone `<skill-name>/`, mirror the complete skill directory to `~/.codex/skills/<skill-name>/` before finishing. Include `SKILL.md`, `agents/`, `references/`, `scripts/`, and assets; exclude only VCS metadata, local-tool metadata, and generated caches. Never update only the installed mirror.
- Validate both copies and verify all non-excluded paths and contents match after syncing.
- Install plugin-owned skills through the complete plugin; do not separately mirror a nested `<plugin>/skills/<skill-name>/` unless the skill is intentionally published in both forms.

## Read On Demand

- Before adding, updating, syncing, or validating a skill, read [docs/agent/skill-maintenance.md](docs/agent/skill-maintenance.md) for the exact workflow, checks, and nested-repository handling.
- Before changing `jarvis/` or another plugin, read [docs/agent/plugin-maintenance.md](docs/agent/plugin-maintenance.md). For Jarvis behavior or distribution, read [jarvis/skills/jarvis/SKILL.md](jarvis/skills/jarvis/SKILL.md), [jarvis/hooks/hooks.json](jarvis/hooks/hooks.json), [jarvis/scripts/install.py](jarvis/scripts/install.py), and its focused tests before editing.
- Before changing a skill-specific workflow under `.github/workflows/`, read [docs/agent/skill-maintenance.md](docs/agent/skill-maintenance.md) and the corresponding skill manifest and test scripts.
- For OCB Jira-to-MR delivery, use [deliver-ocb-frontend-change/SKILL.md](deliver-ocb-frontend-change/SKILL.md) for web frontend work and [deliver-ocb-backend-change/SKILL.md](deliver-ocb-backend-change/SKILL.md) for backend work.
- For Jira Cloud work through Atlassian CLI `acli` or Atlassian Rovo MCP, read [interact-with-jira/SKILL.md](interact-with-jira/SKILL.md) before configuring access, authenticating, selecting a tool, or mutating Jira data.
