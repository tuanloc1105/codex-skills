# Platform Rules

Platform-aware layout contracts extracted from `pipeline/prompts/platform-rules.ts` and art-pack
`platformAdaptations` data. These rules are injected by the auto-orchestration flow during
`GEN_LAYOUT`, `GEN_WIREFRAME`, `GEN_STATES`, and `GEN_VARIANTS` phases.

---

## Mobile Platform Contract (max-w 390px)

**Viewport:** max-width 390px, mobile-first single column.

### Navigation
- Navigation model: fixed **bottom tab bar** with text labels (max 5 tabs)
- Bottom tab bar is the canonical mobile archetype across all art packs
- Glass-premium variant: glass-morphic bottom tab with `backdrop-blur`
- Forbidden: sidebars, horizontal nav bars, persistent top nav patterns

### Layout & Content Density
- Single-column layout; no multi-column grids (> 2 cols)
- Comfortable density — min 16px body text, generous vertical padding
- `<div class="max-w-[390px] mx-auto min-h-screen pb-16">` as wrapper
- Allowed modules: `hero`, `article-card`, `pull-quote`, `cta-banner`
- Forbidden modules: `sidebar`, `data-table`, `multi-column-grid`, `persistent-sidebar`

### Touch & Thumb Zone
- Minimum touch target: **44×44px** with 8px gap between tappable elements
- Critical actions must sit in **bottom 60%** of screen (thumb zone)
- Forbidden: hover-only interactions (no hover states as primary UX)

### CTA Placement
- Primary CTA: sticky bottom bar or inline at section end
- Filter/sort: collapsed behind filter button; slide-up panel on tap

### Patterns
- Modals: bottom sheets (full-width), swipe-to-dismiss
- Pull-to-refresh for list views
- Sticky bottom CTA or floating action button (glass-premium: FAB)

---

## iOS 26 Liquid Glass (Mobile iOS target)

When the target platform is **mobile iOS** and the art pack or style calls for premium/glass
treatment, apply Apple's Liquid Glass design language:

- **Backdrop-blur materials:** `backdrop-filter: blur(20px)` on panels and navigation
- **Translucent tab bars:** bottom tab with `bg-white/[0.08]` + `backdrop-blur-xl`
- **Bottom sheet patterns:** glass-surface bottom sheet for modals and drawers
- **Continuous corner radius (squircle):** use Apple-style `border-radius` cascade
  (8 → 12 → 16 → 24px) — outermost containers get the largest radius
- **Specular highlights:** `inset 0 1px rgba(255,255,255,0.15)` on glass surfaces
- **Surface recipe:** `backdrop-filter:blur(20px) + bg:rgba(255,255,255,0.05) + border:rgba(255,255,255,0.08)`
- **Dynamic Island awareness:** reserve top ~60px clearance; avoid full-bleed content in notch area
- **Motion:** scale(0.97)→scale(1) + opacity on panel appear; cubic-bezier(0.16,1,0.3,1) easing

> Note: Liquid Glass is for iOS-targeted builds with glass-premium or similar art pack.
> Do NOT apply to editorial, brutalist, minimal, or warm-earth design styles.

---

## Tablet Platform Contract (max-w 768px)

**Viewport:** max-width 768px. Split-view layout preferred.

### Navigation
- Navigation model: **collapsible sidebar** table-of-contents (w-64 expanded, w-16 collapsed)
- Toggle via hamburger button; slide-in drawer from left
- Glass-premium variant: adaptive sidebar (w-64, collapses to icon rail)
- Tablet is a hybrid input environment — provide tap alternative for all hover states

### Layout & Content Density
- Moderate density — 2-column asymmetric grid (60/40 or 50/50 split)
- Master-detail split: sidebar 280px + content flex-1 OR 2-col grid
- `<div class="max-w-[768px] mx-auto min-h-screen">` as wrapper
- Allowed modules: `hero`, `article-card`, `pull-quote`, `aside-annotation`, `cta-banner`
- Forbidden modules: `data-table`, `command-palette`, `editorial-masthead` (glass-premium)

### CTA Placement
- Inline with content, repeated at section boundaries
- Right sidebar sticky OR inline after lead paragraph

### Patterns
- Collapsible panels, tabbed content areas
- Detail/preview panel to right of list views
- Filter bar visible above content, collapsible on scroll
- Supporting panels: right drawer (glass surface on glass-premium)

