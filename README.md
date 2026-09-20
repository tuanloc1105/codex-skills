# codex-skills

## Sync skills

Both scripts copy skill directories from this repository to
`~/.codex/skills`. Run them without arguments to sync every top-level
directory that contains a `SKILL.md`, or pass one or more skill names to sync
only those skills. All supplied names are validated before copying starts, so
an invalid name does not leave a partially synced selection.

### macOS and Linux

Requires `rsync`.

```sh
./scripts/sync-skills.sh
./scripts/sync-skills.sh data-debug plan
```

### Windows

Uses the built-in `robocopy.exe` command and supports Windows PowerShell 5.1
and PowerShell 7+.

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\sync-skills.ps1
pwsh -ExecutionPolicy Bypass -File .\scripts\sync-skills.ps1 data-debug plan
```

The scripts update and add files but intentionally leave destination-only
files untouched. They exclude `.git`, `.serena`, `.DS_Store`, `__pycache__`,
and `*.pyc` from the copy.

These scripts sync standalone top-level skills only. They intentionally skip
plugin-owned skills because flattening them would omit plugin hooks and scripts.

## Sync `kiro-skill/` to a live Kiro / Kiro Crew install

`kiro-skill/` holds Kiro-native workflow skills, including the Codex ports of
`discuss`, `plan`, `execute`, `interact-with-git-platform`,
`update-agent-docs`, and `simplify`, plus Kiro-specific coordinators such as
`codex-review` (see [kiro-skill/*/SKILL.md](kiro-skill)). They are not
installed by `sync-skills.sh` above, which only targets `~/.codex/skills`. Use
`scripts/sync-kiro-skill.sh` instead to sync them into a local Kiro Crew
install's own skills directory, `~/.kiro/crew/skills/kiro-skill/<name>/` —
kept in a dedicated `kiro-skill/` namespace, never overwriting KiroCrew's own
`~/.kiro/crew/skills/imported/codex/<name>/` mirror of the original Codex
skills these were ported from.

Requires `rsync`. Run without arguments to sync every skill under
`kiro-skill/`, or pass one or more skill names to sync only those. All
supplied names are validated before copying starts, so an invalid name does
not leave a partially synced selection. After copying, the script re-diffs
source against destination and reports a warning (exit code `2`) if the
mirror drifted.

```sh
./scripts/sync-kiro-skill.sh
./scripts/sync-kiro-skill.sh discuss execute
```

Set `KIRO_SKILLS_DEST` to sync to a different Kiro Crew skills root (for
example, a second machine's mounted home directory) instead of the default
`~/.kiro/crew/skills/kiro-skill`.

## Sync `claude-skill/` to a Claude Code install

`claude-skill/` holds Claude Code ports of the Codex `data-debug`,
`deliver-ocb-change`, `discuss`, `execute`, `interact-with-git-platform`,
`interact-with-jira`, `plan`, `simplify`, `technical-diagrams`, and
`update-agent-docs` skills. They keep their original names, so each installs as
`/<name>` in Claude Code. They are not installed by `sync-skills.sh` above,
which only targets `~/.codex/skills`. Use `scripts/sync-claude-skill.sh` to sync
them into `~/.claude/skills/<name>/` instead.

Requires `rsync`. Run without arguments to sync every skill under
`claude-skill/`, or pass one or more skill names to sync only those. All
supplied names are validated before copying starts. After copying, the script
re-diffs source against destination and reports a warning (exit code `2`) if the
mirror drifted.

```sh
./scripts/sync-claude-skill.sh
./scripts/sync-claude-skill.sh discuss execute
```

Set `CLAUDE_SKILLS_DEST` to sync to a different Claude Code skills root instead
of the default `~/.claude/skills`. Because these ports reuse the source skill
names, syncing overwrites a same-named personal skill already installed there.
