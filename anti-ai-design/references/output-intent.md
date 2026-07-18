# Output Intent Mode

Use this reference to decide whether the generated output should behave like a real product, a design concept, or a review artifact.

## Modes
- `real_product`
- `design_concept`
- `review_artifact`

## Default Behavior
- If the user asks for app screens, product UI, landing pages, or a bundle and does not specify otherwise, default to `real_product`.
- If the user asks for a concept, exploration, moodboard, wow-shot, or visual experiment, use `design_concept`.
- If the user explicitly asks for state review, design audit, review board, or handoff inspection, use `review_artifact`.

## Rules
### real_product
- No design-review commentary inside actual product screens
- No state-audit labels or explanatory meta prose in UI
- Screens must read like a real shipped product
- A root launcher/index page is allowed as a utility to open screens quickly
- Unless explicitly requested otherwise, treat `index.html` as a `navigation_hub`, not as a product screen and not as a review canvas
- A navigation hub may be visually lighter and more utilitarian than the product screens it links to

### design_concept
- More expressive compositions allowed
- Still must follow icon, motion, accessibility, and platform rules
- Concept framing should not leak into screens meant to look production-ready

### review_artifact
- Explicit state switchers, notes, and inspection affordances are allowed
- Meta-review language is allowed only because the user explicitly asked for review output

## Output
```yaml
output_intent: real_product
index_mode: navigation_hub
reason: "user asked for real app screens and did not request review output"
```
