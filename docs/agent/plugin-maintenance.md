# Plugin Maintenance

## Source Of Truth

- A top-level directory containing `.codex-plugin/plugin.json` is a complete plugin source. Keep its manifest, skills, hooks, scripts, tests, and assets together.
- Plugin-owned skills under `<plugin>/skills/` install through the plugin. Do not copy them independently to `~/.codex/skills/` unless the repository deliberately maintains a standalone distribution too.
- Treat the repository plugin directory as authoritative and the personal plugin directory as an installed copy.

## Add Or Update A Plugin

1. Read the current `plugin-creator` and `skill-creator` instructions, the plugin manifest, every changed skill as source documentation, and directly linked hook or script guidance. Do not load, invoke, or activate a skill being edited (or its installed copy) in the current session.
2. Scaffold new plugins with `plugin-creator`; do not hand-author the initial manifest or marketplace entry.
3. Run the plugin's focused tests, validate each changed nested skill, validate the plugin root, and run `git diff --check`.
4. Review the repository changes. Plugin edits do not authorize synchronization or reinstallation; leave installed copies untouched unless the user explicitly requests installation or synchronization.

## Explicit Installation Or Synchronization

Only perform these steps when the user explicitly requests installation or synchronization:

1. Sync the complete plugin directory to its local marketplace source, excluding VCS metadata, local-tool metadata, and generated caches. Compare all non-excluded paths and contents afterward.
2. Use the `plugin-creator` marketplace/update workflow instead of hand-editing personal marketplace config. Reinstall the plugin and test it in a new task so Codex reloads its skills and hooks.
3. Review and trust changed non-managed hooks through Codex before relying on them. Never bypass hook trust for normal interactive use.
