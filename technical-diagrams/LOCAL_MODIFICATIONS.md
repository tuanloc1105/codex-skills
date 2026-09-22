# Local modifications

`UPSTREAM_MANIFEST.sha256` is the immutable file-and-content baseline imported
from Archify v2.16.0 at commit
`39a21139a4661203888049d44e3b8c0da13fa576`.

Local changes are maintained in this repository rather than synchronized
automatically with upstream releases. Future upstream work must be reviewed and
adapted manually against the pinned baseline.

## 2026-09-22

- Merged the standalone runtime and focused safety fixes from Archify
  `72c750bb` (`2.17.0-dev.1`) through the v2.16.0 baseline, preserving the
  `technical-diagrams` CLI, environment variables, generated HTML identity,
  Mermaid importer, and disabled upstream update channel.
- Updated the viewer template, schema and validator, local package dependency
  override, browser-evidence contract, diagram examples, and targeted tests.
  Re-rendered packaged HTML examples from their source JSON.
- Kept the local `$discuss`/`$plan`/`$execute` bundle `chart/` placement in
  `SKILL.md`. Archify repository website, publication, and root build tests
  remain outside this standalone package.

## 2026-08-30

- Added `UPSTREAM.md`, `LOCAL_MODIFICATIONS.md`, and
  `UPSTREAM_MANIFEST.sha256` to record provenance and make the import
  reproducible.
- Subsequent rebrand, input-adapter, viewer, compatibility, and test changes
  are tracked by this repository's Git history.
