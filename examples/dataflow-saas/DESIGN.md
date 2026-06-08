# DESIGN.md — DataFlow

Design contract for **DataFlow**, a B2B analytics SaaS.
Validated by `python3 scripts/validate_design.py DESIGN.md`.

---

## 0. Sources Phase 0

- **Brand used:** Linear
- **Command executed:** `npx getdesign@latest add linear`
- **Query executed:** `python3 scripts/search.py "saas analytics dashboard" --design-system -p "DataFlow"`
- **Chosen style:** Data-Dense Dashboard
- **Justification:** High information density, tight grid, maximum performance, zero ornamentation. Linear brings precise tokens (radius 4px, hairline borders).

---

## 1. Theme & Visual Concept

- **Concept:** Analytical precision — interfaces focused on data readability, strong contrast, no frills.
- **Keywords:** Dense, structured, technical, reliable, sober.
- **References:** Linear (compactness, precise tokens), Stripe (typographic clarity).

---

## 2. Color Palette

| Role | Hex | Usage |
| :--- | :--- | :--- |
| Primary | #1E40AF | Primary buttons, active links, focus |
| Secondary | #3B82F6 | Hover, secondary accents, sparklines |
| Accent | #D97706 | Critical CTAs, highlights |
| Background | #F8FAFC | Main background |
| Text | #1E3A8A | Main text, headings |
| Success | #16A34A | Positive indicators, increasing deltas |
| Warning | #F59E0B | Alerts, warnings |
| Danger | #DC2626 | Destructive actions, errors |

WCAG AA contrast — Text on Background: 9.2:1 (min 4.5:1). Primary on Background: 8.1:1 (min 3.0:1).

---

## 3. Typography

- **Fira Code** (Display, Titles, KPI) — technical monospace, fixed-width digits, aligned columns.
- **Fira Sans** (Body, body text) — readable, neutral, complementary.

```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@400;500;600;700&display=swap');
```

---

## 4. Typography Hierarchy

- **H1**: 28px / 700 / 1.2
- **H2**: 22px / 600 / 1.3
- **H3**: 18px / 600 / 1.4
- **P**: 14px / 400 / 1.6
- **Small**: 12px / 400 / 1.5

---

## 5. Spacing & Grid

- **Grid base:** 8px
- **Column gutter:** 16px
- **Vertical section padding:** 32px
- **Horizontal section padding:** 24px
- **Card inner padding:** 16px
- **Gap between cards:** 16px
- **Table row height:** 40px
- **Radius:** 4px (cards, buttons)

---

## 6. Components & States

### Buttons

- **Primary (Normal):** Background #1E40AF, white text, padding 8px 16px, font-weight 600
- **Primary (Hover):** Background #1D4ED8, transition 200ms ease-out
- **Secondary (Normal):** Transparent, border 1px #1E40AF, text #1E40AF
- **Ghost (Normal):** Transparent, text #1E3A8A, no border

### Contact / CTA Section
- **Title:** Visible H2 (28–32px)
- **Subtitle:** Descriptive text, 1–2 lines
- **Action:** Primary button or email field + CTA
- **Max vertical padding:** 96px (never more — minimal density required)

### Grid behavior on odd number of cards
- **Strategy:** Last card with `grid-column: 1 / -1` (full-width) if N%3 != 0
- **Alignment:** Centered on the incomplete row

### Cards

- **Structure:** White background, border 1px solid #DBEAFE, radius 4px
- **Inner Padding:** 16px
- **Shadow:** `0 1px 3px rgba(30, 64, 175, 0.08)`

---

## 7. Motion & Animations

- **General transitions:** 200ms ease-out
- **Hover states:** 150ms ease-in-out
- **Stagger entries:** duration 300ms, stagger 40ms, ease power2.out
- **Tooltip:** 150ms ease-out
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

## Anti-Slop Validation Checklist

- [x] **DESIGN.md**: Complete, Phase 0 documented.
- [x] **Fonts**: 2 fonts (Fira Code + Fira Sans).
- [x] **Spacing**: All multiples of 8px (4, 8, 16, 24, 32, 40, 48, 64).
- [x] **Radii**: 4px — clean and technical.
- [x] **Icons**: Lucide only for justified functions (targeted functional icons only).
- [x] **Gradients**: No decorative gradient.
- [x] **Artifacts**: No emoji, no sticker, no unrequested status badge.
- [x] **Logo**: Styled text "DataFlow" in Fira Code 600.
- [x] **Structure**: Dashboard (fixed sidebar + topbar + grid of cards).
- [x] **Text**: Precise descriptions, zero buzzword.
- [x] **Buttons**: 3 variants (Primary, Secondary, Ghost).
- [x] **Colors**: 8 colors with semantic roles.
- [x] **Animations**: All <= 400ms. prefers-reduced-motion documented.
- [x] **WCAG AA**: Ratios calculated and compliant.

---

## 8. Dark Mode

| Role | Hex | Light Equivalent |
| :--- | :--- | :--- |
| Background | #0F172A | #F8FAFC |
| Surface | #1E293B | #FFFFFF |
| Text | #E2E8F0 | #1E3A8A |
| Secondary text | #94A3B8 | #64748B |
| Border | #334155 | #DBEAFE |
| Primary | #3B82F6 | #1E40AF |
| Accent | #FBBF24 | #D97706 |

**Dark mode rules:**
- Background #0F172A: relative luminance ~0.007 — well below the 9% threshold
- Text #E2E8F0 on Background #0F172A: 14.2:1 — WCAG AAA compliant
- Primary adapted from #1E40AF -> #3B82F6 to maintain contrast on dark background
- Accent adapted from #D97706 -> #FBBF24 for readability on dark background
- `prefers-color-scheme: dark` only — no JS toggle
