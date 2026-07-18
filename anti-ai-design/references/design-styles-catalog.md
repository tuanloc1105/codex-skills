# Design Styles Catalog

36 design styles across 11 categories. Each style is a complete DesignStyle object defining: typography, color palette, layout, materiality, motion, icons, signature motifs, hero archetypes, wow effects, CSS patterns, anti-patterns, and forbidden treatments.

---

## Category: brutalist (4 styles)

### 1. Neo-Brutalist Raw
- **ID:** `neo-brutalist-raw`
- **Vibe:** Punk graphic — hard grid, zero radius, thick black borders, neon accent
- **Typography:** Monospace display (Space Mono, JetBrains Mono) + chunky sans (Archivo Black, DM Sans Black). Oversized headings as graphic elements. Text used decoratively — rotate, overlap, uppercase.
- **Colors:** Maximum contrast: black #000 + white #fff. Accent via single neon hue — lime #a3e635 OR hot-pink #ec4899 OR electric-yellow #facc15.
- **Layout:** Harsh grid with visible borders (gap:0 + border on children). No rounded corners (border-radius: 0). Visible grid lines as design element.
- **Motion:** Abrupt transitions: step-start or 50ms duration. Scale jumps on hover (1.0→1.05 instant). No spring physics.
- **Icons:** Filled, Tabler
- **Surfaces:** `border-4 border-black shadow-[4px_4px_0_#000]`, `bg-lime-400 border-3 border-black`
- **Anti-patterns:** Rounded corners, gradients, glassmorphism, soft shadows, serif fonts
- **Forbidden:** border-radius, gradients of any kind, more than 3 colors total
- **Products:** Manufacturing, Developer-Tools, Infrastructure
- **CSS Patterns:**
  - `border-4 border-black shadow-[4px_4px_0_#000]`
  - `bg-white text-black rounded-none`
  - `uppercase font-black tracking-wider`
  - `grid grid-cols-3 gap-0 border-4 border-black`
  - `bg-lime-400 hover:bg-lime-300 active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all`

### 2. Kinetic Orange
- **ID:** `kinetic-orange`
- **Vibe:** High-energy brutalist with burnt orange as explosive accent
- **Typography:** Archivo Black (headings, weight 400 only), DM Sans (body)
- **Colors:** Burnt orange #ea580c, black #000000, cream #fef3c7
- **Layout:** Dense grid, border-radius: 0, hard 4px shadow offset
- **Motion:** Snap interactions: hover shifts 2px up, shadow shrinks. Click collapses shadow to zero.
- **Icons:** Sharp, Material Symbols
- **Surfaces:** `bg-amber-50 border-4 border-black shadow-[4px_4px_0_#000]`, `bg-orange-600 border-4 border-black text-white`
- **Anti-patterns:** Rounded corners, gradients, soft shadows, pastel palettes
- **Products:** Events, Sports, Media
- **CSS Patterns:**
  - `bg-amber-50 border-4 border-black shadow-[4px_4px_0_#000]`
  - `bg-orange-600 text-white font-black uppercase tracking-widest`
  - `text-stone-900 text-5xl font-black leading-none tracking-tight uppercase`
  - `hover:shadow-[2px_2px_0_#000] hover:-translate-y-px active:shadow-none active:translate-y-0 transition-none`

