# Output Bundle Rules

Strict rules for how generated output bundles must be structured, shared, validated, and self-audited.

Use this reference whenever the skill is generating a multi-file bundle (`html/`, `css/`, `js/`).

---

## Goal

Prevent broken multi-file output caused by:

- shared classes defined in only one screen CSS file
- HTML files referencing assets that do not exist
- navigation/brand/layout primitives disappearing on sibling screens
- inconsistent platform file naming
- result screens loading in the wrong default state
- bundle outputs that work on one page but break when navigating to another

---

## Required Bundle Shape

```text
<app-slug>-design/
  html/
  css/
  js/
  manifest.json
```

### Required files

- `css/foundation.css`
- `css/shared.css`
- `js/app.js`
- `manifest.json`

### manifest.json contract

```json
{
  "app": "<app-slug>",
  "platforms": ["mobile", "desktop"],
  "screens": [
    "landing-page",
    "mobile-link-generator",
    "mobile-result",
    "desktop-link-generator",
    "desktop-result"
  ],
  "html": [],
  "css": [],
  "js": [],
  "sharedCss": ["foundation.css", "shared.css"],
  "sharedJs": ["app.js"]
}
```

The manifest does not need runtime behavior. It exists to make the output auditable.

---

## Asset Ownership Rules

### foundation.css owns only tokens

Allowed:
- CSS custom properties only

Forbidden:
- component selectors
- page layout selectors
- nav/button/card selectors

### shared.css owns all cross-screen primitives

If a class appears in **2 or more HTML files**, it MUST live in `shared.css`.

Typical examples:
- brand lockups
- nav item primitives
- sidebar/topbar shells
- shared glass card recipes
- button primitives
- form primitives
- state switchers
- skeleton primitives
- trust-list/detail-list primitives
- platform-wide shells reused across multiple pages

Examples that belong in `shared.css`:
- `.brand-lockup`
- `.brand-mark`
- `.brand-name`
- `.brand-subtitle`
- `.desktop-nav-stack`
- `.desktop-nav-link`
- `.desktop-side-panel`
- `.mobile-topline`

### screen CSS owns only screen-local classes

A screen CSS file may contain:
- layout specific to one HTML page
- one-off compositions
- unique hero treatments
- page-specific bento spans or local wrappers

A screen CSS file must NOT be the only owner of a class reused by sibling screens.

---

## HTML Linking Contract

Every HTML file must link assets in this order:

```html
<link rel="stylesheet" href="../css/foundation.css" />
<link rel="stylesheet" href="../css/shared.css" />
<link rel="stylesheet" href="../css/<screen>.css" />
...
<script src="../js/app.js"></script>
<script src="../js/<screen>.js"></script>
```

Rules:
- shared assets always before screen assets
- no missing screen asset references
- no references to tablet files when tablet was not selected
- no hidden dependency on another screen's CSS file

---

## Navigation Consistency Rules

If multiple screens belong to the same platform family, navigation primitives must be shared.

### Desktop family
If 2+ desktop pages exist, these must live in shared.css:
- sidebar shell
- desktop nav list
- desktop nav link
- desktop shared side panel
- shared brand lockup used in desktop pages

### Mobile family
If 2+ mobile pages exist, these must live in shared.css:
- mobile top line / compact header row
- bottom tab nav
- shared mobile shell primitives when reused

---

## Default State Rules

### Generator screens
Default visible state should usually be `empty`.

Use `success` as the generator default only when the user explicitly asked for:
- a demo-ready preloaded screen
- a seeded sample workflow
- or a review artifact that must open with generated content already present

A generator screen must not accidentally imply completed output before the user has provided or loaded input.

### Result screens
Default visible state should depend on narrative intent:
- if the page is meant to showcase the finished result in review output, default to `success`
- if the page is meant to demonstrate loading skeletons first, say so explicitly in copy

Do not accidentally leave a result page in `loading` by default unless that is intentional and explained.

---

## Self-Audit Checklist (MANDATORY BEFORE FINAL OUTPUT)

Before declaring the bundle complete, the generator must verify all of the following:

### A. Shared-class audit
For each HTML file:
1. collect all classes used
2. identify classes reused across sibling HTML files
3. move those selectors into `shared.css`
4. leave only screen-local selectors in screen CSS

### B. Asset existence audit
For each HTML file:
- every local `href` exists
- every local `src` exists
- no extra platform files are referenced

### C. Cross-page navigation audit
- clicking from one sibling screen to another must not lose nav/brand/sidebar/header styling
- no page may rely on a sibling page CSS file to look correct

