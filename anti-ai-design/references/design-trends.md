# Design Trends & Art Direction Packs

6 distinct trends + 3 art direction packs. Each trend fully constrains AI output aesthetics. Art packs are enriched with platform navigation models, wow effects, and reference tags.

---

## Section 1: Core Trends (6)

### Trend 1: Human-Centric
**Human-Centric** (v1.0.0) — Original 2026 trend. High-end editorial precision, zero generic AI glassmorphism.

- **Typography:** Ban standard system fonts (Inter, Roboto, Arial). Use bold, expressive, variable fonts (Space Grotesk, Syne, Plus Jakarta Sans). Oversized headings with tight line-height.
- **Materiality:** ABSOLUTE BAN on generic AI glassmorphism, glowing orbs, heavy blurs. Use solid backgrounds, 1px hairline borders (rgba(255,255,255,0.1)), razor-sharp contrast. Subtle SVG noise 1-2% opacity only.
- **Composition:** Avoid edge-to-edge full-bleed layouts. Wrap main content in framed container with border-radius and generous negative space. Asymmetric CSS Grid.
- **Color:** Avoid safe tech blue and bland neutral gray. Use warm organic palettes (earth tones), deep OLED dark modes (OKLCH), or high-contrast neo-brutalism accents.
- **Motion:** Hero sections grounded and architectural. NO floating blurred orbs. Strict grid animations, precise clipping masks, elegant typography reveals. Spring-like easing: cubic-bezier(0.25, 1, 0.5, 1). Honor prefers-reduced-motion.

### Trend 2: Neo-Brutalism
**Neo-Brutalism** (v1.0.0) — Punk graphic design, hard grid, zero radius.

