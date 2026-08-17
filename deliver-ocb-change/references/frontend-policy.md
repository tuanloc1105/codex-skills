# OCB Frontend Delivery Policy

Apply this policy only to web frontend paths in `frontend` or `mixed` mode, together with [core-policy.md](core-policy.md).

## Acceptance and implementation

Identify authoritative UI acceptance from Jira, linked designs, repository documentation, or an approved plan. Do not invent missing visual requirements. A user-facing change requires acceptance evidence before `CODE_READY`; unresolved criteria or an inaccessible required design source is a **Hard** gate for affected implementation.

Before editing, locate application roots, routes, design system, shared components, state and data-fetching patterns, API contracts, localization, generated files, and nearby tests. Reuse established components and tokens. Do not introduce an alternate UI system or speculative abstraction.

Run repository-mandated checks as **Hard** gates. Select applicable evidence from:

- Focused unit, component, integration, or end-to-end tests
- Lint, typecheck, and production build
- Loading, empty, error, permission, validation, retry, and success states
- Changed-state screenshots or equivalent visual evidence at relevant viewports
- Keyboard, focus, semantics, contrast, and assistive-technology checks
- Supported browser and responsive-layout checks
- Client authorization assumptions, output encoding, URL handling, storage, and sensitive-data exposure

Screenshot, accessibility, browser, and responsive checks are **Advisory** when neither repository rules nor acceptance criteria require them. Record applicability, evidence, skipped checks, and residual risk. Do not expose private designs, credentials, tokens, customer data, or sensitive screenshots.

For a frontend-only change, do not apply backend service/data gates. In `mixed` mode, classify affected paths and keep frontend evidence separate from backend evidence in the workflow contract.

## Readiness additions

`CODE_READY` requires frontend acceptance criteria and required checks to pass, or an explicit allowed override with residual risk. `MR_PREPARED` additionally requires reviewed UI evidence or recorded exceptions and exact frontend diff boundaries.

Frontend scope excludes Backend and Mobile delivery unless the resolved mode is `mixed`, in which case the backend portion follows [backend-policy.md](backend-policy.md).
