---
name: anti-ai-design
description: "Auto-orchestrating UI design skill that prevents generic AI-generated output. Detects project context and target platform, explicitly asks the user which platforms to design for, resolves brand color direction through user choice or auto-selection, presents curated design style options, and generates a CJX-ready output bundle with html/css/js folders plus frozen foundation tokens for visual consistency. Use when asked for: UI design, landing pages, dashboards, app screens, product pages, onboarding flows, or any visual interface output. Enforces 18 banned patterns and 12 required quality signals inline on every generation."
metadata:
  version: "1.1.0"
  author: claudible
---

# anti-ai-design

Auto-orchestrating UI design skill with mandatory anti-AI rules. Produces impossibly beautiful, visually distinct screens — never the generic AI-looked output.

## When to Use

Activate this skill whenever the user asks for:

- A landing page, hero section, or marketing screen
- A dashboard, admin panel, or data-rich interface
- A mobile app screen (iOS, Android) or responsive web UI
- An onboarding flow, signup form, or product walkthrough
- Any component library or design system screen
- "Make it look better", "redesign this", "create a UI for…"

## Non-Negotiable Interaction Contract

Before generating any design output, you MUST resolve these three decisions in order:

1. **Platform scope** — ask the user which platforms to generate for: `mobile`, `tablet`, `desktop`.
   - Multi-select is allowed.
   - If the user chooses only `mobile` and `desktop`, do NOT generate `tablet`.
   - If the platform is already explicitly stated and unambiguous, confirm by restating it and proceed.
2. **Color direction** — resolve brand color direction using this order:
   - If the user supplied exact colors, use them.
   - Else if the user supplied a brand/theme mood, offer 2–3 suitable palette directions and ask them to choose.
   - Else auto-select a palette that fits the product category and state clearly that it was auto-selected.
3. **Style direction** — present 2–3 style options and have the user choose one.

Do not skip these decisions unless the conversation already contains an unambiguous answer.

## Execution Mode

### Interactive (default)
- Ask the user for each missing choice in sequence: platform → color → style.
- Wait for their response before proceeding to the next phase.
- Present option cards for style direction with a RECOMMENDED label.

### Non-Interactive
Activate when the user:
- invokes the skill with `mode: non_interactive` or equivalent flag,
- is running a one-shot CLI command, background Codex job, or scripted pipeline, or
- provides a prompt with no prior conversational context (no chat turns before the request).

**Auto-selection rules (applied in order):**
1. **Platform** — if not stated, default to `desktop`. If mobile-first signals exist (mobile app description, React Native mention, "phone" context), default to `mobile`.
2. **Color direction** — select the best-fit palette for the detected project type without offering alternatives.
3. **Style direction** — from the 2–3 candidate styles for this project context, select the one that would be marked RECOMMENDED. Do not present option cards.

**Required output header before generating (non-interactive only):**

```
Auto-selected:
- Platform: [selected platform(s)]
- Palette: [palette name] — primary [hex value]
- Style: [style name] — [one-sentence vibe]
Proceeding to bundle generation.
```

Do not ask clarifying questions. Do not present option cards. Proceed directly to Phase 3 after the header.

## Output Contract — CJX Bundle, Not Single Loose HTML

Default output is a **bundle directory** for the project, not a single loose HTML file.

```text
<app-slug>-design/
  html/
    landing-page.html
    mobile-<screen>.html
    tablet-<screen>.html
    desktop-<screen>.html
  css/
    foundation.css
    shared.css
    landing-page.css
    mobile-<screen>.css
    tablet-<screen>.css
    desktop-<screen>.css
  js/
    app.js
    landing-page.js
    mobile-<screen>.js
    tablet-<screen>.js
    desktop-<screen>.js
```

### Bundle Rules

- `html/` contains one HTML file per generated screen/platform combination.
- `css/foundation.css` contains the frozen design tokens only.
- `css/shared.css` contains shared primitives, utilities, motion, glass recipes, focus states, and common layout patterns.
- Screen-specific CSS goes into a screen-specific file.
- `js/app.js` contains shared UI helpers, state toggles, mock data handling, and accessibility-safe interactions.
- Screen-specific JS goes into a screen-specific file only if needed.
- If the user asks for a single-file export later, you may additionally provide a self-contained HTML export, but the default contract is the CJX bundle.

### Platform File Naming Rules

