# Output Bundle Template

Canonical CJX-ready output bundle template. Generated screens must follow this structure exactly unless the user explicitly asks for a single-file export.

---

## Default Bundle Structure

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
  manifest.json
```

### Required files

- `css/foundation.css`
- `css/shared.css`
- `js/app.js`
- `manifest.json`

## Naming Rules

- Landing page keeps semantic naming: `landing-page.*`
- App screens must use platform prefixes:
  - `mobile-<screen>.*`
  - `tablet-<screen>.*`
  - `desktop-<screen>.*`
- Generate files only for the platforms selected by the user.
- If the user selected `mobile` and `desktop`, the bundle MUST NOT contain `tablet-*` files.

---

## foundation.css Template

```css
/* FROZEN FOUNDATION TOKENS — DO NOT MODIFY */
:root {
  --color-primary: /* value */;
  --color-secondary: /* value */;
  --color-accent: /* value */;
  --color-bg: /* value */;
  --color-surface: /* value */;
  --color-text: /* value */;
  --color-text-muted: /* value */;
  --font-heading: /* value */;
  --font-body: /* value */;
  --space-base: /* value */;

  --radius-1: /* value */;
  --radius-2: /* value */;
  --radius-3: /* value */;
  --radius-4: /* value */;
  --radius-5: /* value */;
  --radius-shell: /* value */;
  --radius-surface: /* value */;
  --radius-inset: /* value */;
  --radius-control: /* value */;
  --radius-tight: /* value */;
  --radius-pill: 9999px;

  --ease-spring: /* value */;
}
```

Rules:
- `foundation.css` contains tokens only.
- No component styles in `foundation.css`.
- Freeze a **semantic radius grammar** and reuse it verbatim.
- Map major surfaces to `shell`, `surface`, `inset`, `control`, and `tight` roles instead of scattering arbitrary radius values.
- These tokens are frozen after the first approved screen and reused verbatim.

---

## shared.css Template

```css
*, *::before, *::after { box-sizing: border-box; }

html, body {
  margin: 0;
  min-height: 100%;
  font-family: var(--font-body);
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

body {
  min-height: 100dvh;
}

img {
  max-width: 100%;
  display: block;
}

button,
a,
input,
select,
textarea {
  font: inherit;
}

button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 3px;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Rules:
- `shared.css` holds reusable resets, focus styles, motion defaults, and shared primitives.
- Put shared glass recipes, button state recipes, shared shells, utility classes, and any selector reused across 2+ HTML files here.
- Shared nav, brand, sidebar, header-row, and repeated platform-family primitives MUST live here, never only in one screen CSS file.
- Shared radius application helpers and repeated role-based curvature patterns should also live here when reused across multiple pages.
- Nested same-material surfaces must not flatten into equal-radius layers; apply the semantic radius grammar consistently.

---

## manifest.json Template

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
  "html": [
    "landing-page.html",
    "mobile-link-generator.html",
    "mobile-result.html",
    "desktop-link-generator.html",
    "desktop-result.html"
  ],
  "css": [
    "foundation.css",
    "shared.css",
    "landing-page.css",
    "mobile-link-generator.css",
    "mobile-result.css",
    "desktop-link-generator.css",
    "desktop-result.css"
  ],
  "js": [
    "app.js",
    "landing-page.js",
    "mobile-link-generator.js",
    "mobile-result.js",
    "desktop-link-generator.js",
    "desktop-result.js"
  ],
  "sharedCss": ["foundation.css", "shared.css"],
  "sharedJs": ["app.js"]
}
```

Rules:
- `manifest.json` is required for every bundle output.
- It must exactly match the generated file set.
- It must not list files for unselected platforms.

---

## HTML Document Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <title>{Page Title}</title>
  <link rel="stylesheet" href="../css/foundation.css" />
  <link rel="stylesheet" href="../css/shared.css" />
  <link rel="stylesheet" href="../css/{screen-file}.css" />
</head>
<body>
  <main data-ai-id="page-root">
    <!-- Page content -->
  </main>

  <script src="../js/app.js"></script>
  <script src="../js/{screen-file}.js"></script>
</body>
</html>
```

### Required Elements
- `<!DOCTYPE html>` — strict mode
- `viewport-fit=cover` — iOS safe area handling
- `<main data-ai-id="...">` — page root with AI targetable ID
- All major structural elements must have `data-ai-id` attributes
- HTML must reference `foundation.css`, `shared.css`, shared `app.js`, and its own screen file assets

### Forbidden Output Patterns
- One loose standalone HTML as the default output
- Hardcoded hex/rgb values that duplicate CSS variables when a token exists
- Non-semantic container divs (`<div class="wrapper">` without purpose)
- Inline event handlers (use `addEventListener` in JS files instead)
- Empty `alt=""` on informational images
- `h-screen` (use `min-h-[100dvh]` instead)
- Missing JS/CSS file references for interactive screens

---

## JS Contract

### app.js
Shared behavior only. Examples:
- nav active-state helpers
- reusable modal open/close helpers
- mock state toggles for loading/empty/error/success
- focus management helpers
- accessibility-safe interaction utilities