### 3. Yellow Neo-Brutalist
- **ID:** `yellow-neo-brutalist`
- **Vibe:** Electric yellow on black — maximum contrast, hard shadows
- **Typography:** JetBrains Mono bold (headings, uppercase), Inter (body)
- **Colors:** Electric yellow #facc15, pure black #000000
- **Layout:** Dense grid, border-radius: 0, hard yellow offset shadows (4px 4px 0 #facc15)
- **Motion:** Snap state changes — no easing. Yellow shadow expands to 6px on hover. Collapse to zero on click.
- **Icons:** Filled, Tabler
- **Surfaces:** `bg-black border-2 border-yellow-400 shadow-[4px_4px_0_#facc15]`, `bg-yellow-400 text-black font-black uppercase`
- **Anti-patterns:** Warm/pastel colors, rounded corners, serif fonts, smooth transitions
- **Products:** Developer-Tools, Startup, Creative-Agency
- **CSS Patterns:**
  - `bg-black text-yellow-400 border-2 border-yellow-400 shadow-[4px_4px_0_#facc15]`
  - `font-mono font-bold uppercase tracking-widest text-yellow-300`
  - `hover:shadow-[6px_6px_0_#facc15] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-none`

### 4. Season 04 Fashion
- **ID:** `season-04-fashion`
- **Vibe:** High-fashion brutalism — editorial typography meets raw structure
- **Typography:** Bebas Neue (headlines at 12vw+), Outfit (body)
- **Colors:** Charcoal #1a1a1a, neutral #e5e5e5, pink accent #ec4899, off-white #fafafa
- **Layout:** Asymmetric-scroll, border-radius: 0, intentional misalignment
- **Motion:** Clip-path text reveals on scroll, staggered 80ms, hover scale(1.01)
- **Icons:** Outlined, Heroicons
- **Surfaces:** `bg-white border border-neutral-200`, `border-l-2 border-l-pink-500`
- **Anti-patterns:** Symmetrical grids, rounded shapes, heavy drop shadows
- **Products:** Fashion, Portfolio, Creative-Agency
- **CSS Patterns:**
  - `text-[15vw] font-normal leading-none tracking-tight text-neutral-900 uppercase`
  - `border-b border-neutral-300 pb-2 text-xs uppercase tracking-[0.3em] text-neutral-500`
  - `bg-pink-500 h-px w-0 animate-[expand_0.4s_ease-out_0.3s_forwards]`

---

## Category: cinematic (2 styles)

### 5. B&W Motion Studio
- **ID:** `bw-motion-studio`
- **Vibe:** Black-and-white motion studio — dramatic contrast, cinematic wipes
- **Typography:** Bebas Neue (display, uppercase only), Outfit (body, 300-400)
- **Colors:** White #ffffff, gray #737373, black #000000
- **Layout:** Full-bleed hero, border-radius: 0, spacious density
- **Motion:** Horizontal wipe reveals via clip-path, text stagger 50ms per word, easing cubic-bezier(0.77,0,0.175,1), 800ms
- **Icons:** Outlined, Lucide
- **Surfaces:** Pure black #000, white/10 border
- **Anti-patterns:** Any color accent, rounded corners, shadows, busy grids
- **Products:** Film, Photography, Architecture, Portfolio
- **CSS Patterns:**
  - `bg-black text-white min-h-screen flex items-center`
  - `text-8xl font-bold uppercase tracking-tighter`
  - `border-t border-white/10 pt-8 mt-16`
  - `w-full h-px bg-white/20 my-12`

### 6. Cinematic Noir Gallery
- **ID:** `cinematic-noir-gallery`
- **Vibe:** Dark gallery with theatrical lighting — museum-grade presentation
- **Typography:** Cormorant Garamond (display, 300-400, italic for pull quotes), Lato (body, 300)
- **Colors:** Near-black #0a0a0a, amber #fbbf24, cream #fef3c7
- **Layout:** Centered-cinematic, spotlight radial gradients, border-radius: 4px
- **Motion:** Fade-in with upward drift 20px over 700ms, spotlight intensity pulses on hover
- **Icons:** Outlined, Heroicons
- **Surfaces:** `bg-[#0a0a0a]` with radial amber glow, vignette framing
- **Anti-patterns:** Bright colors, busy grids, sans-serif display, hard drop shadows
- **Products:** Art, Museum, Gallery, Luxury
- **CSS Patterns:**
  - `bg-[#0a0a0a] text-stone-100 min-h-screen`
  - `max-w-2xl mx-auto px-8 py-24 text-center`
  - `font-serif text-5xl leading-tight tracking-tight text-amber-100`
  - `border border-amber-200/10 rounded-sm overflow-hidden`
  - `text-amber-400 text-xs uppercase tracking-[0.3em] font-light`

---

## Category: commerce (1 style)

### 7. Bold Commerce
- **ID:** `bold-commerce`
- **Vibe:** Conversion-focused e-commerce — split hero scroll, snappy motion, dominant CTAs
- **Typography:** (From recipe: Space Grotesk for headings, system sans for body)
- **Colors:** High contrast — black/white with emerald or bold accent
- **Layout:** Split-hero-scroll, sticky price+CTA alongside scrolling imagery
- **Motion:** Spring snappy, scale(0.95) on click, fast transitions
- **Icons:** Filled, Material Symbols
- **Surfaces:** Bold card surfaces with prominent CTAs
- **Anti-patterns:** Heavy editorial whitespace, centered minimal layout, no CTA above fold
- **Products:** E-commerce
- **CSS Patterns:**
  - `grid grid-cols-1 lg:grid-cols-2 min-h-screen`
  - `sticky top-0 h-screen flex flex-col justify-center p-12`
  - `text-5xl font-extrabold tracking-tight text-gray-900`
  - `w-full py-4 bg-gray-900 text-white font-bold rounded-xl hover:bg-gray-800 active:scale-95 transition-all`

---

## Category: dark-luxury (5 styles)

### 8. Noir Cinema
- **ID:** `noir-cinema`
- **Vibe:** Dramatic dark cinematics — deep blacks, clip-path reveals, bold display typography
- **Typography:** Syne (headings, 700-900), Inter (body)
- **Colors:** Pure black #000000, white #ffffff, violet accent
- **Layout:** Centered-cinematic, border-radius: 0, spacious density
- **Motion:** Clip-path reveals left-to-right 600ms ease-out, stagger 100ms, no hover on text
- **Icons:** Filled, Material Symbols
- **Surfaces:** `bg-black border border-white/10`
- **Anti-patterns:** Light backgrounds, rounded pills, warm palette, busy grids
- **Products:** Creative, Luxury, Film, Portfolio
- **CSS Patterns:**
  - `bg-black text-white min-h-screen flex items-center justify-center`
  - `text-7xl font-black uppercase tracking-tighter leading-none`
  - `opacity-60 text-xs tracking-[0.3em] uppercase text-gray-400`
  - `w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent my-12`

### 9. Dark Elite Frosted
- **ID:** `dark-elite-frosted`
- **Vibe:** Elite dark frosted glass panels over OLED black — specular highlights, premium fintech feel
- **Typography:** General Sans (headings, semibold), Inter (body, tabular-nums for data)
- **Colors:** OLED black #020617, cyan accent #22d3ee, surface rgba(255,255,255,0.06)
- **Layout:** Bento-grid, border-radius: 16px, compact density
- **Motion:** Scale from 0.96 to 1.0 in 200ms ease-out, stagger 40ms, cyan border on hover
- **Icons:** Outlined, Lucide
- **Surfaces:** `bg-white/[0.06] border border-white/[0.08] rounded-2xl backdrop-blur-xl`, specular inset highlight `inset_0_1px_rgba(255,255,255,0.08)`
- **Anti-patterns:** Light/warm backgrounds, heavy accent colors, bold typography above 700
- **Products:** Fintech, Dashboard, Crypto
- **CSS Patterns:**
  - `bg-[#020617] text-slate-200 min-h-screen`
  - `bg-white/[0.06] border border-white/[0.08] rounded-2xl backdrop-blur-xl p-5`
  - `text-3xl font-semibold tabular-nums text-cyan-400`
  - `border border-cyan-500/20 shadow-[0_0_24px_-4px_rgba(34,211,238,0.3)]`
  - `grid grid-cols-4 gap-3 p-4`

### 10. Gold on Black AI
- **ID:** `gold-on-black-ai`
- **Vibe:** Regal gold accents on true black — premium AI/tech luxury with restrained metallic highlights
- **Typography:** Cormorant Garamond (headings, italic for elegance), Sora (body, 300-400)
- **Colors:** True black #09090b, gold #fbbf24, amber #f59e0b, surface #111113
- **Layout:** Centered-cinematic, border-radius: 8px, spacious density
- **Motion:** Slow deliberate reveals: clip-path 800ms cubic-bezier(0.25, 0.46, 0.45, 0.94), gold underline grows from center 300ms, stagger 150ms
- **Icons:** Two-tone, Material Symbols
- **Surfaces:** Near-black #111113, thin 1px gold/20 borders, metallic gold halo on CTA
- **Anti-patterns:** Gray backgrounds, generic tech blues, Inter headings, excessive glow
- **Products:** AI, Tech, Luxury
- **CSS Patterns:**
  - `bg-[#09090b] text-[#fafaf9] min-h-screen`
  - `shadow-[0_0_48px_-8px_rgba(251,191,36,0.15)]`
  - `border border-white/[0.06] rounded-lg p-6`
  - `font-serif text-5xl font-bold italic`

### 11. Red Noir
- **ID:** `red-noir`
- **Vibe:** Crimson-on-black cinema noir — seductive dark contrast with blood-red accent
- **Typography:** Libre Bodoni (display), Work Sans (body, 300-400)
- **Colors:** Velvet black #0a0a0a, crimson #dc2626, bright red #ef4444, deep red #4a0404
- **Layout:** Full-bleed hero, border-radius: 4px, balanced density
- **Motion:** Dramatic slow reveals: clip-path from bottom 700ms, red accent sweeps 400ms, hover text turns crimson 200ms
- **Icons:** Filled, Lucide
- **Surfaces:** `bg-[#0f0f0f] border border-red-800/30`, red ambient glow `shadow-[0_20px_60px_-10px_rgba(220,38,38,0.2)]`
- **Anti-patterns:** Light backgrounds, competing accent colors, playful rounded shapes
- **Products:** Entertainment, Nightlife, Luxury
- **CSS Patterns:**
  - `bg-[#0a0a0a] text-zinc-50 min-h-screen`
  - `text-6xl font-bold italic tracking-tight text-white leading-none`
  - `border border-red-800/30 rounded bg-zinc-950/80 p-6 hover:border-red-500/50 transition-colors`
  - `text-red-500 font-semibold`
  - `shadow-[0_20px_60px_-10px_rgba(220,38,38,0.2)]`

### 12. Immersive Cinematic
- **ID:** `immersive-cinematic`
- **Vibe:** Full-viewport cinematic experience with 21:9 section aspect ratios
- **Typography:** Unbounded (headings, 400-900), DM Sans (body, 300-400)
- **Colors:** Near-black #0c0c0c, violet accent #7c3aed, surface #161616
- **Layout:** Full-bleed hero, 21:9 aspect ratios, border-radius: 0, spacious density
- **Motion:** Cinematic entrances: clip-path 900ms cubic-bezier(0.76, 0, 0.24, 1), parallax 0.4x scroll, stagger 200ms
- **Icons:** Sharp, Material Symbols
- **Surfaces:** `aspect-[21/9] w-full overflow-hidden bg-[#0c0c0c]`
- **Anti-patterns:** Light backgrounds, busy grids, rounded elements, small-detail card layouts
- **Products:** Film, Portfolio, Creative-Agency
- **CSS Patterns:**
  - `bg-[#0c0c0c] text-neutral-100 min-h-screen`
  - `aspect-[21/9] w-full overflow-hidden relative bg-[#161616]`
  - `text-[clamp(3rem,8vw,8rem)] font-black leading-none tracking-tight text-neutral-50`
  - `text-violet-400 font-medium text-sm tracking-[0.2em] uppercase`

---

## Category: editorial (6 styles)

### 13. Editorial Luxury
- **ID:** `editorial-luxury`
- **Vibe:** Magazine-premium full-bleed layouts with expressive serif display and terracotta warmth on cream
- **Typography:** Playfair Display (headings, 700-900, italic accent), Plus Jakarta Sans (body, 300-600)
- **Colors:** Cream #faf5e4, charcoal #2d2d2d, terracotta #c4683f, olive #6b7f3b
- **Layout:** Full-bleed hero, border-radius: 8px, spacious density
- **Motion:** Clip-reveal 400ms, parallax text 0.5x, easing cubic-bezier(0.16,1,0.3,1), hero image clip-path curtain drop 700ms
- **Icons:** Rounded, Lucide
- **Surfaces:** `bg-[#faf5e4]` with SVG noise 1.5%, warm shadow `rgba(139,90,43,0.12)`, terracotta hairline borders
- **Anti-patterns:** Card grids as primary, sans-serif headlines, cool-blue palette, nav inside hero
- **Products:** Luxury, Creative, Fashion
- **CSS Patterns:**
  - `font-serif text-6xl leading-none tracking-tight`
  - `border border-[rgba(139,90,43,0.15)] rounded-lg shadow-[0_4px_20px_rgba(139,90,43,0.12)]`
  - `border-l-4 border-[#c4683f] pl-6 italic font-serif text-2xl`
  - `w-full h-screen relative overflow-hidden`

### 14. Earthy Organic
- **ID:** `earthy-organic`
- **Vibe:** Earth-toned editorial with organic variable-weight typography — terracotta and olive on cream
- **Typography:** Fraunces (headings, 700-900, optical-size large), Source Sans 3 (body, 300-400)
- **Colors:** Warm parchment #f5efe6, terracotta #8b6f4e, olive primary #6b4f3f, surface #ede4d8
- **Layout:** Asymmetric-editorial, border-radius: 12px, spacious density
- **Motion:** Gentle fade-up 28px over 420ms, ease-in-out, stagger 100ms, organic transitions
- **Icons:** Outlined, Tabler
- **Surfaces:** `bg-[#ede4d8] rounded-xl p-8`, warm bordered modules `bg-[#f5efe6] border border-[rgba(107,79,63,0.2)]`
- **Anti-patterns:** Cool gray/blue backgrounds, sharp geometric sans, neon accents, dense grids
- **Products:** Wellness, Food, Sustainability
- **CSS Patterns:**
  - `bg-[#f5efe6] min-h-screen font-sans`
  - `max-w-3xl mx-auto px-8 py-20 space-y-16`
  - `font-serif text-5xl font-bold text-[#3d3028] leading-tight`
  - `text-[#8b6f4e] text-sm uppercase tracking-widest font-medium`

### 15. Midnight Editorial
- **ID:** `midnight-editorial`
- **Vibe:** Dark editorial with ivory text on deep navy — cinematic magazine layouts meet dark-mode elegance
- **Typography:** Lora (headings, 600-700, italic for drama), DM Sans (body, 300-500)
- **Colors:** Deep navy #0f1419, ivory #e8e0d0, gold accent #c9a96e, surface #1a2030
- **Layout:** Full-bleed hero, border-radius: 4px, balanced density
- **Motion:** Clip-path from bottom 600ms, crossfade 400ms, no spring — cinematic gravity
- **Icons:** Outlined, Lucide
- **Surfaces:** `bg-[#1a2030] border border-[rgba(232,224,208,0.1)]`, gold hairline rule `border-[rgba(201,169,110,0.3)]`
- **Anti-patterns:** Light backgrounds, bright saturated colors, rounded-xl, bouncy motion
- **Products:** Media, Publishing, Portfolio
- **CSS Patterns:**
  - `bg-[#0f1419] text-[#e8e0d0] min-h-screen`
  - `font-serif text-5xl leading-tight italic text-[#e8e0d0]`
  - `bg-[#1a2030] border border-[rgba(232,224,208,0.08)] rounded p-6`
  - `text-[#c9a96e] text-xs uppercase tracking-widest font-medium`

### 16. Organic Serif
- **ID:** `organic-serif`
- **Vibe:** Literary and contemplative — Crimson Pro headings, muted taupe surfaces, reading-room atmosphere
- **Typography:** Crimson Pro (headings, 600-700, italic for sub-heads), Nunito Sans (body, 400, line-height 1.75)
- **Colors:** Aged paper #faf7f2, umber #4a4238, taupe accent #9b7e5e, surface #f0ebe2
- **Layout:** Split-hero, border-radius: 8px, spacious density, max-width 72ch for body
- **Motion:** Soft spring (stiffness 100, damping 20), fade-up 20px, stagger 80ms, reading progress indicator
- **Icons:** Rounded, Phosphor
- **Surfaces:** `bg-[#f0ebe2] rounded-lg p-8 border border-[rgba(74,66,56,0.12)]`, reading column `bg-[#faf7f2] p-10 max-w-[72ch]`
- **Anti-patterns:** Bright/saturated accents, sans-serif headlines, dense grids, dark backgrounds
- **Products:** Publishing, Education, Culture
- **CSS Patterns:**
  - `bg-[#faf7f2] min-h-screen text-[#3d362e]`
  - `max-w-[72ch] mx-auto px-8 py-16 space-y-10`
  - `font-serif text-5xl font-semibold text-[#4a4238] leading-snug`
  - `border-l-4 border-[#9b7e5e] pl-6 italic text-xl text-[#7a6a57]`

### 17. Forest Green Grid
- **ID:** `forest-green-grid`
- **Vibe:** Deep forest greens and structured editorial grid — nature-informed luxury with Swiss precision
- **Typography:** Libre Baskerville (headings, 700), Work Sans (body, 300-600)
- **Colors:** Forest #1b4332, sage #40916c, mint accent #52b788, mint surface #dcfce7
- **Layout:** 12-col-grid, border-radius: 4px, compact density
- **Motion:** Fade-up 16px over 280ms, ease-out, stagger 50ms, no bounce
- **Icons:** Outlined, Heroicons
- **Surfaces:** `bg-[#dcfce7] rounded border border-[rgba(27,67,50,0.12)]`, forest feature column `border-l-4 border-[#1b4332]`
- **Anti-patterns:** Warm earth tones, asymmetric overlapping, rounded corners beyond 4px, dark backgrounds
- **Products:** Sustainability, Finance, Real-Estate
- **CSS Patterns:**
  - `grid grid-cols-12 gap-x-4 max-w-screen-xl mx-auto px-8`
  - `col-span-8 border-l-4 border-[#1b4332] pl-6`
  - `bg-[#dcfce7] rounded border border-[rgba(27,67,50,0.12)] p-6`
  - `font-serif text-4xl font-bold text-[#1b4332] leading-tight`

### 18. Matte Earth Toned
- **ID:** `matte-earth-toned`
- **Vibe:** Muted earthy palette with matte surfaces — warm sophistication without gloss
- **Typography:** DM Serif Display (headings, one weight, large only), Karla (body, 300-600)
- **Colors:** Umber #5c4f3d, linen #f3ede4, dark gold accent #b8860b, surface #e8ddd0
- **Layout:** Asymmetric-editorial, border-radius: 16px, balanced density
- **Motion:** Soft spring (stiffness 80, damping 18), translate-y 24px→0, stagger 90ms, hover scale 1.01
- **Icons:** Rounded, Tabler
- **Surfaces:** `bg-[#e8ddd0] rounded-2xl p-8 border border-[rgba(92,79,61,0.15)]`
- **Anti-patterns:** High-gloss surfaces, cool gray neutrals, sharp corners, bright accents
- **Products:** Lifestyle, Home, Craft
- **CSS Patterns:**
  - `bg-[#f3ede4] min-h-screen text-[#3d3425]`
  - `max-w-5xl mx-auto px-8 py-16`
  - `bg-[#e8ddd0] rounded-2xl p-8 border border-[rgba(92,79,61,0.15)]`
  - `font-serif text-5xl text-[#5c4f3d] leading-tight`
  - `text-[#b8860b] text-xs uppercase tracking-widest font-semibold`

---

## Category: glassmorphism (3 styles)

### 19. Glass Aurora
- **ID:** `glass-aurora`
- **Vibe:** Ethereal premium glassmorphism — layered frosted panels over aurora gradient background
- **Typography:** Sora (headings), Inter (body)
- **Colors:** Aurora background: violet-950 → indigo-900 → sky-900, surface rgba(255,255,255,0.10), violet accent #a78bfa
- **Layout:** Centered-floating, border-radius: 16px, balanced density
- **Motion:** Scale-in from 0.95, blobs drift with slow CSS translate, hover lift scale(1.02)
- **Icons:** Rounded, Phosphor
- **Surfaces:** `bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl`, specular inset `inset_0_1px_rgba(255,255,255,0.2)`
- **Anti-patterns:** White/light backgrounds (kills depth), no blur, warm earth tones, harsh borders
- **Products:** Premium-SaaS, Music, Social
- **CSS Patterns:**
  - `relative overflow-hidden bg-gradient-to-br from-violet-950 via-indigo-900 to-sky-900 min-h-screen`
  - `absolute w-96 h-96 rounded-full blur-3xl opacity-40 pointer-events-none`
  - `bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8`
  - `shadow-[0_8px_32px_rgba(0,0,0,0.4),inset_0_1px_rgba(255,255,255,0.2)]`

### 20. Obsidian Lime
- **ID:** `obsidian-lime`
- **Vibe:** Dark obsidian glass with electric lime accents — neon glow through frosted dark panels
- **Typography:** Space Grotesk (headings, tight tracking), Inter (body)
- **Colors:** Pure black #0c0a09, lime accent #a3e635, surface rgba(255,255,255,0.05)
- **Layout:** Bento-grid, border-radius: 20px, compact density
- **Motion:** Sharp scale-in on load, lime glow pulses on hover, active compress scale(0.98)
- **Icons:** Outlined, Lucide
- **Surfaces:** `bg-black/80 backdrop-blur-lg border border-lime-500/20 rounded-[20px]`, neon glow `shadow-[0_0_24px_-4px_rgba(132,204,22,0.40)]`
- **Anti-patterns:** Light backgrounds, pastel colors, serif fonts, centered single-column
- **Products:** Gaming, Developer-Tools, Crypto
- **CSS Patterns:**
  - `bg-stone-950 min-h-screen text-stone-200`
  - `grid grid-cols-3 gap-3 p-4`
  - `bg-black/80 backdrop-blur-lg border border-lime-500/20 rounded-[20px] p-5`
  - `text-lime-400 font-bold tabular-nums text-2xl`
  - `shadow-[0_0_24px_-4px_rgba(132,204,22,0.40),inset_0_1px_rgba(255,255,255,0.06)]`

### 21. Slate Atmospheric
- **ID:** `slate-atmospheric`
- **Vibe:** Soft slate-toned glassmorphism with atmospheric depth — muted blue-gray panels on misty gradient
- **Typography:** Plus Jakarta Sans (headings, medium weight), Inter (body)
- **Colors:** Deep slate #0f172a, sky accent #38bdf8, surface rgba(148,163,184,0.08), mist rgba(15,23,42,0.60)
- **Layout:** Floating-cards, border-radius: 24px, spacious density
- **Motion:** Fade-up with stagger, hover gently lifts translateY(-2px), calm throughout
- **Icons:** Outlined, Heroicons
- **Surfaces:** `bg-slate-900/60 backdrop-blur-2xl border border-slate-400/15 rounded-[24px]`, misty gradient `bg-gradient-to-br from-slate-900 via-sky-950 to-slate-900`
- **Anti-patterns:** Neon accents (too aggressive), dense grids (spaciousness is signature), warm backgrounds
- **Products:** Weather, Meditation, Analytics
- **CSS Patterns:**
  - `bg-gradient-to-br from-slate-900 via-sky-950/50 to-slate-900 min-h-screen p-8`
  - `flex flex-wrap gap-6 justify-center`
  - `bg-slate-800/60 backdrop-blur-2xl border border-slate-400/15 rounded-[24px] p-8`
  - `text-sky-400 font-semibold text-lg`
  - `shadow-[0_4px_40px_rgba(0,0,0,0.35),inset_0_1px_rgba(148,163,184,0.12)]`

---

## Category: industrial (3 styles)

### 22. Refined Industrial
- **ID:** `refined-industrial`
- **Vibe:** Refined industrial with concrete textures and copper accents — warehouse-loft sophistication
- **Typography:** Barlow Condensed (oversized display headings), Source Sans 3 (body)
- **Colors:** Stone #f5f5f4, copper #d97706, warm black #1c1917, concrete #e7e5e4
- **Layout:** Split-hero, border-radius: 4px, balanced density
- **Motion:** Restrained fade-up, hover shifts copper accent shadow slightly right, deliberate
- **Icons:** Outlined, Tabler
- **Surfaces:** `bg-stone-100 border border-stone-300 rounded-[4px]`, copper accent `border-l-4 border-amber-600`
- **Anti-patterns:** Pure white background, rounded corners beyond 6px, bright neon, dark backgrounds
- **Products:** Architecture, Real-Estate, Construction
- **CSS Patterns:**
  - `bg-stone-100 text-stone-900 min-h-screen`
  - `grid grid-cols-1 lg:grid-cols-2 gap-0 min-h-screen`
  - `bg-stone-200 border border-stone-300 rounded-[4px] p-6`
  - `shadow-[0_2px_8px_rgba(41,37,36,0.12)] hover:shadow-[0_4px_16px_rgba(41,37,36,0.18)]`

### 23. Industrial Disruptor
- **ID:** `industrial-disruptor`
- **Vibe:** Raw industrial with exposed structure and monospace details — factory-floor meets digital precision
- **Typography:** IBM Plex Mono (headings and labels), IBM Plex Sans (body)
- **Colors:** Near-black #18181b, orange #f97316, zinc surface #27272a, grid-line #52525b
- **Layout:** Dense-grid, border-radius: 2px, compact density
- **Motion:** Snappy 200ms, hover adds orange offset shadow, click hard scale(0.97)
- **Icons:** Sharp, Material Symbols
- **Surfaces:** `bg-zinc-900 border border-zinc-700 rounded-[2px]`, orange glow `rgba(249,115,22,0.30)`
- **Anti-patterns:** Rounded corners beyond 4px, pastel colors, decorative gradients, soft shadows
- **Products:** Manufacturing, Developer-Tools, Infrastructure
- **CSS Patterns:**
  - `bg-zinc-950 text-zinc-300 font-mono min-h-screen`
  - `grid grid-cols-4 gap-[2px] bg-zinc-800`
  - `bg-zinc-900 border border-zinc-700 p-4 rounded-[2px]`
  - `text-orange-400 font-bold uppercase tracking-widest text-xs`
  - `shadow-[2px_2px_0_rgba(249,115,22,0.60)] hover:shadow-[3px_3px_0_rgba(249,115,22,0.80)]`

### 24. Browser Workspace
- **ID:** `browser-workspace`
- **Vibe:** Browser-app hybrid — macOS-inspired floating panels, tab bars, content areas (See source file for full spec)
- **Typography:** SF Pro Display alternative (system-ui, -apple-system), Inter fallback
- **Colors:** Light gray surface, subtle borders, accent per context
- **Layout:** App-shell with sidebar + content area, floating panels
- **Motion:** Native-feel transitions, 200-300ms
- **Icons:** Outlined, SF Symbols or Lucide

---

## Category: minimal (3 styles)

### 25. Nordic Minimal
- **ID:** `nordic-minimal`
- **Vibe:** Clean Scandinavian restraint — breathable whitespace, hairline borders, typographic confidence
- **Typography:** Space Grotesk (headings, 600-700), Inter (body, 300-400)
- **Colors:** Near-black #2d2d2d, warm neutral #fafafa, accent #6b7f3b, surface #f3f4f6
- **Layout:** Left-aligned hero, border-radius: 4px, spacious density
- **Motion:** Fade-up 20px over 300ms, stagger 60ms, easing cubic-bezier(0.16,1,0.3,1), scroll only
- **Icons:** Outlined, Heroicons
- **Surfaces:** `bg-gray-50 border border-gray-100 rounded`, hairline rule `border-b border-gray-200`
- **Anti-patterns:** Centered hero without motion, heavy drop shadows, gradients, rounded-3xl pills
- **Products:** SaaS, Minimal, Productivity
- **CSS Patterns:**
  - `border-b border-gray-200 pb-8 mb-12`
  - `text-left max-w-xl space-y-4`
  - `bg-gray-50 border border-gray-100 rounded p-6`
  - `tracking-tight font-semibold text-4xl text-gray-900`
  - `text-gray-500 text-sm uppercase tracking-widest`

### 26. Swiss Precision
- **ID:** `swiss-precision`
- **Vibe:** Grid-perfect Helvetica-era rigour — strict 12-column system, zero decoration
- **Typography:** Inter (headings, 700-900, tight tracking -0.04em), Helvetica Neue fallback
- **Colors:** Pure black #000000, white #ffffff, red accent #dc2626
- **Layout:** 12-col-grid, border-radius: 2px, compact density
- **Motion:** Fade-up 16px over 250ms, linear easing only, opacity crossfade 150ms, no springs
- **Icons:** Outlined, Heroicons
- **Surfaces:** `border-t border-gray-900 pt-4`, `col-span-8 border-l-4 border-black pl-6`
- **Anti-patterns:** Decorations, asymmetric overlapping, rounded corners beyond 4px, motion beyond fade
- **Products:** SaaS, Dashboard, Corporate
- **CSS Patterns:**
  - `grid grid-cols-12 gap-x-4 gap-y-0`
  - `col-span-8 border-l-4 border-black pl-6`
  - `text-xs font-mono text-gray-400 tracking-widest uppercase`
  - `border-t border-gray-900 pt-4`
  - `max-w-screen-xl mx-auto px-8`

### 27. Pure Flat
- **ID:** `pure-flat`
- **Vibe:** Ultra-flat surfaces with zero depth — color-only hierarchy, slate backgrounds
- **Typography:** DM Sans (single family, headings 600-700, body 400)
- **Colors:** Slate-50 #f8fafc, primary #1e293b, accent #3b82f6, surface #f1f5f9
- **Layout:** Single-column-stack, border-radius: 12px, spacious density
- **Motion:** Fade-up 24px over 320ms, ease-out, stagger 80ms, opacity nudge only on hover
- **Icons:** Outlined, Lucide
- **Surfaces:** `bg-slate-100 rounded-xl` (borderless, color defines boundary), blue accent block `bg-blue-50`
- **Anti-patterns:** Any box-shadow, visible borders, gradients, multiple font families, compact density
- **Products:** SaaS, Documentation, Developer-Tools
- **CSS Patterns:**
  - `bg-slate-50 min-h-screen`
  - `max-w-2xl mx-auto px-6 py-16 space-y-12`
  - `bg-slate-100 rounded-xl p-8`
  - `bg-blue-50 text-blue-700 rounded-full px-3 py-1 text-xs font-medium`
  - `text-slate-900 text-4xl font-semibold tracking-tight leading-tight`

---

## Category: playful (3 styles)

### 28. Playful Pop
- **ID:** `playful-pop`
- **Vibe:** Fun bouncy energy with saturated pastels, rounded shapes, spring physics
- **Typography:** Quicksand (headings, bold), Nunito (body)
- **Colors:** Violet primary #7c3aed, surface white, violet-50 background #f5f3ff
- **Layout:** Centered-hero, border-radius: 24px, balanced density
- **Motion:** Spring-bouncy, buttons scale 1.05 with shadow growth, click compresses scale(0.95), staggered entrance
- **Icons:** Rounded, Phosphor
- **Surfaces:** `bg-white rounded-3xl shadow-[0_8px_24px_rgba(124,58,237,0.20)] border border-violet-100`
- **Anti-patterns:** Dark color scheme, hairline borders, monospace fonts, dense data layouts
- **Products:** Education, E-commerce, Kids, Social
- **CSS Patterns:**
  - `bg-violet-50 min-h-screen`
  - `rounded-3xl px-10 py-5 bg-violet-500 text-white font-bold text-lg shadow-lg hover:shadow-xl`
  - `grid grid-cols-2 md:grid-cols-3 gap-4 p-6`
  - `bg-white rounded-2xl p-5 shadow-md border border-violet-100`

### 29. Soft Pastel Wellness
- **ID:** `soft-pastel-wellness`
- **Vibe:** Airy pastel floating cards with gentle shadows — approachable wellness aesthetic
- **Typography:** Comfortaa (headings), Nunito Sans (body, 1.7 line-height)
- **Colors:** Sky #7dd3fc, mint #86efac, sky-50 background #f0f9ff, surface white
- **Layout:** Floating-cards, border-radius: 28px, spacious density
- **Motion:** Spring-soft entrance, hover lifts card 3px with shadow expansion, calm wellness rhythm
- **Icons:** Rounded, Phosphor
- **Surfaces:** `bg-white rounded-[28px] shadow-[0_4px_32px_rgba(125,211,252,0.20),0_1px_8px_rgba(0,0,0,0.04)] border border-sky-100`
- **Anti-patterns:** Dark mode, harsh borders, dense layouts, high-saturation neon
- **Products:** Healthcare, Wellness, Education
- **CSS Patterns:**
  - `bg-sky-50 min-h-screen p-8`
  - `flex flex-wrap gap-6 justify-center`
  - `bg-white rounded-[28px] p-8 shadow-[0_4px_32px_rgba(125,211,252,0.20)] border border-sky-100`
  - `text-emerald-500 text-sm font-medium bg-emerald-50 rounded-full px-3 py-1`

### 30. Tactile Clay
- **ID:** `tactile-clay`
- **Vibe:** Physical 3D clay aesthetic — inflated rounded shapes, multi-layer shadows, bouncy spring physics
- **Typography:** Nunito ExtraBold (headings, gradient text), DM Sans (body)
- **Colors:** Purple #c084fc, pink #f472b6, gradient surface pink-100 → purple-100
- **Layout:** Floating-cards-3d, border-radius: 24px, balanced density
- **Motion:** Spring-bouncy on entrance, hover inflates scale(1.03) with shadow increase, click deflates scale(0.95)
- **Icons:** Rounded, Phosphor
- **Surfaces:** `rounded-3xl shadow-[0_10px_40px_-10px_rgba(0,0,0,0.2),inset_0_1px_rgba(255,255,255,0.80)]`
- **Anti-patterns:** Flat design, dark backgrounds, sharp corners, monospace fonts
- **Products:** Kids, Games, Creative
- **CSS Patterns:**
  - `bg-gradient-to-b from-pink-100 to-purple-100 min-h-screen p-8`
  - `rounded-3xl p-6 shadow-[0_10px_40px_-10px_rgba(0,0,0,0.2),inset_0_1px_rgba(255,255,255,0.8)]`
  - `text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-b from-gray-800 to-gray-600`
  - `active:scale-95 active:shadow-[0_4px_16px_-4px_rgba(0,0,0,0.2)] transition-all duration-150`

---

## Category: poster (2 styles)

### 31. Poster Bold Typography
- **ID:** `poster-bold-typography`
- **Vibe:** Poster-grade bold typography as primary visual — oversized letterforms, stacked compositions
- **Typography:** Oswald (headings, 700 uppercase), Barlow (body, 400-600)
- **Colors:** Ink #0f172a, rose accent #f43f5e, surface #f1f5f9
- **Layout:** Single-column-stack, border-radius: 0, spacious density
- **Motion:** Letters slide in from bottom: translateY(100%)→0 with clip, per-word stagger 40ms, 600ms
- **Icons:** Filled, Material Symbols
- **Surfaces:** Pure flat white #f8fafc, ink text — typography IS the visual
- **Anti-patterns:** Decorative gradients, card-based layouts, excessive padding softening impact
- **Products:** Events, Conference, Magazine, Media
- **CSS Patterns:**
  - `bg-slate-50 text-slate-900 min-h-screen`
  - `text-[clamp(4rem,12vw,10rem)] font-black uppercase tracking-tighter leading-none`
  - `text-rose-500 font-black uppercase text-[clamp(3rem,8vw,7rem)]`

### 32. Golden Charcoal
- **ID:** `golden-charcoal`
- **Vibe:** Warm charcoal base with golden highlight strokes — vintage poster warmth meets modern typography
- **Typography:** Abril Fatface (display, headlines), Lora (body, italic for hierarchy)
- **Colors:** Charcoal #292524, gold #d97706, cream #fef3c7, sand #e7e5e4
- **Layout:** Asymmetric-scroll, border-radius: 8px, balanced density
- **Motion:** Fade-up 24px over 500ms on scroll, stagger 120ms, gold underline sweeps 200ms
- **Icons:** Rounded, Phosphor
- **Surfaces:** Warm white #fafaf9, charcoal headlines, amber accent details
- **Anti-patterns:** Cold blue/tech colors, geometric sans as display, dark mode backgrounds
- **Products:** Restaurant, Hospitality, Craft, Culture
- **CSS Patterns:**
  - `bg-stone-50 text-stone-900 min-h-screen`
  - `font-serif text-7xl leading-none tracking-tight text-stone-800`
  - `text-amber-600 font-semibold uppercase tracking-widest text-sm`
  - `border-l-4 border-amber-500 pl-6 italic text-stone-600`

---

## Category: tech (4 styles)

### 33. Cyber Serif
- **ID:** `cyber-serif`
- **Vibe:** Cyberpunk meets classical serif — futuristic dark with unexpected serif elegance
- **Typography:** Playfair Display (headings, 900), Fira Code (body, 300-400)
- **Colors:** Midnight #0f0f23, cyan #22d3ee, purple #a855f7, surface #1a1a35
- **Layout:** Bento-grid, border-radius: 8px, compact density
- **Motion:** Cells scale 0.95→1.0 on entrance, neon border glow intensifies on hover 200ms
- **Icons:** Two-tone, Material Symbols
- **Surfaces:** `bg-[#1a1a35] border border-cyan-500/20 rounded-lg`, cyber glow `shadow-[0_0_20px_-4px_rgba(34,211,238,0.15)]`
- **Anti-patterns:** Warm color palettes, pure sans-serif, light backgrounds, playful shapes
- **Products:** AI, Data-Science, Fintech
- **CSS Patterns:**
  - `bg-[#0f0f23] text-sky-100 min-h-screen`
  - `grid grid-cols-3 gap-3 p-4`
  - `bg-[#1a1a35] border border-cyan-500/20 rounded-lg p-5 shadow-[0_0_20px_-4px_rgba(34,211,238,0.15)]`
  - `font-serif text-5xl font-black leading-none text-sky-100`

### 34. Futurist Holo
- **ID:** `futurist-holo`
- **Vibe:** Sci-fi chrome split-screen — holographic gradients, sharp geometry, neon glow accents
- **Typography:** Orbitron (headings, 700-900, wide tracking), Rajdhani (body, 400-600)
- **Colors:** Deep space #050510, cyan #06b6d4, violet #8b5cf6, pink #ec4899
- **Layout:** Split-screen, border-radius: 12px, balanced density
- **Motion:** Scale from 0.9→1.0 + opacity 0→1 over 500ms, holographic shimmer 300ms, scan-line border animation
- **Icons:** Sharp, Material Symbols
- **Surfaces:** Holographic gradient border via `background:linear-gradient()_padding-box,linear-gradient()_border-box`
- **Anti-patterns:** Light backgrounds, warm earth tones, rounded pills, soft organic forms
- **Products:** AI, Space, Gaming, Crypto
- **CSS Patterns:**
  - `bg-[#050510] text-white min-h-screen`
  - `grid grid-cols-2 h-screen`
  - `border border-transparent [background:linear-gradient(#050510,#050510)_padding-box,linear-gradient(135deg,#06b6d4,#8b5cf6,#ec4899)_border-box] rounded-xl`
  - `text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-violet-400 to-pink-400`

### 35. Retro Terminal
- **ID:** `retro-terminal`
- **Vibe:** Nostalgic tech — amber-on-dark monospace panels, sticky sidebar, CRT scanlines
- **Typography:** JetBrains Mono (headings, 700), IBM Plex Mono (body)
- **Colors:** Near-black #0d0d0d, amber #f59e0b, scanline rgba(0,0,0,0.3)
- **Layout:** Sticky-sidebar, border-radius: 2px, compact density
- **Motion:** Text fades in character-by-character 30ms/char, screen flicker 2 frames on load, cursor blink 500ms
- **Icons:** Filled, Lucide
- **Surfaces:** `bg-[#0d0d0d] text-amber-400`, CRT scanline `repeating-linear-gradient(0deg,transparent,transparent_2px,rgba(0,0,0,0.3)_2px,rgba(0,0,0,0.3)_4px)`
- **Anti-patterns:** Light backgrounds, rounded corners beyond 4px, sans-serif, pastel colors
- **Products:** Developer-Tools, Fintech, CLI
- **CSS Patterns:**
  - `bg-[#0d0d0d] text-amber-400 font-mono min-h-screen`
  - `flex h-screen overflow-hidden`
  - `w-56 border-r border-amber-500/20 p-4 flex-shrink-0`
  - `[background-image:repeating-linear-gradient(0deg,transparent,transparent_2px,rgba(0,0,0,0.3)_2px,rgba(0,0,0,0.3)_4px)]`

### 36. Synapse Ambient
- **ID:** `synapse-ambient`
- **Vibe:** Neural-network inspired ambient glow with node-and-edge visual language
- **Typography:** Exo 2 (headings, 700, wide tracking), Inter (body, 300-400)
- **Colors:** Deep forest #022c22, emerald #10b981, mint #34d399, surface #052e16
- **Layout:** Centered-floating, border-radius: 50%/16px, spacious density
- **Motion:** Elements drift up 32px with fade over 700ms, node pulses every 3s, spring soft easing
- **Icons:** Outlined, Heroicons
- **Surfaces:** `bg-[#022c22]`, emerald glow nodes, floating panels `bg-[#052e16]`
- **Anti-patterns:** Warm/amber palette, dense grids, serif display, sharp angular shapes
- **Products:** AI, Biotech, Research, Neural
- **CSS Patterns:**
  - `bg-[#022c22] text-emerald-100 min-h-screen`
  - `max-w-3xl mx-auto px-8 py-32 text-center`
  - `border border-emerald-500/20 rounded-2xl p-8 shadow-[0_0_40px_-8px_rgba(16,185,129,0.2)]`
  - `text-emerald-400 text-sm font-medium tracking-[0.2em] uppercase`

---

## Style Selection Matrix

| Product Type | Primary Styles | Secondary Styles |
|---|---|---|
| SaaS | Nordic Minimal, Swiss Precision, Glass Aurora | OLED Dark Luxury, Nordic Minimal |
| E-commerce | Bold Commerce, Playful Pop, Warm Editorial | Tactile Clay, Nordic Minimal |
| Dashboard | Electric Dashboard, Swiss Precision, Dark Elite Frosted | Retro Terminal, OLED Dark |
| Mobile App | Glass Aurora, Slate Atmospheric, Obsidian Lime | Nordic Minimal, Soft Cloud |
| Portfolio | Editorial Luxury, B&W Motion Studio, Immersive Cinematic | Cinematic Noir Gallery, Organic Serif |
| Creative | Editorial Luxury, Kinetic Magazine, Season 04 Fashion | Golden Charcoal, Playful Pop |
| Fintech | Dark Elite Frosted, OLED Dark Luxury, Cyber Serif | Synapse Ambient, Retro Terminal |
| Gaming | Obsidian Lime, Futurist Holo, Neo-Brutalist Raw | Kinetic Orange, Yellow Neo-Brutalist |
| Fashion | Season 04 Fashion, Editorial Luxury, Golden Charcoal | Poster Bold Typography |
| Wellness | Soft Pastel Wellness, Organic Serif, Earthy Organic | Tactile Clay, Forest Green Grid |
| Developer-Tools | Retro Terminal, Swiss Precision, Industrial Disruptor | Yellow Neo-Brutalist, Cyber Serif |
| Luxury | Editorial Luxury, Midnight Editorial, Gold on Black AI | Immersive Cinematic, Dark Elite Frosted |
| Media | Midnight Editorial, Cinematic Noir Gallery, Poster Bold | B&W Motion Studio, Organic Serif |
| Sustainability | Forest Green Grid, Earthy Organic, Nordic Minimal | Tactile Clay, OLED Dark |
| Architecture | Refined Industrial, Nordic Minimal, Forest Green Grid | Swiss Precision |
| Art/Museum | Cinematic Noir Gallery, B&W Motion Studio, Matte Earth Toned | Immersive Cinematic |
