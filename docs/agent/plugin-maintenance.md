# Plugin Maintenance

## Source Of Truth

- A top-level directory containing `.codex-plugin/plugin.json` is a complete plugin source. Keep its manifest, skills, hooks, scripts, tests, and assets together.

## Add Or Update A Plugin

1. Read the current `plugin-creator` and `skill-creator` instructions, the plugin manifest, every changed skill as source documentation, and directly linked hook or script guidance. Do not load, invoke, or activate a skill being edited in the current session.
2. Scaffold new plugins with `plugin-creator`; do not hand-author the initial manifest or marketplace entry.
3. Run the plugin's focused tests, validate each changed nested skill, validate the plugin root, and run `git diff --check`.
4. Review the repository changes. Maintenance is complete after repository validation. Report only repository changes and checks; do not add installation follow-ups or status notes about copies outside the repository.
