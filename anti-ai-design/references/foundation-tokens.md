# Foundation Tokens

Foundation tokens define the visual language for all generated screens. These tokens are frozen after the first screen (Phase 3) and injected verbatim into all subsequent screens.

---

## Core Token Set

### Color Tokens
```css
--color-primary:        /* Primary brand color */
--color-secondary:      /* Secondary color */
--color-accent:         /* Accent / CTA color */
--color-bg:            /* Page background */
--color-surface:        /* Card/panel surface */
--color-text:          /* Primary text */
--color-text-muted:    /* Secondary/muted text */
--color-border:        /* Borders and dividers */
```

### Typography Tokens
```css
--font-heading:        /* Display/heading font stack */
--font-body:           /* Body text font stack */
--font-mono:           /* Monospace (code/data) */

--size-xs:             /* 12px */
--size-sm:             /* 14px */
--size-base:           /* 16px (mobile) / 14px (desktop) */
--size-lg:             /* 18px */
--size-xl:             /* 24px */
--size-2xl:            /* 32px */
--size-3xl:            /* 48px */
--size-hero:            /* 64px+ */

--weight-normal:       /* 400 */
--weight-medium:       /* 500 */
--weight-semibold:     /* 600 */
--weight-bold:        /* 700+ */

--leading-tight:       /* 1.1-1.2 — headings */
--leading-normal:       /* 1.5 — body */
--leading-loose:       /* 1.7+ — long-form */

--tracking-tight:      /* -0.04em — headings */
--tracking-normal:      /* 0 — body */
--tracking-wide:       /* 0.05em — labels */
```

### Spacing Tokens (4px base grid)
```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-6: 24px;
--space-8: 32px;
--space-12: 48px;
--space-16: 64px;
--space-24: 96px;
```

### Radius Tokens (Semantic grammar + cascade)
```css
--radius-0: 0px;
--radius-1: 8px;
--radius-2: 10px;
--radius-3: 14px;
--radius-4: 16px;
--radius-5: 20px;
--radius-6: 24px;
--radius-7: 28px;

--radius-shell:   /* Largest structural shell */
--radius-surface: /* Major cards / panels */
--radius-inset:   /* Nested surfaces / state panels */
--radius-control: /* Buttons, inputs, nav items, interactive tiles */
--radius-tight:   /* Compact surfaces / icon plates / tiny metric wrappers */
--radius-pill: 9999px; /* Pills, avatars, selective status cues */
```

### Radius Governance
- Use **semantic radius roles**, not arbitrary per-component values.
- One project should usually use **2–4 primary radius tiers** plus pill if needed.
- Nested surfaces must step down: `shell >= surface >= inset >= control >= tight`.
- A child surface must never exceed the radius of the parent that visually contains it.
- Same-material nested surfaces should usually step down by **2–8px**.
- Buttons/inputs/chips should use `--radius-control`, not copy the panel radius blindly.
- Pill radius is selective, not the default for every interactive element.


### Motion Tokens
```css
--ease-spring:    cubic-bezier(0.16, 1, 0.3, 1)   /* iOS gesture feel */
--ease-bounce:    cubic-bezier(0.68, -0.55, 0.27, 1.55) /* Playful bounce */
--ease-smooth:    cubic-bezier(0.25, 1, 0.5, 1)   /* Hover/focus transitions */
--ease-out:       cubic-bezier(0.0, 0, 0.2, 1)    /* Exits */
--ease-in:        cubic-bezier(0.4, 0, 1, 1)      /* Entries */

--duration-fast:   150ms;    /* Micro-interactions */
--duration-normal: 300ms;    /* Standard transitions */
--duration-slow:  500ms;    /* Page transitions, reveals */
--duration-slower: 800ms;   /* Editorial reveals */

--stagger: 30ms;  /* Incremental delay for sequential elements */
```

### Shadow Tokens
```css
/* Multi-layer smooth shadows — prefer these over single-layer */
--shadow-sm:   0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md:   0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
--shadow-lg:   0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.05);
--shadow-xl:   0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05);

/* Glass surface shadow (on dark backgrounds) */
--shadow-glass: 0 8px 32px rgba(0, 0, 0, 0.24);

/* Stacked card effect */
--shadow-stacked: 0 1px 0 rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.08);
```

---

## Per-Art-Pack Token Overrides

### Glass Premium
```css
--color-bg:       #000000;    /* True OLED black */
--color-surface:  rgba(255, 255, 255, 0.05);
--color-border:   rgba(255, 255, 255, 0.08);
--shadow-glass:   inset 0 1px 0 rgba(255, 255, 255, 0.15);
```

### Warm Editorial
```css
--color-bg:       #F9F6F0;   /* Warm cream */
--color-surface:  #FFFFFF;
--color-border:   rgba(26, 26, 26, 0.12);
--shadow-glass:   none;       /* Flat paper aesthetic */
```

