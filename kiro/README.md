# Kiro Workflow Modes

This directory is an independent Kiro IDE 1.x / CLI 3.x fork of the repository's tracker-backed discuss, plan, and execute workflows. It publishes three namespaced Agent Skills and a standalone v1 command-hook guard without importing the Codex runtime at execution time.

## Included workflows

- `/workflow-discuss` maintains a workflow-record v4 discussion bundle and its decision/action history.
- `/workflow-plan` creates a reviewed version 4 plan bundle with dependency-aware phase files.
- `/workflow-execute` adopts the exact approved bundle, tracks evidence and scoped actions, and remains active until explicit exit.

The IDE and CLI receive lifecycle enforcement. Kiro Web and Mobile can consume project-exported skills, but those surfaces do not execute local hooks, so they are skill-only and cannot claim mutation enforcement.

## Global installation

Preview an installation without writing:

```bash
python3 kiro/scripts/install.py install --dry-run
```

Install into `KIRO_HOME`, or `~/.kiro` when `KIRO_HOME` is unset:

```bash
python3 kiro/scripts/install.py install
```

Use `--kiro-home <path>` to choose an explicit temporary or alternate home. The installer writes only the three namespaced skill directories, `hooks/workflow-modes.json`, and `workflow-modes/` runtime files. Unrelated skills, hooks, settings, agents, and other Kiro content are preserved.

## Project export

Preview or export a project-owned distribution:

```bash
python3 kiro/scripts/install.py export --project /path/to/project --dry-run
python3 kiro/scripts/install.py export --project /path/to/project
```

The export writes only these paths beneath the selected project's `.kiro/` directory:

```text
.kiro/skills/workflow-discuss/
.kiro/skills/workflow-plan/
.kiro/skills/workflow-execute/
.kiro/hooks/workflow-modes.json
.kiro/workflow-modes/
```

The project marker makes a global workflow hook dormant for that workspace, preventing duplicate guard execution when Kiro merges global and project hooks.

## Safety, backups, and recovery

Every operation validates the complete source bundle, renders a scope-specific hook command, stages and fingerprints all owned files, then replaces files atomically. An identical installation is a no-op. Same-version drift is rejected unless `--force-drift` is explicit.

When owned files already exist, the installer stores an operation backup next to the selected configuration root and reports its path. Restore it with:

```bash
python3 kiro/scripts/install.py rollback \
  --config-root /path/to/.kiro \
  --backup /path/reported/by/install
```

Rollback removes only files listed by that operation and restores only its backed-up workflow-owned files. To uninstall without a prior backup, remove the manifest-listed workflow-owned files individually; never delete the broad `.kiro/` directory.

## Runtime behavior and limitations

- Kiro command-hook JSON is received on stdin. Successful stdout becomes agent context; blocking prompt/tool denials use stderr and a nonzero exit.
- Kiro has no documented compaction hook. The runtime emits a bounded active-mode anchor at every active prompt/tool boundary and reconciles record revisions there.
- Kiro `Stop` cannot be blocked. An uncheckpointed stop persists pending recovery, and subsequent mutation remains denied until synchronization, terminal action/write repair, and checkpoint completion.
- Hook payload aliases are normalized for the documented IDE/CLI forms. A live Kiro smoke test remains required to confirm the installed client supplies and renders those fields exactly as documented.
- IDE 0.x and CLI 2.x legacy hook layouts are unsupported.
- Kiro Specs are intentionally out of scope.

## Manual parity maintenance

The Kiro fork is maintained manually. `kiro/tests/test_parity.py` compares runtime-neutral workflow contracts against the immutable Codex sources and classifies only expected namespace, runtime, and capability adaptations. It reports drift read-only and never rewrites either implementation.

Run all automated checks with:

```bash
python3 -m unittest discover -s kiro/tests -p 'test_*.py'
```
