# anti-ai-design

**Cross-platform UI design skill for AI agents** — generates impossibly beautiful, visually distinct screens that defy generic AI aesthetics.

> *"I asked for a dashboard. It looks like it was made by a human."*

An auto-orchestration skill that detects context (project type + target platform), resolves brand color direction, presents curated design options drawn from a catalog of 36 real styles, generates a CJX-ready output bundle with `html/css/js` folders plus frozen foundation tokens, and recovers selectively when you ask for changes.

Enforces **22 banned patterns** and **14 required quality signals** on every generation.

Works with Claude Code, GSD, Gemini CLI, Codex CLI, Cursor, and any Agent Skills Spec-compatible runtime.

---

## What It Does

- **Detects** project type (SaaS, e-commerce, mobile app, portfolio, dashboard), target platform (mobile iOS/Android, tablet, desktop web), and input mode
- **Resolves** brand color direction — user-supplied colors → mood-based palette offer → auto-select best-fit
- **Presents** 2–3 design direction options drawn from a curated catalog of 36 styles across 11 categories and 3 art direction packs
- **Generates** a CJX bundle (`html/` + `css/` + `js/` + `manifest.json`) with foundation tokens frozen at selection time — all follow-up screens stay visually consistent
- **Recovers** selectively — regenerates only the changed aspect, preserves the rest
- **Self-audits** every bundle against a design critique rubric before finalizing

---

## Non-Negotiable Interaction Contract

Before generating any design output, the skill resolves three decisions in order:

1. **Platform scope** — ask the user which platforms: `mobile`, `tablet`, `desktop` (multi-select)
2. **Color direction** — user-supplied exact colors → mood-based palette offer (2–3 options) → auto-select best-fit
3. **Style direction** — present 2–3 style options from the catalog, user picks one

### Execution Modes

| Mode | Behavior |
|------|----------|
| **interactive** | Ask the user for missing choices, wait for response before generating |
| **non_interactive** | Auto-select best-fit palette + recommended style, state what was auto-selected, proceed without blocking |

Non-interactive mode is for one-shot CLI execution, background Codex jobs, and scripted runs.

---

## Output Contract — CJX Bundle

Default output is a **bundle directory**, not a single loose HTML file:

```text
<app-slug>-design/
  index.html              # Navigation hub or review canvas (when needed)
  html/
    landing-page.html
    mobile-<screen>.html
    tablet-<screen>.html
    desktop-<screen>.html
  css/
    foundation.css         # Frozen design tokens only
    shared.css             # Shared primitives, utilities, motion, glass recipes
    landing-page.css
    mobile-<screen>.css
    tablet-<screen>.css
    desktop-<screen>.css
  js/
    app.js                 # Shared UI helpers, state toggles, mock data
    landing-page.js
    mobile-<screen>.js
    tablet-<screen>.js
    desktop-<screen>.js
  manifest.json
```

### Bundle Rules

- Generate files **only for selected platforms** — no tablet files if tablet wasn't chosen
- Landing pages stay semantic (`landing-page.*`); app screens use platform prefixes (`mobile-<screen>.*`)
- Every HTML file references `foundation.css` → `shared.css` → screen CSS → `app.js` → screen JS
- Every generated app screen handles four UX states: **loading**, **empty**, **error**, **success**
- `data-ai-id` on all major structural elements
- Contextual, realistic copy — never lorem ipsum

---

## Auto-Orchestration Flow (5 Phases)

### Phase 1 — Context Detection

Classifies input mode, extracts design-relevant fields from docs/specs, resolves implementation target, synthesizes a working brief, detects brand assets, and resolves platform scope.

### Phase 2 — Color + Design Direction

Resolves color palette first, then presents 2–3 curated style options from the catalog. Marks one as RECOMMENDED. In interactive mode, waits for user choice.

### Phase 3 — Bundle Generation

Applies platform rules, implementation target constraints, radius grammar, UX state completeness, utility-screen realism rules, and all anti-AI design rules. Runs bundle self-audit + aesthetic self-critique before finalizing.

### Phase 4 — Foundation Token Freeze

Extracts exact token values into `css/foundation.css` after the first approved screen. All subsequent screens consume these exact values.

### Phase 5 — Recovery

On change requests, regenerates **only the changed aspect** — does not restart from Phase 1 unless explicitly asked.

