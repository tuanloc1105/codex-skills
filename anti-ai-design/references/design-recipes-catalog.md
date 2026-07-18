# Design Recipes Catalog

15 complete DesignRecipe objects — structured aesthetic directives for wireframe prompts. Each recipe constrains: layout, motion, icon library, font tier, CSS patterns, and anti-patterns.

15 recipes: 10 product-typed (priority 1-3) + 5 wild-card (priority 10, high-variance only).

---

## Product-Typed Recipes (Priority 1-3)

### Recipe 1: Nordic Minimal
- **ID:** `nordic-minimal`
- **Name:** Nordic Minimal
- **Description:** Clean Scandinavian restraint — breathable whitespace, hairline borders, typographic confidence.
- **Product Types:** SaaS, Minimal
- **Priority:** 1
- **Vibe Archetype:** Clean Scandinavian
- **Layout Preference:** left-aligned-hero
- **Motion Preset:** FADE_UP
- **Signature Element:** Oversized left-aligned heading with 1px hairline rule below
- **Font Tier:** moderate
- **Icon Style:** outlined | **Icon Library:** heroicons
- **CSS Patterns:**
  - `border-b border-gray-200 pb-8 mb-12`
  - `text-left max-w-xl space-y-4`
  - `bg-gray-50 border border-gray-100 rounded-lg p-6`
  - `tracking-tight font-semibold text-4xl text-gray-900`
  - `text-gray-500 text-sm uppercase tracking-widest`
- **Anti-Patterns:**
  - Centered hero without motion
  - Heavy drop shadows
  - Gradients
  - Rounded-3xl or pill shapes
- **Compatible Art Packs:** warm-editorial

---

### Recipe 2: Editorial Luxury
- **ID:** `editorial-luxury`
- **Name:** Editorial Luxury
- **Description:** Magazine-premium full-bleed layouts with expressive serif display and editorial spacing.
- **Product Types:** Luxury, Creative
- **Priority:** 1
- **Vibe Archetype:** Magazine premium
- **Layout Preference:** full-bleed-hero
- **Motion Preset:** CLIP_REVEAL
- **Signature Element:** Full-bleed image hero with serif headline overlaid at 90% height
- **Font Tier:** bold
- **Icon Style:** rounded | **Icon Library:** lucide
- **CSS Patterns:**
  - `w-full h-screen relative overflow-hidden`
  - `absolute bottom-12 left-12 right-12 text-white`
  - `font-serif text-6xl leading-none tracking-tight`
  - `border-t border-white/30 pt-4 mt-4`
  - `mix-blend-multiply bg-black/40 absolute inset-0`
- **Anti-Patterns:**
  - Card-based layouts
  - Sans-serif body as headline
  - Pastel colors
  - Navigation bars inside hero
- **Compatible Art Packs:** warm-editorial, glass-premium

---

### Recipe 3: Electric Dashboard
- **ID:** `electric-dashboard`
- **Name:** Electric Dashboard
- **Description:** Data-dense dark bento grid with glowing metric cards and precise two-tone iconography.
- **Product Types:** Dashboard, Fintech
- **Priority:** 1
- **Vibe Archetype:** Data-dense dark
- **Layout Preference:** bento-grid
- **Motion Preset:** SCALE_IN
- **Signature Element:** Glowing KPI card with OKLCH accent border and sparkline
- **Font Tier:** moderate
- **Icon Style:** two-tone | **Icon Library:** material-symbols
- **CSS Patterns:**
  - `bg-gray-950 text-white min-h-screen`
  - `grid grid-cols-4 gap-3 p-4`
  - `bg-gray-900 border border-white/8 rounded-xl p-5`
  - `text-3xl font-bold tabular-nums text-emerald-400`
  - `border border-emerald-500/20 shadow-[0_0_24px_-4px_oklch(0.7_0.2_155/0.3)]`
- **Anti-Patterns:**
  - Light backgrounds
  - Centered single-column layout
  - Serif fonts
  - Warm earth tones
- **Compatible Art Packs:** glass-premium

---

