# Plugin Maintenance

## Source Of Truth

- A top-level directory containing `.codex-plugin/plugin.json` is a complete plugin source. Keep its manifest, skills, hooks, scripts, tests, and assets together.
- Plugin-owned skills under `<plugin>/skills/` install through the plugin. Do not copy them independently to `~/.codex/skills/` unless the repository deliberately maintains a standalone distribution too.
- Treat the repository plugin directory as authoritative and the personal plugin directory as an installed copy.

## Add Or Update A Plugin

1. Read the current `plugin-creator` and `skill-creator` instructions, the plugin manifest, every changed skill, and directly linked hook or script guidance.
2. Scaffold new plugins with `plugin-creator`; do not hand-author the initial manifest or marketplace entry.
3. Run the plugin's focused tests, validate each changed nested skill, validate the plugin root, and run `git diff --check`.
4. Sync the complete plugin directory to its local marketplace source, excluding VCS metadata, local-tool metadata, and generated caches. Compare all non-excluded paths and contents afterward.
5. Use the `plugin-creator` marketplace/update workflow instead of hand-editing personal marketplace config. Reinstall the plugin and test it in a new task so Codex reloads its skills and hooks.
6. Review and trust changed non-managed hooks through Codex before relying on them. Never bypass hook trust for normal interactive use.

For Jarvis distribution to another machine, use the repository installer instead
of copying individual hooks or scripts. It installs the complete plugin bundle
and preserves unrelated personal marketplace entries:

```sh
python3 jarvis/scripts/install.py --dry-run
python3 jarvis/scripts/install.py
```

On Windows, use `py -3 .\jarvis\scripts\install.py`. The installer requires the
Codex CLI and intentionally leaves hook review and trust to the user.

## Jarvis Checks

For `jarvis/`, run:

```sh
python3 -m unittest discover -s jarvis/tests -v
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py jarvis/skills/jarvis
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py jarvis
git diff --check
```

Preserve these invariants:

- `jarvis/skills/jarvis/agents/openai.yaml` keeps implicit invocation disabled.
- Dormant hooks emit no output and enforce nothing until the current session explicitly invokes Jarvis.
- An active task requires baseline review before mutation, rescue review after repeated failure signals, scope review when the touched-file budget expands, and final review before normal completion.
- Hook state contains bounded metadata only; do not persist raw prompts, tool responses, secrets, or transcript contents.
- `jarvis/scripts/install.py` remains Python-standard-library-only, installs the complete bundle on Windows, Linux, and macOS, and never bypasses hook trust.
- The installer requires the explicit-only agent config and supervisor prompt, rejects bundle and destination symlinks, retains replaced copies as timestamped backups, and rolls back the bundle if marketplace writing fails.
- A `codex plugin add` failure leaves the new source and marketplace entry in place for a safe rerun; do not report installation success until the CLI exits successfully.
- `PostCompact` must not declare `additionalContextLimit`; that event returns `systemMessage` and Codex warns that it cannot emit `additionalContext`.
- Rerunning the installer with a newer complete bundle and a new manifest cachebuster must replace the previous installed source, preserve it as a backup, and refresh the versioned Codex cache through `codex plugin add`. Changed bundles that reuse the installed version must fail clearly instead of claiming a cache refresh.
