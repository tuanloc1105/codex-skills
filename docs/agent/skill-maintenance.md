# Skill Maintenance

## Source Of Truth

- Each top-level directory containing `SKILL.md` is a skill. The repository directory is authoritative; `~/.codex/skills/<skill-name>/` is its installed mirror.
- A skill may also own `agents/`, `references/`, `scripts/`, and assets. Inspect the complete directory before editing or syncing; do not assume that copying `SKILL.md` is sufficient.
- Exclude `.git`, `.serena`, `.DS_Store`, `__pycache__`, and `*.pyc` from mirror operations and comparisons. Treat any other destination-only path as drift that must be reconciled.
- Keep every skill directory, including `anti-ai-design/`, as ordinary files tracked by the parent repository. Never copy nested `.git` metadata into a skill directory; if one appears, remove the nested metadata and verify the parent index does not record the skill as a `160000` gitlink.

## Add Or Update A Skill

1. Read the skill's `SKILL.md` completely and follow its links to any required references, scripts, or assets. When creating a skill, follow the current `skill-creator` instructions.
2. Make the change in the repository copy and run any focused checks owned by that skill.
3. Validate the repository copy:

   ```sh
   python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ./<skill-name>
   ```

4. Sync the complete skill directory from the repository to the installed mirror. Keep the trailing slashes so the directory contents map correctly. Do not use broad deletion; the mirror may contain destination-only runtime metadata that must be classified first.

   ```sh
   rsync -a \
     --exclude '.git' \
     --exclude '.serena' \
     --exclude '.DS_Store' \
     --exclude '__pycache__' \
     --exclude '*.pyc' \
     ./<skill-name>/ ~/.codex/skills/<skill-name>/
   ```

5. Validate the installed mirror:

   ```sh
   python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/<skill-name>
   ```

6. Verify all skill-owned paths and contents match, then check the repository diff:

   ```sh
   diff -qr \
     -x '.git' \
     -x '.serena' \
     -x '.DS_Store' \
     -x '__pycache__' \
     -x '*.pyc' \
     ./<skill-name> ~/.codex/skills/<skill-name>
   git diff --check
   ```

   No `diff` output means the skill-owned files match. Inspect every reported destination-only path; remove it only after confirming that it is obsolete skill content rather than local metadata, credentials, environment state, or a generated runtime file.

## Skill-Specific Checks

- When changing `manage-databases/scripts/agent-db/`, read its `package.json` and `.github/workflows/manage-databases.yml`, then run:

  ```sh
  cd manage-databases/scripts/agent-db
  npm ci
  npm run check
  npm test
  node ./bin/agent-db.js --help
  ```

- For adapter or platform changes, use `test/adapters-platform.test.js` as the focused portability check. Run `npm run test:integration` against the relevant live database when available; the smoke script and workflow own the required environment contract. If the live service is unavailable locally, report the skipped check and let `.github/workflows/manage-databases.yml` run the complete database matrix.
- Keep `.github/workflows/manage-databases.yml` aligned with the engines exported by `src/adapters/index.js`. The workflow is the source of truth for runtime, runner, action, and container versions; do not duplicate them in agent docs.

- For every other skill, inspect its scripts and manifests and run the narrowest relevant validation. Do not invent a repository-wide test command when none exists.