### Recipe 4: Warm Craft
- **ID:** `warm-craft`
- **Name:** Warm Craft
- **Description:** Handmade organic warmth — earth tones, paper texture, soft spring motion.
- **Product Types:** Nature, Healthcare
- **Priority:** 1
- **Vibe Archetype:** Handmade organic
- **Layout Preference:** split-hero
- **Motion Preset:** SPRING_SOFT
- **Signature Element:** Paper-texture card with warm terracotta accent and handwritten-style label
- **Font Tier:** safe
- **Icon Style:** outlined | **Icon Library:** tabler
- **CSS Patterns:**
  - `bg-amber-50 text-stone-800`
  - `border border-amber-200 rounded-2xl p-6 shadow-sm`
  - `text-terracotta font-medium uppercase tracking-wider text-xs`
  - `flex gap-8 items-start max-w-5xl mx-auto px-6 py-16`
  - `bg-stone-100 rounded-xl overflow-hidden aspect-square`
- **Anti-Patterns:**
  - Dark backgrounds
  - Neon or electric colors
  - Sharp geometric sans headlines
  - Glassmorphism
- **Compatible Art Packs:** warm-editorial

---

### Recipe 5: Playful Pop
- **ID:** `playful-pop`
- **Name:** Playful Pop
- **Description:** Fun bouncy energy for education and e-commerce — saturated pastels, rounded shapes, spring physics.
- **Product Types:** Education, E-commerce
- **Priority:** 1
- **Vibe Archetype:** Fun bouncy
- **Layout Preference:** centered-hero
- **Motion Preset:** SPRING_BOUNCY
- **Signature Element:** Oversized rounded pill button with drop shadow + bounce hover
- **Font Tier:** moderate
- **Icon Style:** rounded | **Icon Library:** phosphor
- **CSS Patterns:**
  - `bg-violet-50 min-h-screen`
  - `rounded-3xl px-10 py-5 bg-violet-500 text-white font-bold text-lg shadow-lg hover:shadow-xl`
  - `grid grid-cols-2 md:grid-cols-3 gap-4 p-6`
  - `bg-white rounded-2xl p-5 shadow-md border border-violet-100`
  - `text-violet-600 font-extrabold text-5xl text-center leading-none`
- **Anti-Patterns:**
  - Dark color scheme
  - Hairline borders
  - Monospace fonts
  - Grid-dense data layouts
- **Compatible Art Packs:** warm-editorial

---

### Recipe 6: Swiss Precision
- **ID:** `swiss-precision`
- **Name:** Swiss Precision
- **Description:** Grid-perfect Helvetica-era rigour — 12-column system, proportional spacing, zero decoration.
- **Product Types:** SaaS, Dashboard
- **Priority:** 2
- **Vibe Archetype:** Grid-perfect
- **Layout Preference:** 12-col-grid
- **Motion Preset:** FADE_UP
- **Signature Element:** Strict 12-column grid with visible baseline rhythm and numbered section markers
- **Font Tier:** safe
- **Icon Style:** outlined | **Icon Library:** heroicons
- **CSS Patterns:**
  - `grid grid-cols-12 gap-x-4 gap-y-0`
  - `col-span-8 border-l-4 border-black pl-6`
  - `text-xs font-mono text-gray-400 tracking-widest uppercase`
  - `border-t border-gray-900 pt-4`
  - `max-w-screen-xl mx-auto px-8`
- **Anti-Patterns:**
  - Decorative blurs or gradients
  - Asymmetric overlapping elements
  - Rounded corners beyond 4px
  - Motion beyond fade
- **Compatible Art Packs:** warm-editorial

---

### Recipe 7: Noir Cinema
- **ID:** `noir-cinema`
- **Name:** Noir Cinema
- **Description:** Dramatic dark cinematics — deep blacks, clip-path reveals, bold display typography.
- **Product Types:** Creative, Luxury
- **Priority:** 2
- **Vibe Archetype:** Dramatic dark
- **Layout Preference:** centered-cinematic
- **Motion Preset:** CLIP_REVEAL
- **Signature Element:** Black full-viewport section with single white headline at optical centre
- **Font Tier:** bold
- **Icon Style:** filled | **Icon Library:** material-symbols
- **CSS Patterns:**
  - `bg-black text-white min-h-screen flex items-center justify-center`
  - `text-7xl font-black uppercase tracking-tighter leading-none`
  - `border border-white/10 p-px rounded-none`
  - `opacity-60 text-xs tracking-[0.3em] uppercase text-gray-400`
  - `w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent my-12`
