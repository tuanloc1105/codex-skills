# Docs Intake

Use this reference when the input mode is `docs_driven` or `mixed` with docs.

## Goal
Read the minimum necessary docs and extract only what affects the generated design.

## Prioritized sources
1. Explicit path or file attached by the user
2. SRD / SRS / PRD / requirements docs
3. Screen list, flow, wireframe, or UI notes

## Extract these fields only
- product overview
- user roles
- functional requirements
- screen list
- explicit screen decomposition from the user prompt
- business rules
- platform hints
- design constraints
- flow / navigation
- implementation-target hints

## Rules
- Do not force the user to create docs before design can start.
- If docs are incomplete, ask one concise clarification round only for missing fields that materially affect output.
- Prefer docs as source of truth over chat guesses when there is conflict.
- If docs contain enough structure, skip unnecessary platform/style re-questions when already explicit.
- If the user prompt provides a more explicit screen split than the docs, preserve the user prompt decomposition.

## Output
Create an internal summary block:

```yaml
source_of_truth: docs
docs_used:
  - docs/SRD.md
screens:
  - landing-page
  - mobile-link-generator
  - mobile-result
inferred_from_flow:
  broad_screen: affiliate-link-converter
  split_into:
    - link-generator
    - result
missing_fields:
  - style_direction
```
ory, or post-submit result handling to justify that decomposition.

## Output
Create an internal summary block:

```yaml
source_of_truth: docs
docs_used:
  - docs/SRD.md
screens:
  - landing-page
  - mobile-link-generator
  - mobile-result
missing_fields:
  - style_direction
```