---

## Desktop Platform Contract (max-w 1280px)

**Viewport:** max-width 1280px. Multi-column information-dense layout.

### Navigation
- Navigation model: persistent top nav bar (64px) + optional persistent sidebar (w-60)
- Horizontal editorial nav with category dropdowns (warm-editorial art pack)
- Persistent sidebar (w-64) + horizontal top bar (glass-premium art pack)
- Hover states are **REQUIRED** on all interactive elements

### Layout & Content Density
- Dense — 3–4 column grids, data tables, compact spacing
- 12-column grid (Ant Design baseline); bento-box or dashboard layout for data screens
- Editorial variant: 3-col grid 50/25/25
- `<div class="max-w-[1280px] mx-auto min-h-screen">` as wrapper
- Allowed modules: `masthead`, `hero`, `article-card`, `featured-grid`, `cta-banner`, `data-table`, `glass-panel`, `detail-pane`
- Forbidden modules: `bottom-tab-bar`, `pull-to-refresh`, `full-screen-modal`

### CTA Placement
- Top-right of sections, inline in toolbars
- Keyboard shortcut hints for power users
- CTA: above-fold in hero, repeated at article end (editorial)

### Patterns
- Breadcrumbs for deep hierarchies
- Inline editing where applicable
- Tooltips on hover, context menus on right-click
- Keyboard: focus-visible rings, tab navigation, Escape-to-close
- Supporting panels: side panels (w-320), modals (max-w-lg centered), slide-over drawers
- Filter/sort: visible filter row + sort dropdowns; sortable column headers in data tables

---

## Navigation Archetypes by Platform

| Platform | Warm-Editorial Pack | Glass-Premium Pack | Default |
|----------|--------------------|--------------------|---------|
| **Mobile** | Bottom tab bar with text labels | Bottom tab (glass-morphic, backdrop-blur) | Fixed bottom tab bar |
| **Tablet** | Sidebar TOC (w-56, collapsible) | Adaptive sidebar (w-64, collapses to icons) | Collapsible sidebar |
| **Desktop** | Horizontal editorial nav with dropdowns | Persistent sidebar + horizontal top bar | Persistent top nav + sidebar |

---

## Responsive Fundamentals

These rules apply to all platforms regardless of art pack.

### Scaling Philosophy
- **Fluid over rigid:** prioritize liquid/fluid scaling over rigid breakpoints
- CSS Grid over flex percentage math for multi-column layouts
- `min-h-[100dvh]` instead of `h-screen` (accounts for mobile browser chrome)
- Mobile-first progressive enhancement: base styles for mobile, enhance for larger viewports

### Typography
- Use modular type scales (Major Third or Golden Ratio) for rhythmic font sizing
- Dynamic line-heights: tighter on headings (1.1–1.2), looser on body (1.5–1.7)
- Minimum 16px body text on mobile; 14px minimum on tablet; never smaller

### Spatial Rhythm
- 4px/8px grid for spacing increments
- Intentional whitespace — do not fill every pixel
- OKLCH color spaces for perceptually uniform gradients

### Motion
- `transition: all` is forbidden — list properties explicitly
- Spring easing for hover: `cubic-bezier(0.25, 1, 0.5, 1)`
- Staggered motion for sequential lists/grids (30ms delay increments)
- Respect `prefers-reduced-motion` — all animations must degrade gracefully

---

## Accessibility Floor (All Platforms)

These are non-negotiable minimums regardless of design style or platform:

- **Contrast:** text ≥ 4.5:1 (WCAG AA), UI components ≥ 3:1
- **Touch targets:** ≥ 44×44px with ≥ 8px gap (mobile/tablet)
- **Focus rings:** visible `:focus-visible` on all interactive elements — never `outline: none` without replacement
- **Semantic HTML first:** use `<button>` not `<div role="button">`, `<nav>` not `<div class="nav">` — ARIA supplements, doesn't replace semantics
- **Keyboard operable:** all interactive states accessible via Tab, Enter, Space, Escape
- **All states handled:** default, hover, active, focus, disabled — no state can be visually invisible
- **Alt text:** all informational images require descriptive alt text; decorative images use `alt=""`
- **Color alone:** never use color as the only way to convey information (use icon + color, pattern + color)
