# UX Guidelines & Customer Journey Patterns

UX enforcement and customer journey (CJX) patterns for every generated screen. These rules ensure professional, accessible, platform-native user experience.

---

## Cross-Platform UX Rules (Priority Order)

| Priority | Rule | Why |
|---|---|---|
| 1 | Accessibility — all interactive elements keyboard/touch accessible | Legal + inclusive |
| 2 | Touch targets ≥44×44px on mobile/tablet | Usability |
| 3 | Performance — no layout shift, reserved space for async content | Trust |
| 4 | Layout — responsive at 375px / 768px / 1024px / 1440px | Multi-device |
| 5 | Typography — readable line-length (65-75 chars), min 16px body on mobile | Readability |
| 6 | Animation — micro-interactions 150-300ms, respect prefers-reduced-motion | Delight |
| 7 | Style consistency — same style across all pages | Polish |

---

## State Completeness Rule

**Every screen MUST handle all four states:**

| State | Requirement |
|-------|-------------|
| **Loading** | Skeleton loaders matching final layout shape — never blank space |
| **Empty** | Compelling empty state with illustration + CTA — never raw "No data" |
| **Error** | Friendly error message + retry option — never raw error codes |
| **Success** | Confirmation feedback, state transition, or next-step cue |

### Loading State
```html
<div class="skeleton-card" aria-busy="true" aria-label="Loading content">
  <div class="skeleton-line w-3/4 h-4 bg-gray-200 rounded animate-pulse"></div>
  <div class="skeleton-line w-full h-4 bg-gray-200 rounded animate-pulse mt-2"></div>
</div>
```
Never show blank space. Skeleton must match final layout dimensions.

### Empty State
```html
<div class="empty-state" role="status">
  <svg aria-hidden="true" class="w-16 h-16 text-gray-300">...</svg>
  <h3>No items yet</h3>
  <p>Start by adding your first item.</p>
  <button class="cta-primary">Add First Item</button>
</div>
```
Never "No data" — provide context and a path forward.

### Error State
```html
<div class="error-state" role="alert" aria-live="polite">
  <h3>Something went wrong</h3>
  <p>We couldn't load your data. Please try again.</p>
  <button class="retry-btn" onclick="retryLoad()">Try Again</button>
</div>
```
Provide retry path. Never expose raw error codes to users.

---

## Mobile UX (iOS / Android)

### Telegram-Style Navigation Patterns

Telegram's 2025 redesign sets the benchmark for mobile glassmorphism navigation. Reference these patterns for any mobile app.

#### Floating Bottom Nav Bar (Recommended)
```css
/* Telegram-style floating bottom navigation */
.floating-nav {
  position: fixed;
  bottom: 8px;
  left: 8px;
  right: 8px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  padding: 8px 16px;
  display: flex;
  justify-content: space-around;
  z-index: 100;
  /* 4 tabs: Contacts · Calls · Chats · Profile */
}

/* Nav item states */
.nav-item {
  color: rgba(255, 255, 255, 0.5);  /* inactive */
  transition: color 200ms ease;
}
.nav-item.active {
  color: #3390ec;  /* Telegram blue accent */
}
.nav-item svg {
  width: 24px;
  height: 24px;
}
```

#### Bottom Sheet Modal
```css
.bottom-sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  border-radius: 24px 24px 0 0;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-bottom: none;
  padding: 16px;
  max-height: 80vh;
  overflow-y: auto;
}
```

#### iOS Dynamic Island / Notch Clearance
```css
/* Reserve ~60px at top for notch/Dynamic Island */
header {
  padding-top: max(12px, env(safe-area-inset-top));
}
```

### Thumb Zone Rule
**Primary CTAs MUST be in the bottom 60% of viewport (thumb zone).**

| Zone | What goes here |
|------|----------------|
| Top 40% | Context, navigation, display information |
| Bottom 60% | Actions, forms, primary CTAs, FAB |

### Touch Target Minimums
| Platform | Minimum | Recommended |
|---|---|---|
| Mobile | 44×44px | 48×48px |
| Tablet | 44×44px | 56×56px |
| Desktop | 24×24px | 32×32px |

**Gap rule:** Interactive elements must have ≥8px gap between them on mobile.

### Mobile Typography
- **Body text:** Minimum 16px on mobile (prevents iOS auto-zoom on input focus)
- **Line length:** 65-75 characters max (use `max-w-sm` or `max-w-md`)
- **Line height:** 1.5-1.75 for body text
- **Headings:** clamp(1.5rem, 5vw, 3rem) for fluid scaling
- **System fonts:** SF Pro (iOS), Roboto (Android) preferred for native feel

### Mobile Utility Layout Rules
- Avoid absolute-positioned preview stacks for primary utility content.
- The first viewport should establish task clarity before decorative flourish.
- Hero headings on utility screens must preserve readable wrapping and credible line-length at ~390px width.
- Decorative inset cards must remain secondary and must not simulate the main working surface.