- Landing pages stay semantic: `landing-page.html`, `landing-page.css`, `landing-page.js`
- App screens use platform prefixes:
  - `mobile-<screen>.html`
  - `tablet-<screen>.html`
  - `desktop-<screen>.html`
- Generate files only for the selected platforms.
- If the user selected `mobile` and `desktop`, the output bundle must not contain any `tablet-*` files.

### Why Separate Files Instead of One Responsive HTML

Use separate platform files by default because:

- each platform can have materially different IA, navigation, density, and CTA placement,
- review and handoff are easier when each target is isolated,
- CJX verification is clearer when the screen intent is explicit,
- desktop/tablet/mobile often need different hierarchy, not just different breakpoints.

A single responsive HTML is only acceptable when the user explicitly requests one-file delivery.

## Sub-Skill Routing

Load ONLY the reference file needed for the current step. Do NOT load all files at once.

| Task | Load | Details |
|------|------|---------|
| Choose design style / art direction | `references/design-styles-catalog.md` | 36 styles across 11 categories |
| Select trend / art pack | `references/design-trends.md` | 6 trends, 3 art direction packs |
| Apply a design recipe | `references/design-recipes-catalog.md` | 15 complete design recipes |
| Apply platform layout rules | `references/platform-rules.md` | Mobile/iOS 26/Desktop/Tablet rules |
| Freeze and inject foundation tokens | `references/foundation-tokens.md` | Token freeze instructions and format |
| Enforce radius grammar + nesting hierarchy | `references/radius-choreography.md` | Semantic radius roles, nested surface rules, style-family radius grammar |
| Apply UX / customer journey rules | `references/ux-guidelines.md` | UX enforcement, CJX patterns |
| Enforce motion choreography + interaction intent | `references/motion-choreography.md` | Motion purpose, hover policy, state transitions, platform motion rules |
| Enforce bundle asset ownership + manifest audit | `references/output-bundle-rules.md` | Shared-vs-screen asset rules, manifest, self-audit |
| Generate output bundle | `references/output-template.md` | Bundle structure, HTML template, file contract |

---

## Auto-Orchestration Flow

Execute these phases in sequence. Each phase has conditional logic — follow it precisely.

### Phase 1 — CONTEXT DETECTION

1. Scan the conversation and any attached files for: project name, existing brand colors, fonts, tech stack, target platform, and screen purpose.
2. Classify **project type** as one of: SaaS product · e-commerce · mobile app · portfolio · dashboard · marketing site · other.
3. Extract requested screens and count them.
4. Resolve **platform scope** as one or more of: `mobile`, `tablet`, `desktop`.
5. **If platform scope is missing or ambiguous:** ask exactly one platform-selection question with multi-select choices:
   - Mobile
   - Tablet
   - Desktop
6. If the user already specified platforms, do not re-ask — carry those forward exactly.
7. Note any existing brand tokens (colors, fonts, spacing scale) found in the project — you will use them in token freeze later.
8. Resolve **color scheme priority** based on project type:

   **Dark-mode-first** (dark is the primary canvas; light is the optional override):
   - Dashboard · admin panel · data-heavy SaaS · fintech · developer tools · analytics · monitoring · crypto/web3 · media/streaming · gaming

   **Light-mode-first** (light is the primary canvas; dark is the optional override):
   - E-commerce · marketing site · portfolio · healthcare · education · food & beverage · lifestyle

   If the project type is ambiguous or does not fit either list, default to **light-mode-first** and offer dark mode as an add-on.

   Carry this decision forward as `color_scheme_priority: dark_first | light_first`. Phase 2 palette options and Phase 4 token freeze must reflect this priority.

### Phase 2 — COLOR + DESIGN DIRECTION

1. Resolve color direction before style selection.
2. If the user did not provide an explicit palette, offer 2–3 palette directions that fit the product category **and reflect the `color_scheme_priority` from Phase 1**:
   - For `dark_first` projects: lead with dark palette options (e.g. OLED dark-luxury, electric slate, deep navy), include a light option only as the last choice.
   - For `light_first` projects: lead with light palette options (e.g. commerce warm-energy, trust cool-neutral), include a dark option only if it fits the brand.
   - Ask the user to choose one.
