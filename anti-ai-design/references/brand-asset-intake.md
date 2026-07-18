# Brand Asset Intake

Use this reference when the task names a specific brand, product, existing app, company, reusable design system, or when repo evidence contains established visual assets.

## Goal
Increase design specificity so the output looks like it belongs to the actual product instead of a generic premium demo.

## Asset Priority
1. Existing app/site UI screenshots or codebase surfaces
2. Logo / brand mark
3. Product imagery or category-specific visual evidence
4. Existing token/theme files
5. Official marketing pages or docs visuals

## Rules
- When brand or product evidence exists, prefer it over invented visual symbolism.
- If the repo or prompt already provides UI/code context, lift tone, hierarchy, density, and structural patterns from that evidence.
- Do not invent mascot-like marks, emoji brands, or decorative fake identity when a real product identity already exists.
- For digital products, UI screenshots and existing shells are more important than decorative illustration.
- If no reliable brand evidence exists, proceed with the chosen style direction but state internally that the result is style-led rather than brand-led.

## Internal output
```yaml
brand_specificity_mode: evidence_led
brand_assets_found:
  - existing_ui
  - logo
brand_constraints:
  - preserve existing product naming
  - avoid replacing host iconography without cause
```