---

## Icons & Visual Elements

### Icons Rules (from ui-ux-pro-max)
| Rule | Do | Don't |
|------|----|-------|
| **No emoji icons** | Use SVG icons (Heroicons, Lucide, Phosphor, Tabler) | Use emojis like 🎨 🚀 ⚙️ as UI icons |
| **No emoji logos** | Draw brand marks as SVG/vector symbols with intentional geometry | Drop in 🛍️ ✨ 🔥 💸 or similar glyphs as the app/logo mark |
| **Stable hover states** | Use color/opacity transitions on hover | Use scale transforms that shift layout |
| **Consistent icon sizing** | Fixed viewBox (24x24) with `w-6 h-6` | Mix different icon sizes randomly |
| **Icon library choice** | Pick ONE per project (match Design Recipe) | Mix icon families |

### Icon Size Scale
- 18px — inline text accompaniment
- 24px — default for nav and actions
- 32px — feature/highlight icons
- 48px — hero/landing page icons

### Brand Mark Rules
- Brand marks must be intentionally drawn as SVG/vector symbols or typographic marks.
- Do not use emoji, Unicode pictographs, or platform-native glyphs as the app/logo mark.
- If a shopping bag, spark, cart, star, coin, or similar metaphor is needed, redraw it as part of the chosen icon language.
- The brand mark should match the project's icon family weight and visual grammar.

### Icon Semantic Map (Phosphor example)
| Purpose | Icon | Class |
|---|---|---|
| Navigation: back | arrow-left | `ph-arrow-left` |
| Navigation: forward | arrow-right | `ph-arrow-right` |
| Actions: add | plus | `ph-plus` |
| Actions: delete | trash | `ph-trash` |
| Status: success | check-circle | `ph-check-circle` |
| Status: error | warning-circle | `ph-warning-circle` |
| Commerce: cart | shopping-cart | `ph-shopping-cart` |
| Data: chart | chart-bar | `ph-chart-bar` |

---

## Light / Dark Mode Contrast

| Rule | Light Mode | Dark Mode |
|------|------------|-----------|
| **Glass surface** | `bg-white/80` or higher opacity | `bg-white/10` (low opacity OK) |
| **Text contrast** | `#0F172A` (slate-900) | `#E2E8F0` (slate-200) |
| **Muted text** | `#475569` (slate-600) minimum | `#94A3B8` (slate-400) |
| **Border visibility** | `border-gray-200` | `border-white/10` |

**Common failure:** Using `bg-white/10` in light mode — it's invisible. Use `bg-white/80` minimum.

---

## Layout & Spacing

## Utility Screen Realism

Generator, result, form, dashboard, and settings screens are not posters.

- Prefer stable vertical or grid flow over layered concept composition.
- Reserve overlap or stacked-card effects for non-critical decorative modules only.
- Inputs, validation, result payloads, and action groups must remain in normal layout flow.
- If a screen is meant for repeated daily use, optimize for trust and scanability before visual spectacle.
- Decorative modules must not weaken CTA discoverability or make the page feel detached from its working grid.
- Mobile utility screens must look credible at 390px width.
- Desktop utility screens must look credible at 1280px width.

### Responsive Breakpoints
| Breakpoint | Width | Layout |
|---|---|---|
| Mobile | <640px | Single column |
| Tablet | 640-1023px | 2-column, smaller cards |
| Desktop | 1024-1439px | 3-4 column grid |
| Wide | ≥1440px | Max-width container |

### Navbar Spacing
| Rule | Light | Dark |
|------|-------|------|
| **Floating navbar** | Add `top-4 left-4 right-4` spacing | Same |
| **Sticky navbar** | `top-0 left-0 right-0` OK | Same |

### Content Padding
Always account for fixed navbar/header height — content must not hide behind fixed elements.

---

## Form Patterns

### Required: Label Association
```html
<div class="form-group">
  <label for="habit-name">Habit Name</label>
  <input type="text" id="habit-name" name="habitName" required />
</div>
```
Every input MUST have a visible label. Never use placeholder-only labels.

### Required: Input States
- **Default**: Base border, placeholder text
- **Focus**: Border color change + visible focus ring
- **Error**: Red border + error message below + `aria-invalid="true"`
- **Disabled**: Grayed out, `aria-disabled="true"`, `cursor: not-allowed`

### Error Message Pattern
```html
<div class="form-group">
  <label for="email">Email</label>
  <input type="email" id="email" aria-invalid="true" aria-describedby="email-error" />
  <span id="email-error" class="form-error" role="alert">
    Please enter a valid email address.
  </span>
</div>
```

---

## Micro-Interactions