### D. State audit
- loading exists
- empty exists
- error exists
- success exists
- default visible state is intentionally chosen

### E. Radius hierarchy audit
- the bundle uses a clear radius grammar with semantic roles
- nested surfaces step down instead of repeating equal curvature
- controls use control-tier radius rather than shell-tier softness
- no child surface exceeds the radius of the parent that contains it

### F. Manifest audit
- manifest.json exists
- manifest lists the exact generated HTML/CSS/JS files
- selected platforms match the actual file set
- when `index.html` exists, the bundle internally treats it as either `navigation_hub` or `review_canvas`, not as a silent replacement for the landing page

### G. Layout realism audit
- utility screens read credibly at their target viewport instead of looking like concept posters
- no text clipping, crushed headings, or theatrical wrapping in primary utility-screen content
- no overlap-based composition for critical form, result, or state content
- no CTA or validation section is visually displaced by decorative cards
- no proof panel feels detached from the grid that contains it
- primary task content uses normal document flow unless overlap is strictly decorative and non-critical

### H. Product-copy audit
- real-product screens contain no audit-facing labels such as `mobile view`, `desktop view`, `default state`, `empty default`, `success default`, `review artifact`, `review board`, `inspection`, `design note`, `CJX review`, or `state canvas`
- helper text explains user-facing product behavior rather than QA/demo framing
- launcher pages may summarize bundle contents, but product screens must stay free of review-board wording
- a `navigation_hub` index may stay concise and utilitarian; it does not need to inherit the full visual density of the product screens
- a `review_canvas` index may expose comparison affordances, but only when that mode was explicitly requested

---

## Hard Failure Conditions

If any of these are true, the bundle is incomplete and must be regenerated or repaired:

- a class reused across pages exists only in one screen CSS file
- a page loses navigation styling when opening a sibling page
- a referenced asset file does not exist
- a platform file exists for an unselected platform
- result/generator screen is missing one of the 4 CJX states
- the bundle uses flat equal-radius layering that breaks the chosen radius grammar
- the primary utility-screen layout depends on overlapping or absolute-positioned content cards
- the target viewport shows clipped, crushed, or detached critical content on a utility screen
- manifest.json is missing

---

## Repair Strategy

When a bundle fails the rules above:

1. move all cross-screen selectors into `shared.css`
2. keep only page-local selectors in screen CSS files
3. add or repair `manifest.json`
4. re-check local asset references
5. re-check platform file set
6. re-check default state visibility

Never patch only the one broken page if the underlying problem is bundle ownership.
Fix the asset contract.

---

## Font Loading Rules

Every bundle that uses a non-system font must include proper font loading in **every HTML file's `<head>`**, before the CSS links.

### Google Fonts (default for html_bundle)

```html
<!-- Step 1: preconnect — must come before the stylesheet link -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<!-- Step 2: load with display=swap to prevent invisible text -->
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" />
```

Rules:
- Always include both `preconnect` links before the font stylesheet.
- Always append `&display=swap` to every Google Fonts URL.
- Load only the weights actually used — do not load all 100–900 weights by default.
- Place font `<link>` tags **before** `foundation.css` and `shared.css` so the cascade resolves correctly.

### Self-hosted fonts (sveltekit / react_component / production builds)

```css
/* shared.css — at the very top, before any selectors */
@font-face {
  font-family: 'Plus Jakarta Sans';
  src: url('../fonts/plus-jakarta-sans-variable.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
```

Rules:
- Prefer `.woff2` format; include a variable font range (`100 900`) when available.
- Always set `font-display: swap` — never `block` or `auto` in production output.
- Place `@font-face` declarations at the top of `shared.css`, never in `foundation.css` (tokens only) or screen-specific files.

### System font fallback stack

Every `--font-heading` and `--font-body` token must include a full fallback cascade:

```css
--font-heading: 'Plus Jakarta Sans', 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif;
--font-body:    'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif;
--font-mono:    'JetBrains Mono', 'Fira Code', ui-monospace, 'Cascadia Code', monospace;
```

Never declare a font token with only the custom font name and no fallbacks.

### Font loading audit (add to Self-Audit Checklist)

Before finalising the bundle:
- [ ] Every HTML file has `preconnect` links before the font stylesheet (Google Fonts)
- [ ] Every Google Fonts URL includes `&display=swap`
- [ ] `@font-face` blocks use `font-display: swap`
- [ ] Every font token has a full fallback stack
- [ ] Only weights in actual use are requested