- **Typography:** Monospace display (Space Mono, JetBrains Mono) + chunky sans (Archivo Black, DM Sans Black). Oversized headings as graphic elements. Text used decoratively — rotate, overlap, uppercase. NEVER rounded/friendly fonts.
- **Materiality:** Thick solid borders (3-4px black). Hard drop-shadows (4-6px offset, 0 blur, #000). ZERO blur, ZERO gradients, ZERO glassmorphism. Visible grid lines as design element. Background: pure white or pure black only.
- **Composition:** Harsh grid with visible borders (gap:0 + border on children). Broken alignment for emphasis — one element intentionally misaligned. No rounded corners (border-radius: 0).
- **Color:** Maximum contrast: black #000 + white #fff base. Accent via single neon hue — lime #a3e635 OR hot-pink #ec4899 OR yellow #facc15. NEVER gradients. NEVER more than 3 colors total.
- **Motion:** Abrupt transitions: step-start or 50ms. Scale jumps on hover (1.0→1.05 instant). NO spring physics. Elements snap, not glide.

### Trend 3: Warm Editorial
**Warm Editorial** (v1.0.0) — Magazine-premium, organic warmth, craft feel.

- **Typography:** Expressive serif display (Playfair Display, Fraunces, Lora). Body: Plus Jakarta Sans or DM Sans. Oversized headings with tight line-height. Mixed serif+sans hierarchy creates magazine feel.
- **Materiality:** Paper/ink texture via subtle SVG noise (1-2% opacity). Warm shadows (rgba(139,90,43,0.1)). 1px hairline borders. NO harsh edges. Surface feels like premium print.
- **Composition:** Magazine/zine layout: asymmetric CSS Grid, 2-col with one oversized. Generous whitespace. Content wrapped in bordered container with padding from viewport edges. Overlapping elements for depth.
- **Color:** Warm earth tones: terracotta #c4683f, olive #6b7f3b, cream #faf5e4, charcoal #2d2d2d, burnt sienna #a0522d. NO cool blues or tech grays.
- **Motion:** Scroll-triggered reveals: slide-up 20px + opacity fade. Parallax text at 0.5x speed. Easing: cubic-bezier(0.16, 1, 0.3, 1). Transitions 300-500ms.

### Trend 4: Tactile Puffy
**Tactile Puffy** (v1.0.0) — Playful 3D clay aesthetic, inflated shapes.

- **Typography:** Rounded sans-serif (Nunito, Quicksand, Comfortaa). Bubbly friendly letterforms. Medium-weight body, bold-to-black headings.
- **Materiality:** Soft 3D depth: multi-layer shadows, inner-shadow highlights. Buttons feel pressable (inset shadow on :active). Matte surfaces.
- **Composition:** Large border-radius (16-24px). Floating cards with generous shadow. Playful overlapping elements. Generous padding.
- **Color:** Pastel-saturated: lavender #c4b5fd, peach #fdba74, mint #86efac, sky #7dd3fc, soft-pink #fda4af. Backgrounds slightly tinted (not pure white).
- **Motion:** Spring physics: cubic-bezier(0.34, 1.56, 0.64, 1). Bounce on appear. Squish on press (scaleY:0.95). Wobble on hover. 200-400ms.

### Trend 5: OLED Dark Luxury
**OLED Dark Luxury** (v1.0.0) — True black, cinematic elegance, OKLCH accents.

- **Typography:** Geometric sans (Outfit, Sora, General Sans). Tight letter-spacing (-0.02em headings). Light font-weight body (300-400). Display: medium-to-bold.
- **Materiality:** True black backgrounds (#000 or oklch(0% 0 0)). Ultra-thin borders (1px rgba(255,255,255,0.06-0.1)). Extremely subtle grain. NO heavy shadows. Surfaces distinguished by border only.
- **Composition:** Cinematic wide sections with dramatic vertical spacing. Centered content blocks, max-width 800px. Minimal elements per section. Let the black space breathe.
- **Color:** Near-monochrome base (black + white text). Single saturated accent via OKLCH (emerald oklch(0.7 0.2 155), violet oklch(0.6 0.2 300), or amber oklch(0.8 0.15 80)). Accent used sparingly.
- **Motion:** Smooth opacity reveals (0→1 over 600ms). Clip-path wipe animations. Text character-by-character stagger (30ms). Easing: cubic-bezier(0.16, 1, 0.3, 1).

### Trend 6: Retro-Futurism
**Retro-Futurism** (v1.0.0) — Y2K nostalgia meets sci-fi chrome.

- **Typography:** Retro display (Unbounded, Space Grotesk, Archivo). Pixel/bitmap accents for labels. Mix of futuristic geometric + nostalgic rounded forms.
- **Materiality:** CRT scanline overlay (repeating-linear-gradient 2px). Chrome/metallic gradients. VHS noise artifacts. Glow effects via text-shadow with neon colors.
- **Composition:** Y2K card layouts: stacked panels with visible borders. Terminal/console-inspired sections.
- **Color:** Nostalgic neon: amber #f59e0b, teal #14b8a6, magenta #d946ef on dark navy #0f172a. Chrome silver #c0c0c0 for borders.
- **Motion:** Glitch effects (clip-path + translate jitter). Typing/typewriter animations. Flickering opacity (0.8→1→0.9). VHS tracking distortion on scroll.

---

## Section 2: Art Direction Packs (3)

Art Direction Packs are the enriched implementation layer — each pack includes: layout rules, navigation archetypes per platform, wow effects, surface recipes, motion grammar, copy tone, and reference tags.

---

### Art Pack: Glass Premium (v1.0.0)

**Liquid Glass Command Center** — OLED dark luxury meets frosted glass panels. The definitive premium glassmorphism implementation.

#### Core DNA
- **Composition:** Centered minimal — cinematic wide sections, dramatic vertical spacing
- **Typography:** Geometric sans (Outfit, Sora, General Sans). Tight letter-spacing (-0.02em headings). Light body (300-400).
- **Materiality:** True black backgrounds (#000). Ultra-thin borders (1px rgba(255,255,255,0.06-0.1)). Extremely subtle grain. Surfaces distinguished by border only.
- **Color:** Near-monochrome base (black + white text). Single saturated OKLCH accent — emerald oklch(0.7 0.2 155), violet oklch(0.6 0.2 300), or amber oklch(0.8 0.15 80). Accent used sparingly — links, CTAs, highlights only.
- **Motion:** Smooth opacity reveals (0→1 over 600ms). Clip-path wipe. Sidebar collapse width transition 250ms ease-in-out. Panel appear: scale(0.97)→scale(1) + opacity. Easing: cubic-bezier(0.16,1,0.3,1). No bounce.

#### Layout Rules
- `border-radius: 16px`
- `shadowStyle: 0 8px 32px rgba(0,0,0,0.4)`
- `borderStyle: 1px solid rgba(255,255,255,0.08)`
- `surfaceTexture: backdrop-filter: blur(20px); background: rgba(255,255,255,0.05)`
- `iconStyle: duotone`
- `buttonVariant: ghost`
- `motionIntensity: moderate`

#### Signature Motifs
- Frosted translucent control layer over content
- Concentric rounded geometry (radius cascade: 8→12→16→24)
- Specular highlight: `inset 0 1px rgba(255,255,255,0.15)`
- Adaptive sidebar that collapses to bottom tab on mobile
- Restrained blur: max 20px backdrop-filter, never background blur blobs

#### WOW Effects
- `backdrop-filter: blur(20px)` on panels
- Specular highlight via `inset_0_1px_rgba(255,255,255,0.1)`
- OKLCH accent glow: `shadow-[0_0_24px_-4px_oklch(...)]`
- Concentric rounded geometry (border-radius cascade)

#### Surface Recipes
- **Glass panel:** `backdrop-filter:blur(20px) + bg:rgba(255,255,255,0.05) + border:rgba(255,255,255,0.08)`
- **Elevated card:** `bg:rgba(255,255,255,0.03) + specular inset highlight at top edge`
- **Command bar:** `bg:rgba(0,0,0,0.6) + blur(24px) + border-bottom:rgba(255,255,255,0.06)`

#### Navigation Archetypes
| Platform | Navigation Model |
|---|---|
| **Mobile** | Bottom tab bar (glass-morphic, backdrop-blur) |
| **Tablet** | Adaptive sidebar (w-64, collapses to icon rail) |
| **Desktop** | Persistent sidebar (w-64) + horizontal top bar |

#### Platform Adaptations
- **Mobile:** Single-column, condensed card height, sticky bottom CTA or FAB, bottom sheet with glass surface. Allowed: hero, metric-card, command-bar, cta-banner, glass-panel. Forbidden: persistent-sidebar, multi-pane-layout.
- **Tablet:** 2-col grid equal-width cards, top-right CTA in header or inline card footer, right drawer (glass, blur). Allowed: hero, metric-card, glass-panel, data-table, command-bar.
- **Desktop:** Dense 3-4 col grid compact cards, top-right CTA in header, secondary in card footer, right-rail command panel. Allowed: dashboard-grid, metric-card, glass-panel, data-table, command-bar, detail-pane.

#### Copy Tone
Precise, technical authority. Active verbs. Metrics-first. Headline: noun + number or stat. CTA: imperative single word. Avoid filler adjectives.

#### Anti-Patterns
- NO warm earth tones
- NO thick borders
- NO serif fonts
- NO paper textures
- NO pure white backgrounds

#### Forbidden Treatments
- Floating blur blobs in background
- Diffuse AI-chrome gradients
- Warm earth tones
- Thick solid borders
- Serif fonts
- Paper textures

#### Reference Tags
| Tag | Use For | Weight |
|---|---|---|
| Apple Liquid Glass | Frosted panel treatment, specular highlights, blur depth | Primary |
| AlignUI | Dashboard layout, metric cards, data tables | Primary |
| Ant Design v6 | Component density, form layouts, navigation patterns | Secondary |

---

### Art Pack: Warm Editorial (v1.0.0)

**Literary Premium** — Magazine-premium warmth, craft feel, asymmetric editorial layouts.

#### Core DNA
- **Typography:** Expressive serif display (Playfair Display, Fraunces, Lora). Body: Plus Jakarta Sans or DM Sans. Oversized headings with tight line-height.
- **Materiality:** Paper/ink texture via subtle SVG noise (1-2% opacity). Warm shadows (rgba(139,90,43,0.1)). 1px hairline borders. Surface feels like premium print.
- **Composition:** Asymmetric CSS Grid, 2-col with one oversized. Generous whitespace. Content wrapped in bordered container with padding from viewport edges. Overlapping elements for depth.
- **Color:** Terracotta #c4683f, olive #6b7f3b, cream #faf5e4, charcoal #2d2d2d, burnt sienna #a0522d. NO cool blues or tech grays.
- **Motion:** Scroll-triggered reveals: slide-up 20px + opacity fade. Parallax text at 0.5x speed. Easing: cubic-bezier(0.16,1,0.3,1). Transitions 300-500ms. Subtle, elegant, never flashy.

#### Layout Rules
- `border-radius: 8px`
- `shadowStyle: 0 4px 20px rgba(139,90,43,0.12)`
- `borderStyle: 1px solid rgba(139,90,43,0.15)`
- `surfaceTexture: url("data:image/svg+xml,...noise...") at 1-2% opacity`
- `iconStyle: outlined`
- `buttonVariant: outlined`
- `motionIntensity: subtle`

#### Signature Motifs
- Asymmetrical masthead with oversized serif headline
- Numbered sections like book chapters (01, 02)
- Margin annotations as aside elements
- Framed content modules with 1px hairline borders
- Contrast between expressive serif display + sober sans body

#### WOW Effects
- Subtle SVG noise texture overlay at 1-2% opacity
- Warm rgba shadows (139,90,43,0.1)
- Magazine pull-quote with oversized serif
- 1px hairline rules as section dividers

#### Surface Recipes
- **Paper surface:** `bg-[#faf5e4]` with SVG noise at 1.5% opacity
- **Warm bordered card:** `border:1px solid rgba(139,90,43,0.15) rounded shadow-[0_4px_20px_rgba(139,90,43,0.12)]`
- **Pull-quote:** `border-l-4 border-[#c4683f] pl-6 italic font-serif`

#### Navigation Archetypes
| Platform | Navigation Model |
|---|---|
| **Mobile** | Bottom tab bar with text labels |
| **Tablet** | Sidebar table-of-contents navigation (w-56, collapsible) |
| **Desktop** | Horizontal editorial nav with category dropdowns |

#### Platform Adaptations
- **Mobile:** Single-column, generous vertical rhythm, sticky bottom bar or inline CTA, full-width modal sheets. Allowed: hero, article-card, pull-quote, cta-banner.
- **Tablet:** 2-col asymmetric grid 60/40 split, right sidebar sticky or inline after lead paragraph, slide-in drawer from left. Allowed: hero, article-card, pull-quote, aside-annotation, cta-banner.
- **Desktop:** 3-col editorial grid 50/25/25, CTA above-fold in hero + repeated at article end, right-rail for metadata + related links. Allowed: masthead, hero, article-card, pull-quote, aside-annotation, featured-grid, cta-banner.

#### Copy Tone
Confident editorial voice. Short declarative sentences. No tech jargon. Headline: 3-5 words max. Subhead: single sentence. CTA: verb-first action.

#### Forbidden Treatments
- Glassmorphism or frosted panels
- Neon accent colors
- Hard drop shadows
- Monospace or tech fonts
- Dark mode backgrounds
- Floating blur blobs

#### Reference Tags
| Tag | Use For | Weight |
|---|---|---|
| Untitled UI | Clean card layouts, whitespace rhythm, form patterns | Primary |
| AlignUI | Data display, metric cards, table styling | Secondary |
| Shopify Polaris | UX copy patterns, action-oriented CTAs | Secondary |

---

### Art Pack: Neo-Brutalist Light (v1.0.0)

**Raw Grid Manifesto** — Punk graphic design, hard borders, maximum contrast.

#### Core DNA
- **Typography:** Monospace display (Space Mono, JetBrains Mono) + chunky sans (Archivo Black, DM Sans Black). Oversized headings as graphic elements. Text used decoratively — rotate, overlap, uppercase. NEVER rounded/friendly fonts.
- **Materiality:** Thick solid borders (3-4px black). Hard drop-shadows (4-6px offset, 0 blur, #000). ZERO blur, ZERO gradients, ZERO glassmorphism. Raw exposed structure. Background: pure white or pure black only.
- **Composition:** Harsh grid with visible borders between cells (gap:0 + border on children). Broken alignment for emphasis. No rounded corners (border-radius: 0).
- **Color:** Black #000 + white #fff base. Accent via single neon — lime #a3e635 OR hot-pink #ec4899 OR yellow #facc15. NEVER gradients. NEVER more than 3 colors total.
- **Motion:** Abrupt transitions: step-start or 50ms. Scale jumps on hover (1.0→1.05 instant). NO spring physics. Elements snap, not glide. Hover: shadow shrinks + element translates (pressed effect).

#### Layout Rules
- `border-radius: 0px`
- `shadowStyle: 4px 4px 0px #000000`
- `borderStyle: 3px solid #000000`
- `surfaceTexture: none`
- `iconStyle: filled`
- `buttonVariant: flat`
- `motionIntensity: none`

#### Signature Motifs
- Thick 3-4px solid black borders on all containers
- Hard offset box-shadow (4px 4px 0 #000) — no blur
- Oversized uppercase monospace headline as graphic element
- Visible grid gap filled with border color (gap:0 + border on children)
- Intentionally misaligned element for emphasis

#### WOW Effects
- 4px offset hard drop-shadow on every card
- Visible grid borders between cells
- Scale jump on hover (1.0→1.05 instant, step-start)
- Alternating bg-lime-400/bg-white for grid cells

#### Surface Recipes
- **Card:** `bg-white border-3 border-black shadow-[4px_4px_0_#000]`
- **Accent block:** `bg-lime-400 border-3 border-black, text-black uppercase`
- **Divider:** `border-t-4 border-black, no margin collapse`

#### Navigation Archetypes
| Platform | Navigation Model |
|---|---|
| **Mobile** | Top bar with thick border-bottom, hamburger opens full-screen overlay |
| **Tablet** | Horizontal nav bar with thick borders, no dropdowns |
| **Desktop** | Sticky horizontal bar: border-bottom 3px solid #000, text-only links |

#### Platform Adaptations
- **Mobile:** Top bar + full-screen menu overlay (bg-black, white links), single-column full-width bordered cards, full-width sticky button at bottom. Allowed: hero, bordered-card, cta-button, section-divider.
- **Tablet:** Top horizontal bar border-bottom 3px solid #000, 2-col equal borders, inline after hero, full-width bottom bar. Allowed: hero, bordered-card, grid-section, cta-button.
- **Desktop:** Sticky horizontal nav 3px border-bottom text-only, 3-4 col harsh grid gap:0+borders, bold isolated button with hard shadow. Allowed: masthead, hero, grid-section, bordered-card, cta-button, accent-block.

#### Copy Tone
Blunt, direct, zero fluff. All-caps headlines acceptable. Short punchy sentences. CTA: single imperative word (BUY / GET / START). Functional over charming.

#### Forbidden Treatments
- Any border-radius (stays at 0px)
- Gradients of any kind
- Glassmorphism or blur
- Soft drop shadows
- More than 3 colors in palette
- Serif or rounded fonts
- Smooth easing or spring physics

#### Reference Tags
| Tag | Use For | Weight |
|---|---|---|
| Figma Community Brutalist kits | Grid structure, border patterns, card templates | Primary |
| Gumroad 2022 redesign | Bold typography as hero, high-contrast CTA | Primary |
| Linear (early) | Tight grid density, functional copy, sparse color | Secondary |

---

## Telegram Liquid Glass (Mobile Glassmorphism Reference)

Telegram's 2025 Android redesign is a reference implementation of mobile glassmorphism. Use these patterns for mobile-first glass UI.

### Telegram Design Characteristics
- **Blur effect:** `backdrop-filter: blur(16px)` on navigation and floating elements
- **Background:** Translucent with `rgba(255,255,255,0.08-0.12)` on dark, `rgba(0,0,0,0.4)` on light
- **Borders:** Ultra-thin `border: 1px solid rgba(255,255,255,0.08)` on dark, `rgba(0,0,0,0.06)` on light
- **Border-radius:** 16-24px on cards, 12px on buttons, full-round on avatars
- **Floating bottom nav:** `position: fixed; bottom: 8px; left: 8px; right: 8px; border-radius: 16px; backdrop-blur(16px)`
- **Shadows:** Soft `box-shadow: 0 4px 24px rgba(0,0,0,0.15)` with no blur gradient
- **Typography:** System fonts (SF Pro on iOS, Roboto on Android), clean and minimal
- **Icons:** Outlined style, 24px default size, subtle gray when inactive, accent when active
- **Motion:** 200-300ms ease transitions, scale(0.98) on press, subtle fade on state change

### Telegram-Style Mobile Glass Implementation

```
/* Floating bottom nav (Telegram style) */
.floating-nav {
  position: fixed;
  bottom: 8px;
  left: 8px;
  right: 8px;
  border-radius: 16px;
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 4px 24px rgba(0,0,0,0.15);
  padding: 8px 16px;
  display: flex;
  justify-content: space-around;
  z-index: 100;
}

/* Glass card (Telegram style) */
.glass-card {
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  padding: 16px;
}

/* Active nav item */
.nav-item.active {
  color: #3390ec; /* Telegram blue */
}
.nav-item.inactive {
  color: rgba(255,255,255,0.5);
}
```

### Mobile Glassmorphism Variants

#### 1. Telegram Dark (default for dark backgrounds)
- Background: `rgba(30, 30, 30, 0.7)` + blur(16px)
- Border: `rgba(255,255,255,0.06)`
- Active accent: #3390ec (Telegram blue)

#### 2. Telegram Light (for light backgrounds)
- Background: `rgba(255,255,255,0.72)` + blur(16px)
- Border: `rgba(0,0,0,0.06)`
- Active accent: #0077e6

#### 3. Glass Premium (for premium/dashboard apps)
- Background: `rgba(255,255,255,0.05)` + blur(20px)
- Border: `rgba(255,255,255,0.08)` + specular inset highlight
- Active accent: OKLCH emerald/violet/amber
- Shadow: `0 8px 32px rgba(0,0,0,0.4)`

#### 4. Obsidian Lime (for gaming/developer apps)
- Background: `rgba(0,0,0,0.8)` + blur(24px)
- Border: `rgba(163,230,53,0.20)` (lime glow)
- Neon ambient glow halos

#### 5. Slate Atmospheric (for calm/meditation apps)
- Background: `rgba(15,23,42,0.6)` + blur(24px)
- Border: `rgba(148,163,184,0.15)`
- Sky-blue accent: #38bdf8
- Wide padding for spacious calm feel

### iOS 26 Liquid Glass (Apple Reference)
Apple's Liquid Glass introduces:
- **3D depth:** Multiple layers with different blur amounts creating parallax depth
- **Specular highlights:** `inset 0 1px rgba(255,255,255,0.2)` on top edge
- **Reflective surfaces:** Subtle gradient overlays suggesting glass refraction
- **Rounded geometry:** Heavy use of 20-24px border-radius, concentric radius cascade
- **Motion:** Spring physics, morphing transitions, depth-aware animations
- **Color:** Vibrant backgrounds visible through glass, OKLCH color space for vividness

**For iOS 26 style:**
- Layer at least 2 glass levels with different blur intensities (e.g., 20px and 40px)
- Add `::before` pseudo-element with diagonal gradient for specular reflection
- Use `backdrop-filter: blur() saturate(1.5)` for richer glass appearance
- Implement scale and blur transitions on hover/press states