### screen-specific JS
Only when needed:
- state toggles for a specific screen
- input validation for a specific form
- mock data rendering for a specific UI flow
- chart animation or screen-local interactions

Do not put everything into inline `<script>` tags unless the user explicitly asked for single-file export.

---

## State Completeness Requirement

Every app screen in the bundle MUST explicitly handle these four states:

- **Loading** — skeletons, shimmer, reserved layout space
- **Empty** — contextual empty state with CTA
- **Error** — friendly error message + retry path
- **Success** — confirmation cue or next-step state

Implementation options:
1. visible sections in the HTML, toggled by JS classes
2. mock-state switcher in JS for review/demo
3. embedded segmented control for previewing states during handoff

A screen is incomplete if these states do not exist in the shipped output.

---

## Responsive Behavior

- Mobile-first base styles still apply even in platform-specific files
- Use CSS Grid for layout, Flexbox only for alignment within grid cells
- Desktop/tablet/mobile platform files should be materially optimized for their target platform — not just trivially resized clones
- Use `clamp()` for fluid typography where appropriate
- Landing pages may still include responsive behavior, but app screens should respect their platform-specific IA and navigation archetype

---

## Single-File Export Exception

If the user explicitly asks for a single self-contained export, you may additionally provide:

```html
<!-- self-contained export -->
<style>/* foundation + shared + screen CSS */</style>
<script>/* app.js + screen JS */</script>
```

But this is an exception. The default contract remains the CJX-ready bundle with `html/`, `css/`, and `js/` folders.

---

## React Component Output Mode

When `implementation_target` is `shadcn_ui`, `tailwind_css`, or `custom_app` and the user explicitly requests React/TSX output, generate a component bundle instead of the HTML/CSS/JS bundle.

### React Bundle Structure

```text
<app-slug>-design/
  src/
    components/
      shared/
        Nav.tsx
        BrandLockup.tsx
        StateShell.tsx        # loading / empty / error / success wrapper
      <Screen>Page.tsx        # one file per screen
    styles/
      foundation.css          # frozen tokens (CSS custom properties only)
      shared.css              # resets, focus styles, motion defaults
      <Screen>Page.module.css # screen-local styles
    tokens.ts                 # typed re-export of foundation token names
  manifest.json
```

### Component Template

```tsx
// <Screen>Page.tsx
import React, { useState } from 'react';
import styles from '../styles/<Screen>Page.module.css';

interface <Screen>PageProps {
  initialState?: 'loading' | 'empty' | 'error' | 'success';
}

export function <Screen>Page({ initialState = 'empty' }: <Screen>PageProps) {
  const [uiState, setUiState] = useState(initialState);

  if (uiState === 'loading') return <LoadingState />;
  if (uiState === 'empty')   return <EmptyState onAction={() => setUiState('success')} />;
  if (uiState === 'error')   return <ErrorState onRetry={() => setUiState('loading')} />;

  return (
    <main data-ai-id="page-root" className={styles.root}>
      {/* success / default content */}
    </main>
  );
}
```

### tokens.ts Template

```ts
// tokens.ts — typed aliases for CSS custom property names
export const tokens = {
  colorPrimary:   'var(--color-primary)',
  colorBg:        'var(--color-bg)',
  colorSurface:   'var(--color-surface)',
  colorText:      'var(--color-text)',
  colorTextMuted: 'var(--color-text-muted)',
  fontHeading:    'var(--font-heading)',
  fontBody:       'var(--font-body)',
  radiusShell:    'var(--radius-shell)',
  radiusSurface:  'var(--radius-surface)',
  radiusControl:  'var(--radius-control)',
  easingSpring:   'var(--ease-spring)',
} as const;
```

### React Component Rules
- Every screen is a named export, not a default export.
- Props interface is always explicit — no implicit `any`.
- Foundation tokens are consumed via `tokens.ts` or CSS custom properties; never hardcode hex/px design values inline.
- Shared nav, brand lockup, and state shells go in `components/shared/` — never duplicated per screen.
- Screen-local CSS goes in a CSS Module (`<Screen>Page.module.css`); shared primitives go in `shared.css`.
- State completeness (loading / empty / error / success) is expressed as distinct render branches, not CSS class toggles.
- Dark mode: use `data-theme` attribute on `<html>`; Tailwind projects use `darkMode: 'class'` in config.

---

## Accessibility Checklist

Before finalizing any output, verify:
- [ ] All `<button>` elements are `<button>`, not `<div>`
- [ ] All `<nav>` uses semantic `<nav>` tag
- [ ] Focus-visible styles exist on all interactive elements
- [ ] Color contrast ≥4.5:1 for text, ≥3:1 for UI components
- [ ] Touch targets ≥44×44px on mobile/tablet
- [ ] All interactive elements keyboard-operable (Tab, Enter, Space, Escape)
- [ ] No `outline: none` without `:focus-visible` replacement
- [ ] State completeness exists for loading, empty, error, success