- **Anti-Patterns:**
  - Light backgrounds
  - Rounded pill shapes
  - Pastel or warm palette
  - Busy multi-column grids
- **Compatible Art Packs:** glass-premium

---

### Recipe 8: Soft Cloud
- **ID:** `soft-cloud`
- **Name:** Soft Cloud
- **Description:** Airy pastel floating cards — approachable and gentle, ideal for healthcare and education.
- **Product Types:** Healthcare, Education
- **Priority:** 2
- **Vibe Archetype:** Airy pastel
- **Layout Preference:** floating-cards
- **Motion Preset:** SPRING_SOFT
- **Signature Element:** Floating white card on tinted pastel background with soft multi-layer shadow
- **Font Tier:** safe
- **Icon Style:** rounded | **Icon Library:** phosphor
- **CSS Patterns:**
  - `bg-sky-50 min-h-screen p-8`
  - `bg-white rounded-3xl p-8 shadow-[0_4px_32px_rgba(0,0,0,0.06)] border border-sky-100`
  - `text-sky-700 font-semibold text-lg`
  - `flex flex-wrap gap-4 justify-center`
  - `text-gray-500 text-sm leading-relaxed`
- **Anti-Patterns:**
  - Dark mode
  - Harsh borders
  - Monospace or slab fonts
  - High-contrast neo-brutalist patterns
- **Compatible Art Packs:** warm-editorial

---

### Recipe 9: Bold Commerce
- **ID:** `bold-commerce`
- **Name:** Bold Commerce
- **Description:** Conversion-focused e-commerce layout — split hero scroll, snappy motion, dominant CTAs.
- **Product Types:** E-commerce
- **Priority:** 1
- **Vibe Archetype:** Conversion-focused
- **Layout Preference:** split-hero-scroll
- **Motion Preset:** SPRING_SNAPPY
- **Signature Element:** Sticky price + CTA block alongside scrolling product imagery
- **Font Tier:** moderate
- **Icon Style:** filled | **Icon Library:** material-symbols
- **CSS Patterns:**
  - `grid grid-cols-1 lg:grid-cols-2 min-h-screen`
  - `sticky top-0 h-screen flex flex-col justify-center p-12`
  - `text-5xl font-extrabold tracking-tight text-gray-900`
  - `text-3xl font-bold text-emerald-600`
  - `w-full py-4 bg-gray-900 text-white font-bold rounded-xl hover:bg-gray-800 active:scale-95 transition-all`
- **Anti-Patterns:**
  - Heavy editorial whitespace
  - Centered minimal layout
  - No call-to-action above fold
  - Soft pastel palette
- **Compatible Art Packs:** neo-brutalist-light, warm-editorial

---

### Recipe 10: Retro Terminal
- **ID:** `retro-terminal`
- **Name:** Retro Terminal
- **Description:** Nostalgic tech aesthetic — amber-on-dark monospace panels, sticky sidebar, CRT scanlines.
- **Product Types:** Fintech, Dashboard
- **Priority:** 3
- **Vibe Archetype:** Nostalgic tech
- **Layout Preference:** sticky-sidebar
- **Motion Preset:** FADE_UP
- **Signature Element:** CRT scanline overlay with amber monospace text on near-black surface
- **Font Tier:** bold
- **Icon Style:** filled | **Icon Library:** lucide
- **CSS Patterns:**
  - `bg-[#0d0d0d] text-amber-400 font-mono min-h-screen`
  - `flex h-screen overflow-hidden`
  - `w-56 border-r border-amber-500/20 p-4 flex-shrink-0`
  - `text-xs text-amber-600 uppercase tracking-widest mb-1`
  - `[background-image:repeating-linear-gradient(0deg,transparent,transparent_2px,rgba(0,0,0,0.3)_2px,rgba(0,0,0,0.3)_4px)]`
- **Anti-Patterns:**
  - Light backgrounds
  - Rounded corners beyond 4px
  - Sans-serif as primary typeface
  - Pastel or saturated colors
- **Compatible Art Packs:** glass-premium

---

## Wild-Card Recipes (Priority 10 — High Variance Only)

