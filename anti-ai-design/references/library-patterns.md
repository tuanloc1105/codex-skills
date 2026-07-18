# Library Patterns

Apply these rules when the implementation target is library-aware.

## SvelteKit
- Prefer route-driven screen decomposition and predictable page boundaries.
- Avoid assumptions that require browser-only globals before hydration.
- Keep interaction logic local to the screen that owns it; do not imply hidden global event buses.
- For product design, preserve believable form and state transitions that can survive SSR + client enhancement.

## shadcn/ui
- Preserve primitive semantics: Dialog stays a dialog, Sheet stays a sheet, Tabs stay tabs.
- Customize through tokens, spacing, hierarchy, shell layout, and motion before replacing the primitive anatomy.
- Prefer a small number of strong compositional moves over a bespoke wrapper around every component.
- Avoid doc-default blandness, but also avoid destroying Radix interaction expectations.
- **NEVER use native browser form controls for select, date, or time inputs.** Always replace with shadcn/ui primitives:
  - `<select>` → `<Select>` + `<SelectTrigger>` + `<SelectContent>` + `<SelectItem>` (Radix Select)
  - `<input type="date">` → `<Popover>` + `<Calendar>` (from `shadcn/ui calendar`, built on `react-day-picker`)
  - `<input type="time">` → `<Popover>` + a custom time-picker built with `<ScrollArea>` + hour/minute columns, or a third-party headless time wheel that respects Radix focus management
  - Native browser controls are forbidden regardless of how simple the use case appears — they break visual consistency, ignore design tokens, and cannot be styled to match the design system.

## SvelteKit + shadcn-svelte
- Apply all SvelteKit rules above.
- **NEVER use native browser form controls for select, date, or time inputs.** Always replace with shadcn-svelte equivalents:
  - `<select>` → shadcn-svelte `<Select>` built on Bits UI
  - `<input type="date">` → shadcn-svelte `<Calendar>` inside a `<Popover>`
  - `<input type="time">` → custom time-picker built with `<ScrollArea>` + hour/minute columns inside a `<Popover>`
  - Same rationale as shadcn/ui: native controls break token theming, are unstyable cross-browser, and destroy visual consistency.

## Ant Design
- Use Ant Design mental models for enterprise-heavy screens: tables, filters, drawers, forms, steps, toolbars.
- Favor clear action rows, stable density, and credible data-first hierarchy over decorative compositions.
- Customize premium feel through spacing, typography, color, radius, and sectional emphasis, not through breaking form/table ergonomics.
- Utility credibility beats spectacle on Ant Design-style workflows.

## Tailwind CSS
- Express all design tokens through `tailwind.config` theme extensions (`colors`, `fontFamily`, `borderRadius`, `spacing`, `boxShadow`) — never use arbitrary values like `bg-[#1a2b3c]` when a token alias can be defined instead.
- Use utility classes as the primary styling approach; reserve `@apply` only for patterns repeated verbatim across 3+ components (e.g., a shared button primitive).
- Map foundation tokens directly to Tailwind theme keys so `bg-primary`, `text-muted`, `rounded-surface` etc. work as semantic aliases.
- Anti-patterns to avoid: inline `style={{}}` for layout, hardcoded hex values in class strings, wrapping every element in a custom component just to avoid composing utilities.
- For dark mode: use the `class` strategy (`darkMode: 'class'`) so the skill's `data-theme` toggle works correctly; never rely solely on `media` strategy when a manual toggle is needed.

## React Components (custom_app / shadcn_ui / tailwind_css)
- Generate `.tsx` files with an explicit named `Props` interface at the top of each component.
- Use CSS Modules or scoped `styles` objects for screen-specific styling — never `style={{}}` for layout properties.
- Source foundation tokens from CSS custom properties (`var(--color-primary)`) or a typed `tokens.ts` export; never hardcode design values inline.
- Shared layout shells, nav primitives, and repeated compositions belong in a `components/shared/` directory, not duplicated per screen.
- State completeness (loading / empty / error / success) must be expressed as distinct render branches, not just CSS class toggles.

## Cross-library copy filter
- Do not ship meta labels like `mobile view`, `desktop view`, `review board`, `default state`, `empty default`, `success default`, `CJX review`, `state canvas`, `inspection`, or `design note` inside real-product UI.
