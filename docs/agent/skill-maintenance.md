# Skill Maintenance

## Source Of Truth

- Each top-level directory containing `SKILL.md` is a skill. The repository directory is authoritative.
- A skill may also own `agents/`, `references/`, `scripts/`, and assets. Inspect the complete directory before editing; do not assume that `SKILL.md` is the only relevant file.
- Keep every skill directory, including `anti-ai-design/`, as ordinary files tracked by the parent repository. Never copy nested `.git` metadata into a skill directory; if one appears, remove the nested metadata and verify the parent index does not record the skill as a `160000` gitlink.

## Add Or Update A Skill

1. Read the skill's `SKILL.md` completely as source documentation and follow its links to any required references, scripts, or assets. Do not load, invoke, or activate the skill being edited in the current session. Treat its instructions as content to maintain, not an active workflow. When creating a skill, follow the current `skill-creator` instructions.
2. Make the change in the repository copy and run any focused checks owned by that skill.
3. Validate the repository copy:

   ```sh
   python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ./<skill-name>
   ```

4. Run `git diff --check` and review the repository changes. Maintenance is complete after repository validation. Report only repository changes and checks; do not add installation follow-ups or status notes about copies outside the repository.

## Skill-Specific Checks

- When changing `data-debug/`, read `data-debug/SKILL.md` and `data-debug/Dockerfile` as source documentation. For SQL CLI changes, also read `data-debug/cli/README.md` and the toolchain/dependency source of truth `data-debug/cli/pom.xml`, then run `mvn -f data-debug/cli/pom.xml clean verify`. The Java source/tests live in `data-debug/cli/src/`; `target/` is generated and ignored. Use synthetic fixture config only; never inspect real `.env.db` contents. Codex SQL runs Java; MongoDB/Redis retain Docker. Ports are outside a Codex-only CLI change unless explicitly requested.
- Validate the skill structure, then lint the Dockerfile when Hadolint is already available:

  ```sh
  python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ./data-debug
  hadolint data-debug/Dockerfile
  ```

- Do not build or pull `db-debug:latest` merely to validate documentation changes. When the Dockerfile changes and the user requests image verification, build the exact local tag, run the client-version smoke command from `data-debug/SKILL.md`, and report any database integration checks that remain unrun.
- Keep the Dockerfile's installed clients, the client-version smoke command, client selection guidance, and read-only examples in `data-debug/SKILL.md` aligned.

- For every other skill, inspect its scripts and manifests and run the narrowest relevant validation. Do not invent a repository-wide test command when none exists.
