# Upstream provenance

This skill was adapted from Archify v2.16.0 under the MIT License.

- Upstream project: Archify
- Upstream package path: `archify/`
- Pinned commit: `39a21139a4661203888049d44e3b8c0da13fa576`
- Imported on: 2026-08-30
- Original copyright: Copyright (c) 2026 tt-a1i (Archify)
- Earlier work: Cocoon AI's `architecture-diagram-generator` v1.0, also MIT licensed

The complete upstream MIT notice remains in `LICENSE`. Product and source
attribution in this file and `LICENSE` must not be removed by rebranding.

## Imported package inventory

The initial import copies the complete standalone `archify/` package while
excluding only VCS metadata, `.DS_Store`, Python bytecode, and generated cache
directories. `UPSTREAM_MANIFEST.sha256` records the sorted SHA-256 inventory of
the exact pinned upstream package before local files are added.

- Runtime and CLI: `bin/`, `renderers/`, `delta/`, `migrations/`, `recipes/`
- Contracts and authoring: `SKILL.md`, `schemas/`, `references/`, `examples/`
- Generated sources: `renderers/shared/generated-*.mjs`
- Generation and package tools: `scripts/`, `package.json`, `package-lock.json`
- Verification: `test/`
- Viewer and product assets: `assets/`
- Brand data: `brand-marks/`
- Distribution and legal records: `LICENSE`, `skill-release.json`

## Brand and trademark notice

The imported brand catalogue is retained initially because it is functional
diagram data and its provenance is embedded in the generated catalogue. Most
entries derive from Simple Icons 16.28.0; the OpenAI entry points to official
brand guidance. Brand names and logos may be trademarks of their owners. Their
presence does not imply sponsorship, endorsement, or partnership. Review the
recorded source and applicable brand guidance before adding or updating marks.

## Reproducing the baseline inventory

From the pinned upstream package directory:

```sh
find . -type f \
  ! -path './.git/*' \
  ! -path '*/__pycache__/*' \
  ! -name '.DS_Store' \
  ! -name '*.pyc' \
  -print0 | sort -z | xargs -0 shasum -a 256
```

Compare that output with `UPSTREAM_MANIFEST.sha256`. Later local changes are
described in `LOCAL_MODIFICATIONS.md`; the manifest remains immutable.
