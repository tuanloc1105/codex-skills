# Archify v2.16.0 parity map

Baseline: Archify v2.16.0 at commit
`39a21139a4661203888049d44e3b8c0da13fa576`.

## Preserved or renamed

- Typed schemas, generated validators, five renderers, deterministic goldens,
  negative/property tests, geometry/composition diagnostics, delivery safety,
  viewer runtime, export behavior, browser visual-check, repository evidence,
  engineering profiles, brand capture, migrations, and ordinary-model-floor
  tests remain in `test/` with product identifiers renamed.
- Fixed-v1 SVG hashes were refreshed after reviewing the product-only ID and
  metadata substitutions; topology and geometry fixtures remain unchanged.
- CLI, package, environment, HTML namespace, receipt, and viewer assertions now
  target `technical-diagrams` and the valid `TechnicalDiagrams` runtime object.

## Replaced by adaptation-specific equivalents

- Mermaid prose-only ingestion is replaced by `import-mermaid.test.mjs`, which
  validates flowchart, architecture routing, sequence, lifecycle, Unicode,
  long labels, branches, returns, retries, structured errors, and generated
  schema acceptance.
- Legacy Mermaid CLI rendering is replaced by
  `mermaid-flowchart/test/compatibility.test.mjs`, proving permanent alias
  routing and a single canonical validator/renderer.
- Upstream update-notification behavior is replaced by a deterministic local
  disabled receipt because this pinned adaptation owns no update service.
- Monorepo golden paths are replaced by standalone packaged-fixture goldens.

## Intentionally excluded from standalone runtime parity

- Upstream repository website, landing page, guide/gallery builders, README
  badges/showcase copy, community submission links, release publication
  identity, stable update manifest/network notifier, Cursor archive, zip staging,
  and root-level release scripts. These are Archify distribution-site concerns,
  not compiler/viewer behavior, and their parent assets are not packaged here.
- Cross-platform CI jobs cannot run locally. Portability is covered by the
  inherited Node/path tests and installed-package smoke; Windows/Linux CI remains
  a distribution follow-up if this repository later publishes the skill.
- Tests requiring an unrelated pinned external repository remain evidence-only
  unless that repository is supplied; they do not gate local diagram semantics.

No schema, compiler, validator, delivery-safety, geometry, viewer, browser,
package-smoke, importer, or legacy-routing contract is excluded.
