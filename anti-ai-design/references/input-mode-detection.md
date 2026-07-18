# Input Mode Detection

Detect the user's input mode before asking design questions or loading heavy references.

## Modes
- `idea_only` — short natural-language prompt with little structure
- `screen_list` — screen names, page list, or flow fragments are given directly
- `docs_driven` — SRD, SRS, PRD, requirements, spec, or markdown docs are referenced
- `artifact_driven` — existing HTML/CSS/JS/screens/bundles are referenced for reuse or extension
- `mixed` — a combination of docs, existing artifacts, and direct user instructions

## Detection Rules
1. If the user references explicit docs or file paths for requirements/specs, prefer `docs_driven`.
2. If the user references existing generated screens or bundles to modify, prefer `artifact_driven`.
3. If the user provides named screens without formal docs, use `screen_list`.
4. If the user provides only a product idea and rough screen count, use `idea_only`.
5. If multiple signals are present, choose `mixed` and route to the minimum required references.

## Output
Produce an internal classification block before generation:

```yaml
input_mode: idea_only
confidence: high
evidence:
  - "design Shopee affiliate"
  - "3 screens"
```

Do not ask style/platform questions until input mode is resolved.