3. If the user declines to choose, auto-select the best-fit palette and say why in one sentence.
4. Load `references/design-styles-catalog.md`.
5. From the catalog, select **2–3 styles** that best match the project type, chosen palette, and context.
6. For each selected style, generate an **option card** in this format:

   ```
   [N]. **Style Name** — RECOMMENDED (if applicable)
   Vibe: [one sentence vibe/mood]
   Key aesthetic: [3 defining visual characteristics]
   ```

7. Mark exactly ONE option as **RECOMMENDED** based on best fit.
8. Present the numbered list to the user and ask them to choose. Wait for their response before proceeding.
9. If the user asks for a different style not in the list, accommodate it and proceed.

### Phase 3 — BUNDLE GENERATION

1. Load `references/platform-rules.md` for the selected platforms.
2. Load `references/output-template.md` for the CJX bundle format.
3. Load `references/output-bundle-rules.md` for asset ownership, shared-class placement, manifest, and bundle self-audit.
4. Load `references/radius-choreography.md` to resolve radius grammar, nested surface hierarchy, and role-based curvature before writing any CSS.
5. Load `references/ux-guidelines.md` when generating final output because state completeness is mandatory.
6. Apply ALL Anti-AI Design Rules below.
7. Apply the platform rules for each selected platform separately.
8. Resolve a **radius grammar** for the chosen style direction before writing component CSS:
   - choose 2–4 primary radius tiers plus pill if needed,
   - map them to semantic roles: shell, surface, inset, control, tight, pill,
   - keep the grammar consistent across the entire bundle,
   - ensure nested same-material surfaces step down in curvature.
9. Generate a **bundle directory** containing:
   - `html/`
   - `css/`
   - `js/`
   - `manifest.json`
10. Generate one HTML/CSS/JS trio per required screen/platform combination.
11. Generate only the requested screens and only the selected platforms.
12. Landing pages may remain cross-platform semantic if the same file works well, but if layout meaningfully changes by platform, generate platform-specific landing variants too.
13. Every HTML file must:
   - reference `../css/foundation.css`
   - reference `../css/shared.css`
   - reference its screen CSS file
   - reference shared `../js/app.js`
   - reference its screen JS file when needed
   - use `data-ai-id` on all major structural elements
   - use contextual, realistic copy — never lorem ipsum
14. Every generated app screen must include or explicitly handle the four UX states from `ux-guidelines.md`:
   - loading
   - empty
   - error
   - success
15. These states may be visible in the main canvas or implemented as toggleable mock states via JS controls, but they must exist in the shipped bundle.
16. Resolve the **default visible state** intentionally:
   - generator screens should default to `empty` unless the user explicitly asked for a preloaded/demo-ready success canvas,
   - result/review screens should default to `success` unless the narrative explicitly requires another state first,
   - never let a generator screen imply a completed output before the user has provided or loaded input.
17. Apply **utility-screen realism rules** to generator, result, dashboard, and form-heavy screens:
   - optimize for trust, scanability, and alignment before spectacle,
   - keep the primary form, state canvas, result board, and CTA groups in stable normal flow layouts,
   - do not use overlapping or absolute-positioned content-bearing cards as the primary structure of a utility screen,
   - keep decorative asymmetry secondary so it never weakens task clarity or CTA discoverability,
   - ensure hero typography on utility screens reads credibly at the target viewport instead of relying on theatrical wrapping.
18. Before declaring output complete, run the bundle self-audit from `references/output-bundle-rules.md`:
   - move all selectors reused across 2+ HTML files into `shared.css`
   - ensure no page depends on a sibling page CSS file to render correctly
   - ensure every referenced asset exists
   - ensure `manifest.json` exactly matches generated files
   - ensure no files exist for unselected platforms
   - ensure the radius hierarchy follows the chosen semantic grammar and nested surfaces do not flatten into equal-radius layers
   - ensure utility screens pass the layout realism audit at their target viewport

### Phase 4 — FOUNDATION TOKEN FREEZE

1. After generating the first approved screen, extract the exact token values into `css/foundation.css`.
2. Freeze not only color/type/motion, but also the **semantic radius grammar** for the bundle.
3. Use this exact format:

```css
/* FROZEN FOUNDATION TOKENS — DO NOT MODIFY */
:root {
  --color-primary: <exact value>;
  --color-secondary: <exact value>;
  --color-accent: <exact value>;
  --color-bg: <exact value>;
  --color-surface: <exact value>;
  --color-text: <exact value>;
  --color-text-muted: <exact value>;
  --font-heading: <exact font stack>;
  --font-body: <exact font stack>;
  --space-base: <exact value>;
  --radius-1: <exact value>;
  --radius-2: <exact value>;
  --radius-3: <exact value>;
  --radius-4: <exact value>;
  --radius-5: <exact value>;
  --radius-shell: <exact value>;
  --radius-surface: <exact value>;
  --radius-inset: <exact value>;
  --radius-control: <exact value>;
  --radius-tight: <exact value>;
  --radius-pill: 9999px;
  --ease-spring: <exact value>;
}
```

4. State explicitly: `Foundation tokens frozen. All subsequent screens will use these exact values.`
   - If `color_scheme_priority` is `dark_first`: state `Foundation tokens frozen (dark primary + light override).`
   - If `color_scheme_priority` is `light_first` and dark mode was generated: state `Foundation tokens frozen (light primary + dark override).`
5. All subsequent screens must consume these exact values from `foundation.css`.

### Phase 5 — RECOVERY

When the user says "change the [color / layout / typography / motion / spacing / platform set]":

1. Identify the **single aspect** they want changed.
2. Regenerate **only that aspect** — do not alter other design decisions.
3. If changing platforms:
   - add only newly requested platform files,
   - remove omitted platform files from the proposed output,
   - do not regenerate unaffected platform files unless necessary.
4. If changing a frozen token: update `foundation.css` and note which token changed.
5. If changing layout: update only the affected platform screen files.
6. If changing color direction: preserve IA and structure where possible, update tokens and affected surfaces only.
7. Do NOT restart from Phase 1 unless the user explicitly asks to start over.
8. **Cross-screen consistency check** — after any partial regeneration, verify the full bundle before declaring complete:
   - all screens still reference the same `foundation.css` token values (no radius, color, or spacing drift),
   - icon family and weight are consistent across all regenerated and untouched screens,
   - `shared.css` primitives used by the changed screen are still intact and not accidentally narrowed,
   - `manifest.json` reflects the current file set (no stale entries, no missing files),
   - if a token changed, confirm every screen that consumes that token renders correctly at its target viewport.

---

## Anti-AI Design Rules (MANDATORY)

These rules apply to **every screen, every generation, without exception**. Violation of any BANNED PATTERN requires immediate regeneration.

### BANNED PATTERNS (Violation = Reject & Regenerate)