---

## Design Styles (36 Styles, 11 Categories)

| Category | Count | Example Styles |
|---|---|---|
| brutalist | 4 | Neo-Brutalist Raw, Kinetic Orange, Yellow Neo-Brutalist, Season 04 Fashion |
| cinematic | 2 | B&W Motion Studio, Cinematic Noir Gallery |
| commerce | 1 | Bold Commerce |
| dark-luxury | 5 | Noir Cinema, Dark Elite Frosted, Gold on Black AI, Red Noir, Immersive Cinematic |
| editorial | 6 | Editorial Luxury, Earthy Organic, Midnight Editorial, Organic Serif, Forest Green Grid, Matte Earth Toned |
| glassmorphism | 3 | Glass Aurora, Obsidian Lime, Slate Atmospheric |
| industrial | 3 | Refined Industrial, Industrial Disruptor, Browser Workspace |
| minimal | 3 | Nordic Minimal, Swiss Precision, Pure Flat |
| playful | 3 | Playful Pop, Soft Pastel Wellness, Tactile Clay |
| poster | 2 | Poster Bold Typography, Golden Charcoal |
| tech | 4 | Cyber Serif, Futurist Holo, Retro Terminal, Synapse Ambient |

## Art Direction Packs

- **Glass Premium** — Liquid glass command center: OLED black, blur(20px), specular highlights, concentric radius cascade. Reference: Apple Liquid Glass, AlignUI.
- **Warm Editorial** — Cream paper, Playfair Display, Kinfolk-meets-Apple-News. Reference: Untitled UI, Shopify Polaris.
- **Neo-Brutalist Light** — Hard grid manifesto: thick borders, zero radius, maximum contrast. Reference: Gumroad redesign, Linear.

## Design Recipes (15 Recipes)

Complete design recipes with icon library assignments, layout patterns, and component specifications. Available in `references/design-recipes-catalog.md`.

---

## Sub-Skill Routing — Reference Files (19 Files)

Load ONLY the file needed for the current phase. **Never load all references at once.**

| Task | Reference File | Description |
|------|---------------|-------------|
| Classify input mode (prompt vs docs vs existing bundle) | `references/input-mode-detection.md` | Input mode detection and classification |
| Extract design-relevant fields from user docs/specs | `references/docs-intake.md` | Docs intake and source-of-truth extraction |
| Handle updates/expansions to existing bundles | `references/update-and-expansion.md` | Change mode resolution for existing designs |
| Resolve output intent (real product vs concept vs review) | `references/output-intent.md` | Output intent classification |
| Resolve implementation target and host stack constraints | `references/implementation-targets.md` | HTML bundle vs SvelteKit vs shadcn/ui vs Ant Design |
| Synthesize internal working brief before generation | `references/working-brief-synthesis.md` | Working brief synthesis protocol |
| Intake brand assets (logo, UI, product) | `references/brand-asset-intake.md` | Brand asset intake and specificity rules |
| Choose design style / art direction | `references/design-styles-catalog.md` | 36 styles across 11 categories |
| Select trend / art pack | `references/design-trends.md` | 6 trends, 3 art direction packs |
| Apply a design recipe | `references/design-recipes-catalog.md` | 15 complete design recipes with icon library reference |
| Apply platform layout rules | `references/platform-rules.md` | Mobile iOS/Android, Desktop, Tablet layout constraints |
| Freeze and inject foundation tokens | `references/foundation-tokens.md` | Token freeze instructions and CSS variable format |
| Enforce radius grammar + nesting hierarchy | `references/radius-choreography.md` | Semantic radius roles, nested surface rules, style-family grammar |
| Enforce motion choreography + interaction intent | `references/motion-choreography.md` | Motion purpose, hover policy, state transitions, platform rules |
| Apply UX / customer journey rules | `references/ux-guidelines.md` | UX enforcement, CJX patterns, state completeness |
| Resolve host-library component patterns | `references/library-patterns.md` | Pattern mapping for SvelteKit, shadcn/ui, Ant Design |
| Enforce bundle asset ownership + manifest audit | `references/output-bundle-rules.md` | Shared-vs-screen asset rules, manifest, self-audit |
| Run aesthetic self-critique before finalizing | `references/design-critique-rubric.md` | Hierarchy, craft, functionality, originality rubric |
| Generate output bundle | `references/output-template.md` | Bundle structure, HTML template, file contract |

