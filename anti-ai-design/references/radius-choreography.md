# Radius Choreography

Radius rules for structural hierarchy, nested surfaces, and style-family consistency.

Use this reference whenever the output includes:
- cards inside cards
- panels with inset surfaces
- glassmorphism or premium commerce shells
- nav + toolbar + form + result surfaces in the same screen
- reusable foundation tokens
- multi-screen bundles where consistency matters

---

## Radius Philosophy

Border radius is not decoration. Radius communicates:

1. **Hierarchy** — outer shells, primary surfaces, inset surfaces, controls, and micro-elements should not feel equally soft.
2. **Material** — glass, paper, brutalist, luxury, commerce, and playful products do not use the same curvature grammar.
3. **Containment** — nested surfaces should feel intentionally contained, not duplicated.
4. **Interaction** — controls may share the family language, but they should not blindly inherit panel curvature.

If everything uses the same radius, the UI feels junior and template-like.

---

## Core Governance

### Rule 1 — Use a radius grammar, not random values
One project should typically use:
- 2–4 primary radius tiers
- plus pill radius only where semantically justified

### Rule 2 — Nested surfaces step down
If a child surface sits visually inside a parent surface, the child radius must be **less than or equal to** the parent radius.

### Rule 3 — Same-material nesting must visibly tighten
If both parent and child are part of the same material family (for example glass panel inside glass shell), the child should usually step down by **2–8px**.

### Rule 4 — Controls use control radius
Buttons, inputs, segmented controls, chips, and small nav items should use the **control tier**, not copy the panel radius blindly.

### Rule 5 — Avoid radius inflation
Do not make every card, inset, input, and button look equally rounded. That destroys hierarchy.

### Rule 6 — Pill is special, not default
Use pill radius for:
- badges
- status pills
- segmented chips when the active visual language supports it
- avatars

Do not make every CTA, card, and nav element a pill unless the product direction explicitly calls for it.

---

## Semantic Radius Token Model

Prefer a two-layer system.

### Raw scale
```css
:root {
  --radius-0: 0px;
  --radius-1: 8px;
  --radius-2: 10px;
  --radius-3: 14px;
  --radius-4: 16px;
  --radius-5: 20px;
  --radius-6: 24px;
  --radius-7: 28px;
  --radius-pill: 9999px;
}
```

### Semantic mapping
```css
:root {
  --radius-shell: var(--radius-7);
  --radius-surface: var(--radius-5);
  --radius-inset: var(--radius-4);
  --radius-control: var(--radius-3);
  --radius-tight: var(--radius-2);
  --radius-pill: 9999px;
}
```

Rules:
- `--radius-shell` is for major outer shells and hero wrappers.
- `--radius-surface` is for major cards and section panels.
- `--radius-inset` is for nested proof cards, state panels, preview surfaces, and interior canvases.
- `--radius-control` is for buttons, inputs, nav items, tabs, and actionable tiles.
- `--radius-tight` is for tiny metric wrappers, compact icon plates, or mini utility surfaces.

---

## Recommended Radius by Role

| Role | Typical use |
|---|---|
| `shell` | page shell, hero shell, modal shell, large mobile glass shell |
| `surface` | section card, workspace card, sidebar block, desktop panel |
| `inset` | state panel, proof inset, result canvas, nested card |
| `control` | buttons, inputs, tabs, nav items, clickable share cards |
| `tight` | small chips, icon mounts, tiny metric capsules |
| `pill` | badges, status pills, selective chip systems |

---

## Style-Family Radius Grammar

These are heuristics, not rigid formulas.

### Brutalist / Industrial
- shell: `0–8px`
- surface: `0–6px`
- inset: `0–4px`
- control: `0–8px`
- pill: rarely used

Use structure, borders, and shadow offsets instead of softness.

### Editorial / Luxury
- shell: `20–24px`
- surface: `14–16px`
- inset: `10–12px`
- control: `10–12px`
- pill: selective

Refined, restrained, and never candy-soft.

### Glass / Premium Commerce
- shell: `24–28px`
- surface: `18–20px`
- inset: `14–16px`
- control: `12–14px`
- tight: `8–10px`
- pill: selective for status cues

Outer softness should be clear, but inner surfaces must tighten.

### Playful / Organic
- shell: `28–32px`
- surface: `20–24px`
- inset: `16–18px`
- control: `14–16px`
- pill: common but still controlled

Even in playful products, maintain hierarchy.

### Enterprise / Data-heavy
- shell: `16–20px`
- surface: `12–14px`
- inset: `10–12px`
- control: `8–10px`
- pill: limited

Favor clarity over softness.

---

## Nesting Rules

### Parent/child rule
- child surface radius must never exceed parent radius when visually contained inside it
- if parent and child share the same material family, the child should usually step down

### Suggested step-downs
- light nesting: `2–4px`
- clear inset nesting: `4–8px`
- controls inside a panel: usually `2–6px` below the containing panel tier

### Examples

#### Good
- outer shell `28px`
- primary surface `20px`
- state panel `16px`
- button/input `14px`

#### Bad
- outer shell `24px`
- inner panel `24px`
- button `24px`

#### Also bad
- outer shell `20px`
- child inset `22px`

---

## Component Guidance

### Hero sections
Hero wrappers often tolerate the largest radius on the screen.
If a hero contains an inset board or signal card, that inset should tighten.

### Forms
- form shell: `surface`
- inline state panel: `inset`
- input/button: `control`

### Result boards
- result shell: `surface`
- generated URL panel / proof card: `inset`
- copy/share buttons: `control`

### Navigation systems
- desktop nav item: `control`
- mobile tab item: `control`
- status badges inside nav/header: `pill` or `tight`

### Clickable cards
Interactive cards should usually use `control` or `inset`, depending on size.
Do not give small clickable tiles the same curve as the main shell unless the product is intentionally ultra-soft.

---

## Anti-Patterns

Reject and rework when any of these appear:

- same radius on all major layers
- nested glass cards with equal curvature
- child radius larger than parent radius
- random mix of 8/12/14/16/18/20/24/28 without role discipline
- pill overload on every CTA and nav item
- panel radius copied directly onto tiny controls
- hero section with inner and outer cards equally soft

---

## Self-Audit Checklist

Before finalizing output, verify:

- [ ] The project uses a clear radius grammar with no more than 2–4 primary tiers plus pill
- [ ] Each major role maps to a semantic radius tier
- [ ] Nested surfaces tighten relative to their parent
- [ ] Controls use control-tier radius, not shell radius
- [ ] Child surfaces do not exceed parent curvature
- [ ] Pill radius is used selectively
- [ ] The active style family matches the chosen radius grammar
- [ ] Hero sections do not look like stacked equal-radius demo cards

---

## Recommended Default for Commerce Glass Warm

When the style direction is commerce glass warm, prefer:

```css
:root {
  --radius-shell: 28px;
  --radius-surface: 20px;
  --radius-inset: 16px;
  --radius-control: 14px;
  --radius-tight: 10px;
  --radius-pill: 9999px;
}
```

Use this as the default starting point unless the product context clearly needs a tighter or flatter system.
