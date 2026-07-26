# codex-skills

## Sync skills

Both scripts copy skill directories from this repository to
`~/.codex/skills`. Run them without arguments to sync every top-level
directory that contains a `SKILL.md`, or pass one or more skill names to sync
only those skills.

### macOS and Linux

Requires `rsync`.

```sh
./scripts/sync-skills.sh
./scripts/sync-skills.sh data-debug plan-mode
```

### Windows

Uses the built-in `robocopy.exe` command and supports Windows PowerShell 5.1
and PowerShell 7+.

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\sync-skills.ps1
pwsh -File .\scripts\sync-skills.ps1 data-debug plan-mode
```

The scripts update and add files but intentionally leave destination-only
files untouched. They exclude `.git`, `.serena`, `.DS_Store`, `__pycache__`,
and `*.pyc` from the copy.