---

## Anti-AI Design Rules (22 Banned Patterns)

1. ❌ NO Inter, Roboto, Arial, Helvetica as display/heading fonts
2. ❌ NO generic gradient blob backgrounds (subtle aurora/mesh gradients anchored to corners are OK)
3. ❌ NO tech-blue (#0070f3, #2563eb) as primary without explicit request
4. ❌ NO symmetric 3-column feature grid (icon + title + description × 3)
5. ❌ NO Undraw/Blush-style generic illustrations
6. ❌ NO cheap glassmorphism-on-gradient — use restrained blur + subtle borders for premium glass
7. ❌ NO centered "Welcome to [Product]" hero + single CTA — make it visually dynamic
8. ❌ NO `transition: all` — list properties explicitly
9. ❌ NO box-shadow with blur > 20px (unless trend allows)
10. ❌ NO placeholder images from via.placeholder.com or picsum
11. ❌ NO generic "lorem ipsum" — use contextual realistic copy
12. ❌ NO perfectly symmetrical brutalist layouts — embrace intentional asymmetry
13. ❌ NO default 16px font size everywhere — enforce modular typographic scale
14. ❌ NO standard box-shadows — use multi-layer smooth or stacked card effects
15. ❌ NO standard border-radius — use squircle curves or fully rounded pills
16. ❌ NO emoji icons for UI — use a designated icon library (Heroicons, Phosphor, Tabler, Lucide, Material Symbols)
17. ❌ NO emoji brand marks, mascots, logos, or pictograms masquerading as product identity
18. ❌ NO mixing icon families — pick ONE per project
19. ❌ NO generic icons when specific alternatives exist (e.g., "key" for API keys)
20. ❌ NO absolute-positioned or overlapping content cards as primary structure for utility screens
21. ❌ NO decorative asymmetry that weakens CTA alignment or form scanability on utility screens
22. ❌ NO utility-screen hero typography relying on ultra-tight line-height or theatrical wrapping

## Required Quality Signals (14 Signals)

1. Headings use display font, NEVER body font
2. Color palette has ≥3 distinct hues (no monochrome gray)
3. Icons optically aligned with text baselines (`vertical-align: -0.125em`)
4. Brand marks must be vector-drawn symbols, never emoji glyphs
5. All icons in a view use same weight/stroke-width
6. Icon scale: 18px inline · 24px default · 32px feature · 48px hero
7. Dashboard panels have premium volumetric depth (gradients, layered borders)
8. Every major container has premium effects (stacked cards, inner borders, complex shadows)
9. Landing/marketing pages have ≥1 surprise element (bento grid, masonry, parallax, spotlight border, dock magnification, liquid swipe, stacked cards, text mask reveal)
10. Utility screens: surprise elements stay secondary to working layout
11. Buttons have distinct hover/active/focus states with spring easing + glow effects
12. Spacing follows 4px/8px grid with staggered motion delays
13. All images have descriptive alt text, never empty `alt=""`
14. Utility screens maintain stable reading rails and look credible at target viewport

---

## Responsive Rules

- Ban `h-screen` — use `min-h-[100dvh]` (iOS Safari viewport bug)
- Ban flex percentage math — use CSS Grid; flexbox only for alignment within grid cells
- Every multi-column grid collapses to single-column at <640px
- No hover-dependent interactions on mobile — all critical actions tap-accessible
- Semantic HTML first (`<button>`, `<nav>`, `<main>`, `<section>`) before ARIA
- Touch targets minimum 44px × 44px on mobile
- Fluid scaling with `clamp()` — no rigid breakpoint jumps

## Utility Screen Composition Rules

Applies to generator, result, dashboard, settings, and form-heavy screens:

- Trust, scanability, and alignment before spectacle
- Forms, state canvases, result boards in stable normal-flow layouts
- No overlapping/absolute-positioned content cards as primary structure
- Decorative asymmetry in secondary zones only
- Hero typography reads credibly at target viewport
- If it looks more like a concept poster than a daily-use product screen → regenerate

---

## Cross-Platform Navigation Reference

### Mobile (iOS/Android)
- Glassmorphism floating bottom nav (Telegram/Apple style)
- Floating action buttons, sticky bottom CTAs
- Bottom sheet modals with glass surface
- Dynamic Island / notch clearance (~60px top)
- Thumb-zone CTA placement (bottom 60% of viewport)

### Tablet
- Adaptive sidebar (w-64, collapses to icon rail at 768px)
- 2-column layouts, equal-width cards
- Right drawer panels (glass surface)

### Desktop
- Persistent sidebar (w-64) + horizontal top bar
- Dense 3–4 column grids, compact card heights
- Right-rail command panels and detail panes
- Multi-pane layouts with data tables

---

## Install

### Claude Code / GSD

```bash
git clone https://github.com/huyhoangnhh98/anti-ai-design.git
cp -r anti-ai-design ~/.claude/skills/anti-ai-design
```

Or symlink for live development:

```bash
git clone https://github.com/huyhoangnhh98/anti-ai-design.git
ln -s "$(pwd)/anti-ai-design" ~/.claude/skills/anti-ai-design
```

### Gemini CLI

```bash
git clone https://github.com/huyhoangnhh98/anti-ai-design.git
gemini skills install "$(pwd)/anti-ai-design" --scope user
```

### Codex CLI

```bash
git clone https://github.com/huyhoangnhh98/anti-ai-design.git
cp -r anti-ai-design ~/.agents/skills/anti-ai-design
```

### Cursor / Other Agent Skills Spec Runtimes

Copy to your runtime's skill discovery directory:
- `~/.claude/skills/`
- `~/.gemini/skills/`
- `~/.cursor/skills/`
- `~/.agents/skills/`

---

## Usage

### Auto-activation

```
Use anti-ai-design to design a SaaS onboarding flow for mobile Android.
```

```
Design a dashboard for my analytics app. Glass Premium style with Telegram bottom nav.
```

```
Make this landing page look better — warm editorial, cream paper feel.
```

### Workflow

1. **Context Detection** → identifies project type + platform + input mode + implementation target
2. **Color + Design Direction** → resolves palette, presents 2–3 style options, waits for choice
3. **Bundle Generation** → CJX bundle with anti-AI rules + UX states + self-audit
4. **Token Freeze** → locks foundation tokens for cross-screen consistency
5. **Recovery** → selective regeneration on change requests

---

## Skill Contents

```
anti-ai-design/
├── SKILL.md                                  # Entry point — orchestration flow + all rules
├── README.md
├── LICENSE
└── references/
    ├── input-mode-detection.md               # Input mode classification
    ├── docs-intake.md                        # Design-relevant field extraction from docs/specs
    ├── update-and-expansion.md               # Change mode resolution for existing bundles
    ├── output-intent.md                      # Output intent (real_product / design_concept / review_artifact)
    ├── implementation-targets.md             # HTML bundle vs SvelteKit vs shadcn/ui vs Ant Design
    ├── working-brief-synthesis.md            # Internal working brief synthesis
    ├── brand-asset-intake.md                 # Brand asset intake and specificity rules
    ├── design-styles-catalog.md              # 36 styles across 11 categories
    ├── design-trends.md                      # 6 trends + 3 art direction packs
    ├── design-recipes-catalog.md             # 15 design recipes with icon library reference
    ├── platform-rules.md                     # Mobile iOS/Android, Desktop, Tablet constraints
    ├── foundation-tokens.md                  # Token freeze protocol + CSS variable format
    ├── radius-choreography.md                # Semantic radius roles, nesting hierarchy
    ├── motion-choreography.md                # Motion purpose, hover policy, state transitions
    ├── ux-guidelines.md                      # UX enforcement, CJX patterns, state completeness
    ├── library-patterns.md                   # Host-library component pattern mapping
    ├── output-bundle-rules.md                # Asset ownership, manifest, bundle self-audit
    ├── design-critique-rubric.md             # Aesthetic self-critique rubric
    └── output-template.md                    # Bundle structure, HTML template, file contract
```

---

## Requirements

- Any Agent Skills Spec-compatible runtime (Claude Code, GSD, Gemini CLI, Codex CLI, Cursor, etc.)
- No build step — pure markdown + prompt engineering
- No external API calls — all processing is in-context

---

## License

MIT License — see [LICENSE](LICENSE)