These are selected at variance >= 8 OR when user explicitly picks them.

---

### Recipe 11: Neo-Brutalist Raw
- **ID:** `neo-brutalist-raw`
- **Name:** Neo-Brutalist Raw
- **Description:** Punk graphic design — hard grid, zero radius, thick black borders, neon accent.
- **Product Types:** (none — wild-card)
- **Priority:** 10
- **Vibe Archetype:** Punk graphic
- **Layout Preference:** dense-grid
- **Motion Preset:** SPRING_SNAPPY
- **Signature Element:** Hard 4px black border with 4px offset drop shadow on every card
- **Font Tier:** bold
- **Icon Style:** filled | **Icon Library:** tabler
- **CSS Patterns:**
  - `border-4 border-black shadow-[4px_4px_0_#000]`
  - `bg-white text-black rounded-none`
  - `uppercase font-black tracking-wider`
  - `grid grid-cols-3 gap-0 border-4 border-black`
  - `bg-lime-400 hover:bg-lime-300 active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all`
- **Anti-Patterns:**
  - Rounded corners
  - Gradients
  - Glassmorphism
  - Soft shadows
  - Serif fonts
- **Compatible Art Packs:** neo-brutalist-light

---

### Recipe 12: Glass Aurora
- **ID:** `glass-aurora`
- **Name:** Glass Aurora
- **Description:** Ethereal premium glassmorphism — layered frosted panels over aurora gradient background.
- **Product Types:** (none — wild-card)
- **Priority:** 10
- **Vibe Archetype:** Ethereal premium
- **Layout Preference:** centered-floating
- **Motion Preset:** SCALE_IN
- **Signature Element:** Frosted glass card with aurora gradient blob visible through blur
- **Font Tier:** bold
- **Icon Style:** rounded | **Icon Library:** phosphor
- **CSS Patterns:**
  - `relative overflow-hidden bg-gradient-to-br from-violet-950 via-indigo-900 to-sky-900 min-h-screen`
  - `absolute w-96 h-96 rounded-full blur-3xl opacity-40 pointer-events-none`
  - `bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8`
  - `text-white font-semibold text-xl`
  - `shadow-[0_8px_32px_rgba(0,0,0,0.4),inset_0_1px_rgba(255,255,255,0.2)]`
- **Anti-Patterns:**
  - White backgrounds
  - No blur effect
  - Warm earth tones
  - Harsh solid borders
- **Compatible Art Packs:** glass-premium

---

### Recipe 13: Kinetic Magazine
- **ID:** `kinetic-magazine`
- **Name:** Kinetic Magazine
- **Description:** Motion-editorial with asymmetric scroll — text layers, parallax depth, clip-path reveals.
- **Product Types:** (none — wild-card)
- **Priority:** 10
- **Vibe Archetype:** Motion-editorial
- **Layout Preference:** asymmetric-scroll
- **Motion Preset:** CLIP_REVEAL
- **Signature Element:** Overlapping typography layers with different scroll speeds creating parallax depth
- **Font Tier:** bold
- **Icon Style:** outlined | **Icon Library:** heroicons
- **CSS Patterns:**
  - `relative overflow-hidden`
  - `absolute text-[20vw] font-black text-gray-100 select-none pointer-events-none leading-none`
  - `relative z-10 max-w-2xl`
  - `text-5xl font-bold leading-tight tracking-tight`
  - `grid grid-cols-[2fr_1fr] gap-12 items-start`
- **Anti-Patterns:**
  - Static non-scrolling layout
  - Uniform symmetric grid
  - Flat monochrome palette
  - Rounded pill elements
- **Compatible Art Packs:** warm-editorial, glass-premium

---