### Button States (All Required)
Every button MUST implement all 4 states:

```css
/* Default */
.btn {
  background: var(--btn-bg);
  transition: transform 150ms ease, box-shadow 150ms ease;
}

/* Hover — NOT just opacity */
.btn:hover {
  transform: scale(1.02);
  box-shadow: 0 6px 20px rgba(var(--accent-rgb), 0.25);
}

/* Active/Press — tactile feedback */
.btn:active {
  transform: scale(0.97);
  box-shadow: 0 2px 8px rgba(var(--accent-rgb), 0.2);
}

/* Focus — visible ring */
.btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* Disabled */
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
```

### Spring Easing
```css
/* Spring — panel appears, modal open, tab switch */
--ease-spring: cubic-bezier(0.16, 1, 0.3, 1);  /* RECOMMENDED default */

/* Bounce — playful buttons, celebration animations */
--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);

/* Smooth — hover states, focus transitions */
--ease-smooth: cubic-bezier(0.25, 1, 0.5, 1);
```

### Micro-Animation Duration Scale
| Type | Duration | Example |
|------|----------|---------|
| Micro | 50-100ms | Icon toggle, toggle switch |
| State | 150-300ms | Button hover, tab switch, dropdown open |
| Entrance | 300-500ms | Modal open, card entrance |
| Page | 400-700ms | Screen transition, parallax |

---

## Progressive Disclosure

**Show only what the user needs at each step.** Additional detail reveals on demand.

| Pattern | Use When |
|---------|---------|
| Accordion/Collapse | FAQ, settings sections |
| Tabbed Content | Multi-section screens (one tab active) |
| "Show More" | Long lists (show 3-5, reveal remainder) |
| Tooltip on Demand | Dense data tables, icon-only buttons |

**Anti-pattern:** Progressive disclosure is NOT hidden complexity. Frequently-used features should be visible by default.

---

## Navigation Consistency

### Bottom Tab Bar (Mobile)
- 3-5 tabs maximum
- Icon + label required for each tab
- Active tab visually distinct (color, scale, underline)
- Badge/notification dot for alerts

### Sidebar (Desktop/Tablet)
- Persistent on desktop (≥1024px)
- Collapsible to icon rail at 768-1024px
- Current section highlighted

### Back Navigation
| Platform | Pattern |
|---|---|
| Mobile | Physical back button + in-app back arrow in header |
| Desktop | Breadcrumb trail or back link |

---

## Gesture Patterns (Mobile)

| Gesture | Action |
|---------|--------|
| Swipe left | Reveal list item actions (edit, delete) |
| Swipe down | Pull-to-refresh content |
| Swipe up | Dismiss bottom sheet / modal |
| Long press | Context menu |

---

## Animation & Motion

### Stagger Pattern
```css
.item:nth-child(1) { animation-delay: 0ms; }
.item:nth-child(2) { animation-delay: 60ms; }
.item:nth-child(3) { animation-delay: 120ms; }
.item:nth-child(4) { animation-delay: 180ms; }
/* ... */
```

### Reduced Motion (Mandatory)
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
```

---

## Accessibility Minimums (All Platforms)

### The Big Four
1. **Contrast**: Text ≥4.5:1 (AA), UI components ≥3:1 (AA), large text ≥3:1
2. **Focus visible**: `:focus-visible` ring on ALL interactive elements — never invisible
3. **Touch targets**: ≥44×44px with ≥8px gap on mobile/tablet
4. **Color alone**: Never convey information through color alone — add icon/text/pattern

### Semantic HTML
| Wrong | Right |
|-------|-------|
| `<div onclick="...">` | `<button>` |
| `<div class="nav">` | `<nav>` |
| `<div class="btn">` | `<button class="btn">` |
| `<span role="checkbox">` | `<input type="checkbox">` |

### Keyboard Navigation
All interactive elements must be reachable and operable via keyboard:
- **Tab** — move forward through focusable elements
- **Shift+Tab** — move backward
- **Enter/Space** — activate buttons and links
- **Escape** — close modals, dropdowns, tooltips
- **Arrow keys** — navigate within menus, tabs, sliders

### Alt Text Rules
| Image Type | Alt Text |
|------------|---------|
| Informational | Descriptive: "Screenshot of dashboard showing revenue chart" |
| Decorative | `alt=""` (empty) |
| Action-triggering | Describe the action: "Close dialog" |

### ARIA Quick Reference
```html
<!-- Live region for dynamic updates -->
<div aria-live="polite" aria-atomic="true">...</div>

<!-- Dialog -->
<div role="dialog" aria-modal="true" aria-labelledby="dialog-title">...</div>

<!-- Error alert -->
<div role="alert" aria-live="assertive">...</div>

<!-- Loading state -->
<div aria-busy="true" aria-label="Loading dashboard">...</div>
```