- NO Inter, Roboto, Arial, Helvetica as display/heading fonts
- NO generic gradient blob backgrounds. DO use tasteful, subtle aurora/mesh gradients (e.g., Apple-style) anchored to corners or specific cards for a premium glowing effect.
- NO tech-blue (#0070f3, #2563eb) as primary without explicit user request
- NO symmetric 3-column feature grid (icon + title + description × 3)
- NO Undraw/Blush-style generic illustrations
- NO glassmorphism-on-gradient ONLY IF it looks cheap. DO use backdrop-blur-xl with very subtle border colors (e.g. border-white/20) for a premium glass effect.
- NO centered "Welcome to [Product]" hero with subtitle + single CTA; make it visually dynamic.
- NO `transition: all` — list properties explicitly
- NO box-shadow with blur > 20px (unless the active trend explicitly allows it)
- NO placeholder images from via.placeholder.com or picsum
- NO generic "lorem ipsum" placeholder text — use contextual, realistic copy
- NO perfectly symmetrical or overly balanced brutalist layouts; embrace intentional asymmetry
- NO default 16px font size everywhere; strictly enforce a modular typographic scale
- NO standard box-shadows; use tailored, multi-layered smooth shadows, or "stacked card" effects via pseudo-elements (e.g., layered borders and tinted shadows beneath primary cards)
- NO standard border-radius; use continuous squircle curves or fully rounded pills depending on the active trend
- NO emoji icons for UI elements; use the designated icon library from the Design Recipe (e.g. Heroicons, Phosphor, Tabler, Lucide, or Material Symbols)
- NO emoji brand marks, emoji mascots, emoji logos, or emoji-like pictograms masquerading as product identity
- NO brand lockups that rely on emoji glyphs, Unicode symbols, or platform-rendered pictographs for the app mark
- NO mixing icon families — pick ONE icon library per project and use it exclusively
- NO generic icons when specific alternatives exist (e.g. use "key" for API keys, not "settings" cog)
- NO absolute-positioned or overlapping content cards as the primary structure for generator, result, form, or dashboard screens
- NO decorative asymmetry that weakens CTA alignment, form scanability, or state readability on utility screens
- NO utility-screen hero typography that depends on ultra-tight line-height, extreme wrapping, or narrow text columns to feel dramatic
- NO concept-shot compositions that look like poster art instead of a credible working product screen
- NO surprise element that competes with the primary form, result payload, or state canvas

### REQUIRED QUALITY SIGNALS

- Headings MUST use the trend's display font, NEVER the body font
- Color palette MUST have >=3 distinct hues (no monochrome gray)
- Icons MUST be optically aligned with text baselines (`vertical-align: -0.125em` for inline)
- Brand marks and app logos MUST be vector-drawn or explicitly designed symbols, never emoji glyphs or platform-rendered pictographs
- All icons in a view MUST use the same weight/stroke-width
- Icon sizes MUST follow the scale: 18px inline · 24px default · 32px feature · 48px hero
- For dashboard panels, incorporate subtle gradients on surface backgrounds (e.g. from transparent to 3% foreground) with low-opacity borders to create premium volumetric depth
- Every major container/card MUST have premium effects: layered stacked cards, inner borders `border border-white/10`, or complex shadows `shadow-[0_8px_30px_rgba(0,0,0,0.04)]`
- Landing pages and marketing pages MUST have >=1 "surprise" element — choose from: Bento grid, masonry layout, parallax tilt, spotlight border, dock magnification, gooey menu, liquid swipe, stacked cards, or text mask reveal
- Utility screens MAY use a surprise element only when it stays secondary to the working layout and does not rely on overlap hacks or CTA displacement
- Buttons MUST have distinct hover/active/focus states (not just opacity change) with spring easing (`cubic-bezier(0.25, 1, 0.5, 1)`) and glow effects
- Spacing follows mathematical rhythm (4px or 8px base), never arbitrary; use staggered motion delays for sequential elements
- All images use descriptive alt text, never empty `alt=""`
- Utility screens MUST maintain stable reading rails for form fields, state panels, result payloads, and validation messages
- Utility screens MUST look credible at their target viewport, with no clipped content, crushed headings, or detached proof panels
- Design MUST exhibit high visual quality and clear hierarchy; trust-critical screens should prefer credible product realism over maximal visual density

---

## Responsive Rules

Apply on every screen regardless of target platform:

- **Ban `h-screen`** — use `min-h-[100dvh]` to avoid iOS Safari viewport bugs
- **Ban flex percentage math** — use CSS Grid for layout; flexbox only for alignment within grid cells
- **Mobile fallback** — every multi-column grid must collapse to single-column at <640px
- **No hover-dependent interactions on mobile** — all critical actions must be tap-accessible
- **Semantic HTML first** — use `<button>`, `<nav>`, `<main>`, `<section>` before adding ARIA attributes
- **Touch targets** — minimum 44px × 44px for all interactive elements on mobile
- **Fluid scaling** — prefer `clamp()` and fluid type scales over rigid breakpoint jumps

## Utility Screen Composition Rules

Apply these rules to generator, result, dashboard, settings, and other form-heavy operational screens:

- Trust, scanability, and alignment come before spectacle.
- Keep forms, state canvases, result boards, and primary CTA groups in stable normal-flow layouts.
- Do not use overlapping or absolute-positioned content-bearing cards as the primary structure of a utility screen.
- Decorative asymmetry may exist only in clearly secondary zones and must never displace the working layout.
- Hero typography on utility screens must read credibly at the target viewport; do not rely on crushed line-lengths or theatrical wrapping.
- Surprise elements on utility screens must be subordinate to the task flow and must not compete with the primary action.
- If a layout would look more like a concept poster than a daily-use product screen, regenerate it.

## Selective Loading Rule

**IMPORTANT:** This skill's `references/` directory contains multiple large files. Load ONLY the file required for the current phase:

- Phase 2 (color/style selection): load `references/design-styles-catalog.md` only
- Phase 3 (generation): load `references/platform-rules.md` + `references/output-template.md` + `references/output-bundle-rules.md`
- If state completeness or CJX implementation is needed: load `references/ux-guidelines.md`
- If user requests a specific recipe: load `references/design-recipes-catalog.md` only

**Never load all references at once.** Loading all files simultaneously will exhaust the context window and degrade output quality. One file at a time, only when needed.