### Recipe 14: Tactile Clay
- **ID:** `tactile-clay`
- **Name:** Tactile Clay
- **Description:** Physical 3D clay aesthetic — inflated rounded shapes, multi-layer shadows, bouncy spring physics.
- **Product Types:** (none — wild-card)
- **Priority:** 10
- **Vibe Archetype:** Physical 3D
- **Layout Preference:** floating-cards-3d
- **Motion Preset:** SPRING_BOUNCY
- **Signature Element:** Puffy inflated card with inner highlight shadow + outer depth shadow
- **Font Tier:** moderate
- **Icon Style:** rounded | **Icon Library:** phosphor
- **CSS Patterns:**
  - `bg-gradient-to-b from-pink-100 to-purple-100 min-h-screen p-8`
  - `rounded-3xl p-6 shadow-[0_10px_40px_-10px_rgba(0,0,0,0.2),inset_0_1px_rgba(255,255,255,0.8)]`
  - `bg-white/80 backdrop-blur-sm`
  - `text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-b from-gray-800 to-gray-600`
  - `active:scale-95 active:shadow-[0_4px_16px_-4px_rgba(0,0,0,0.2)] transition-all duration-150`
- **Anti-Patterns:**
  - Flat design with no depth
  - Dark backgrounds
  - Sharp corners
  - Monospace fonts
- **Compatible Art Packs:** warm-editorial

---

### Recipe 15: Futurist Holo
- **ID:** `futurist-holo`
- **Name:** Futurist Holo
- **Description:** Sci-fi chrome split-screen — holographic gradients, sharp icon geometry, neon glow accents.
- **Product Types:** (none — wild-card)
- **Priority:** 10
- **Vibe Archetype:** Sci-fi chrome
- **Layout Preference:** split-screen
- **Motion Preset:** SCALE_IN
- **Signature Element:** Holographic gradient border with scan-line shimmer animation
- **Font Tier:** bold
- **Icon Style:** sharp | **Icon Library:** material-symbols
- **CSS Patterns:**
  - `bg-[#050510] text-white min-h-screen`
  - `grid grid-cols-2 h-screen`
  - `border border-transparent [background:linear-gradient(#050510,#050510)_padding-box,linear-gradient(135deg,#06b6d4,#8b5cf6,#ec4899)_border-box] rounded-xl`
  - `text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-violet-400 to-pink-400`
  - `shadow-[0_0_60px_-10px_rgba(139,92,246,0.6)]`
- **Anti-Patterns:**
  - Light backgrounds
  - Warm earth tones
  - Rounded pill shapes
  - Soft or organic forms
- **Compatible Art Packs:** glass-premium

---

## Icon System Reference

Each recipe specifies an icon library. Use the correct CDN and semantic icon names:

| Library | CDN | CSS Class | Semantic Names Example |
|---|---|---|---|
| **heroicons** | `<script src="https://cdn.jsdelivr.net/npm/heroicons@2.1.5/24/outline/index.js">` | SVG inline | arrow-left, bars-3, check-circle |
| **phosphor** | `<link href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css">` | `<i class="ph ph-icon-name">` | ph-arrow-left, ph-plus, ph-check-circle |
| **tabler** | `<link href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css">` | `<i class="ti ti-icon-name">` | ti-arrow-left, ti-plus, ti-circle-check |
| **lucide** | `<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js">` | `<i data-lucide="icon-name">` | arrow-left, plus, check-circle |
| **material-symbols** | `<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,0">` | `<span class="material-symbols-rounded">` | arrow_back, add, check_circle |

**Rules for ALL icon libraries:**
- Pick ONE library per project — NEVER mix families
- Prefer specific icons over generic (e.g., "key" for API keys, NOT "settings" cog)
- Optically align icons with text baselines: `vertical-align: -0.125em` for inline
- All icons in a view MUST use same weight/stroke-width
- Size scale: 18px inline · 24px default · 32px feature · 48px hero
- NEVER use emoji as icons

---

## Recipe Selection Guide

| Variance (1-10) | Font Tier Preference | Suggested Recipes |
|---|---|---|
| 1-3 (low) | safe | Nordic Minimal, Swiss Precision, Soft Cloud, Warm Craft |
| 4-6 (moderate) | moderate | Playful Pop, Bold Commerce, Nordic Minimal, Electric Dashboard |
| 7-9 (high) | bold | Editorial Luxury, Noir Cinema, Electric Dashboard, Futurist Holo |
| 10 (wild-card) | any | Neo-Brutalist Raw, Glass Aurora, Kinetic Magazine, Tactile Clay, Futurist Holo |

**Platform bias:** desktop/cli/mcp prefer dense layouts → use Electric Dashboard, Swiss Precision, Retro Terminal, Obsidian Lime.