### Vibrant Organic Bloom
```css
--color-bg:       #FFF5F0;   /* Warm blush white */
--color-surface:  rgba(255, 255, 255, 0.9);
--color-border:   rgba(0, 0, 0, 0.08);
--radius-pill:    9999px;   /* Maximum rounded */
--ease-spring:   cubic-bezier(0.68, -0.55, 0.27, 1.55); /* Bouncy */
```

---

## Token Freeze Protocol

### When to Freeze
After generating the first screen (after Phase 3), freeze all tokens before generating Screen 2.

### How to Extract Tokens
1. Scan the generated screen's `:root {}` block
2. Extract the exact values for all core tokens
3. Output the frozen token block as markdown
4. Inject the block verbatim at the top of all subsequent screens

### Recovery Token Update
When the user requests a specific change:
1. Identify which token(s) to update
2. Change ONLY the requested token(s)
3. Re-output the complete frozen block with changed tokens marked
4. All other tokens remain frozen

### Validation Rules
- `--color-text` + `--color-bg` must pass WCAG AA (≥4.5:1 contrast)
- `--color-text-muted` must pass WCAG AA on `--color-surface`
- `--size-base` minimum 16px on mobile, 14px on desktop
- `--radius-lg` ≥ `--radius-md` ≥ `--radius-sm` (cascade direction)
- `--duration-normal` must be between 150ms and 500ms

---

## Dark Mode Token System

### When to apply
Always generate both light and dark token sets when the project type supports both schemes. The `color_scheme_priority` resolved in Phase 1 determines which scheme goes in `:root` and which is the override.

**Dark-mode-first projects** (dashboard, fintech, developer tools, analytics, data-heavy SaaS, crypto/web3, media, gaming):
- Dark values go directly in `:root` — dark is the default experience.
- Light values go in `[data-theme="light"]` and `@media (prefers-color-scheme: light)` as overrides.

**Light-mode-first projects** (e-commerce, marketing, portfolio, healthcare, education):
- Light values go directly in `:root` — light is the default experience.
- Dark values go in `[data-theme="dark"]` and `@media (prefers-color-scheme: dark)` as overrides.

### Declaration pattern — dark-mode-first

```css
/* foundation.css */

:root {
  /* dark is the primary scheme */
  --color-bg:           /* dark page background, e.g. #0a0a0f */;
  --color-surface:      /* dark card/panel surface, e.g. #13131a */;
  --color-text:         /* light text on dark, e.g. #f0f0f5 */;
  --color-text-muted:   /* muted text, e.g. rgba(240,240,245,0.5) */;
  --color-border:       /* subtle border, e.g. rgba(255,255,255,0.08) */;
  --color-primary:      /* brand primary */;
  --color-accent:       /* accent / CTA */;
  /* ... all other tokens ... */
}

/* Light override — applied when user explicitly switches or OS is light */
[data-theme="light"],
@media (prefers-color-scheme: light) {
  :root {
    --color-bg:           /* light page background */;
    --color-surface:      /* light card surface */;
    --color-text:         /* dark text on light */;
    --color-text-muted:   /* muted on light */;
    --color-border:       /* light border */;
    /* primary/accent usually unchanged unless contrast fails on light */
  }
}
```

### Declaration pattern — light-mode-first

```css
/* foundation.css */

:root {
  /* light is the primary scheme */
  --color-bg:           /* light page background */;
  --color-surface:      /* light card surface */;
  --color-text:         /* dark text on light */;
  --color-text-muted:   /* muted on light */;
  --color-border:       /* subtle border */;
  --color-primary:      /* brand primary */;
  --color-accent:       /* accent / CTA */;
}

/* Dark override */
[data-theme="dark"],
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg:           /* dark page background */;
    --color-surface:      /* dark card surface */;
    --color-text:         /* light text on dark */;
    --color-text-muted:   /* muted on dark */;
    --color-border:       /* dark border */;
  }
}
```

### Theme toggle pattern (shared.css / app.js)

```js
// app.js — theme toggle helper
function toggleTheme() {
  const root = document.documentElement;
  const current = root.getAttribute('data-theme');
  root.setAttribute('data-theme', current === 'dark' ? 'light' : 'dark');
  localStorage.setItem('theme', root.getAttribute('data-theme'));
}

// On load: restore saved preference or respect OS setting
(function () {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme', saved || (prefersDark ? 'dark' : 'light'));
})();
```

### Dark mode governance rules
- Never simply invert light-mode colors — dark surfaces need proper elevation layering (`bg` < `surface` < `inset` in luminance).
- Dark text on dark backgrounds must still pass WCAG AA (≥4.5:1).
- `--color-primary` and `--color-accent` may need adjusted lightness in dark mode to avoid over-saturation on dark surfaces.
- Glass Premium art pack is inherently dark-first — define only a light-mode override if explicitly requested, not by default.
- Freeze both the light and dark token sets when dark mode is enabled: state `Foundation tokens frozen (light + dark).`
