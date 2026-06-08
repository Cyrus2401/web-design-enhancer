# DESIGN.md — Manus Demo

Design contract for **Manus**, an AI agent orchestration tool.
Validated by `python3 scripts/validate_design.py DESIGN.md`: 0 errors.

---

## 0. Sources Phase 0

- **Brand used:** Vercel
- **Command executed:** `npx getdesign@latest add vercel`
- **Query executed:** `python3 scripts/search.py "ai agent orchestration developer tool" --design-system -p "Manus"`
- **Chosen style:** Clean Tech + Neo-Brutalism
- **Justification:** AI-agent oriented developer tool. Vercel brings extreme precision (radius 0, sharp edges, absolute black/white). Neo-Brutalism for strong identity. Zero ornamentation — every pixel has a function.

---

## 1. Theme & Visual Concept

- **Concept:** High-precision tech minimalism — performance-driven interfaces, absolute contrasts, no frills.
- **Keywords:** Geometric, contrasted, functional, terminal, precise.
- **References:** Vercel (absolute black/white, fine typography), Linear (density, tight tokens).

---

## 2. Color Palette

| Role | Hex | Usage |
| :--- | :--- | :--- |
| Primary | #000000 | Primary buttons, strong text, borders |
| Secondary | #171717 | Dark surfaces, nav, sidebar |
| Background | #FFFFFF | Main background |
| Text | #0A0A0A | Body text, headings |
| Muted | #737373 | Secondary labels, placeholders |
| Accent | #0066FF | Active links, focus, highlights |
| Success | #10B981 | Confirmations, OK states |
| Danger | #EF4444 | Errors, destructive actions |

WCAG AA contrast — Text on Background: 20.3:1 (min 4.5:1). Accent on Background: 4.6:1 (min 3.0:1).

---

## 3. Typography

- **Geist Mono** (Display, Titles, UI labels) — technical monospace, terminal identity.
- **Geist Sans** (Body, body text) — readable, neutral, same family.

```css
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600;700&family=Geist:wght@400;500;600&display=swap');
```

---

## 4. Typography Hierarchy

- **H1**: 40px / 600 / 1.1
- **H2**: 28px / 600 / 1.2
- **H3**: 18px / 500 / 1.3
- **P**: 15px / 400 / 1.6
- **Small**: 12px / 400 / 1.5
- **Mono (IDs, logs, code)**: 13px / 400 / 1.4

---

## 5. Spacing & Grid

- **Grid base:** 8px
- **Vertical section padding:** 64px
- **Horizontal section padding:** 24px
- **Card inner padding:** 16px
- **Gap between elements:** 8px, 16px, 24px
- **Log line height:** 32px
- **Radius:** 0px (sharp edges — precise tech identity)

---

## 6. Components & States

### Buttons

- **Primary (Normal):** Background #000000, text #FFFFFF, padding 8px 16px, font-weight 500, radius 0
- **Primary (Hover):** Background #171717, transition 150ms ease-out
- **Secondary (Normal):** Background #FFFFFF, border 1px solid #000000, text #000000, radius 0
- **Ghost (Normal):** Transparent background, text #737373, no border

### Contact / CTA Section
- **Title:** Visible H2 (28–32px)
- **Subtitle:** Descriptive text, 1–2 lines
- **Action:** Primary button or email field + CTA
- **Max vertical padding:** 96px (never more — minimal density required)

### Grid behavior on odd number of cards
- **Strategy:** Last card with `grid-column: 1 / -1` (full-width) if N%3 != 0
- **Alignment:** Centered on the incomplete row

### Cards

- **Structure:** Background #FFFFFF, border 1px solid #E5E5E5, radius 0
- **Inner Padding:** 16px
- **Shadow:** none (sharp edges are enough)

### Console / Logs

- **Background:** #0A0A0A
- **Text:** #E5E5E5 (monospace)
- **Success accent:** #10B981
- **Error accent:** #EF4444
- **Prompt:** #0066FF

---

## 7. Motion & Animations

- **General transitions:** 150ms ease-out
- **Hover states:** 100ms ease-in-out
- **Stagger entries:** duration 300ms, stagger 40ms, ease power2.out
- **Logs stream:** line-by-line appearance, 50ms between each
- **Accessibility:** `prefers-reduced-motion` mandatory.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 8. Dark Mode

| Role | Hex | Light Equivalent |
| :--- | :--- | :--- |
| Background | #0A0A0A | #FFFFFF |
| Surface | #171717 | #F5F5F5 |
| Text | #FAFAFA | #0A0A0A |
| Secondary text | #A3A3A3 | #737373 |
| Border | #262626 | #E5E5E5 |
| Primary | #FFFFFF | #000000 |
| Accent | #3B82F6 | #0066FF |

**Dark mode rules:**
- Background #0A0A0A: relative luminance ~0.002 — well below the 9% threshold
- Text #FAFAFA on Background #0A0A0A: 19.8:1 — WCAG AAA compliant
- Accent #3B82F6 adapted for sufficient contrast on dark background
- No JS toggle: `prefers-color-scheme: dark` only

---

## Anti-Slop Validation Checklist

- [x] **DESIGN.md**: Complete, Phase 0 documented.
- [x] **Fonts**: 2 fonts (Geist Mono + Geist Sans — same family, consistency guaranteed).
- [x] **Spacing**: All multiples of 8px (8, 16, 24, 32, 40, 48, 64).
- [x] **Radii**: 0px — intentional sharp edges, Neo-Brutalism identity.
- [x] **Icons**: Mono only for justified functions in the console.
- [x] **Gradients**: No decorative gradient.
- [x] **Artifacts**: No emoji, no sticker.
- [x] **Logo**: Styled text "MANUS" in Geist Mono 600.
- [x] **Structure**: Terminal-first layout — not a generic landing page.
- [x] **Text**: Precise descriptions, zero buzzword.
- [x] **Buttons**: 3 variants (Primary, Secondary, Ghost).
- [x] **Colors**: 8 colors with semantic roles.
- [x] **Animations**: All <= 400ms. prefers-reduced-motion documented.
- [x] **WCAG AA**: 20.3:1 Text/Background — largely compliant.
- [x] **Dark Mode**: §8 section complete, background #0A0A0A, 7 inverted tokens.
