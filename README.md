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
./scripts/sync-skills.sh data-debug plan
```

### Windows

Uses the built-in `robocopy.exe` command and supports Windows PowerShell 5.1
and PowerShell 7+.

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\sync-skills.ps1
pwsh -File .\scripts\sync-skills.ps1 data-debug plan
```

The scripts update and add files but intentionally leave destination-only
files untouched. They exclude `.git`, `.serena`, `.DS_Store`, `__pycache__`,
and `*.pyc` from the copy.

These scripts sync standalone top-level skills only. They intentionally skip
plugin-owned skills such as `jarvis/skills/jarvis`; flattening that directory
would omit the plugin hooks and scripts.

## Install Jarvis

Jarvis installs as a complete plugin. Copy or clone this repository (or at
least the complete `jarvis/` directory) to the target machine; `install.py`
is not a standalone payload. Its Python 3.8+ installer copies the whole
bundle to the current user's personal plugin directory, safely updates the
personal marketplace, and asks Codex CLI to install or refresh the plugin.
Rerun the same command with a newer complete `jarvis/` bundle and a new manifest
version/cachebuster to update an existing installation. The installer replaces
the installed source before refreshing Codex's versioned plugin cache. It is
idempotent for identical bundles and rejects changed bundles that reuse the
installed version, preventing Codex from silently retaining stale cached hooks.

On macOS or Linux, run:

```sh
python3 jarvis/scripts/install.py
```

On Windows PowerShell, run:

```powershell
py -3 .\jarvis\scripts\install.py
```

Pass `--dry-run` to validate the bundle, marketplace, and Codex CLI discovery
without changing the machine. If `codex` is not on `PATH`, pass
`--codex <path-to-executable>`.

When replacing an existing copy, the installer retains a timestamped sibling
backup under `~/plugins/`. If marketplace writing fails, it restores that copy.
If `codex plugin add` fails, the new source and marketplace entry remain ready
so the installer can be rerun after fixing the reported CLI error. Review old
backup directories manually before removing them.

Open a new task after installation so Codex reloads the skill and hooks. Review
and trust the Jarvis hooks through `/hooks` before invoking `$jarvis`.
