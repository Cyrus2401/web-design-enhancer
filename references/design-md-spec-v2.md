# DESIGN.md Specification — Format v3

The `DESIGN.md` file is the project's **single design contract**. It is read by AI agents before any implementation, and mechanically validated by `validate_design.py` before any code is written.

> **Fundamental rule:** If DESIGN.md is not valid, no code should be written.
> `check.py --gate 1` blocks progress if `validate_design.py` returns an error.

---

## Philosophy

DESIGN.md is not a passive reference document — it is an **execution contract**.
Each section corresponds to a mechanical rule that can be verified automatically.
The goal: make it impossible to produce "AI slop" even with an unsupervised agent.

**3 principles:**
1. **Explicit > implicit** — anything not written will be invented by the AI
2. **Verifiable > subjective** — every rule must be testable by a script
3. **Minimal > exhaustive** — a contract that is too long does not get read

---

## Full structure (§0 to §10)

### § 0 — Sources Phase 0

**Mandatory.** Proves that the design is anchored in real references, not in the AI's training data.

```markdown
## 0. Sources Phase 0

- **Brand used:** [BrandName]
- **Command executed:** `npx getdesign@latest add [brand]`
- **Query executed:** `python3 scripts/search.py "[query]" --design-system -p "[Project]"`
- **Chosen style:** [Style]
- **Justification:** [Why this style for this project]
```

**Validated by:** `check.py --gate 0`
**Blocks if:** `getdesign-*.md` or `design-system-output*.md` files are missing, or placeholders are not replaced (`[BrandName]`, `TODO`, `to fill in`).

---

### § 1 — Theme & Visual Concept

**Mandatory.** Defines the intent — the "why" of the design.

```markdown
## 1. Theme & Visual Concept

- **Concept:** [Precise description of the visual identity]
- **Keywords:** [3–5 words, no generic buzzwords]
- **References:** [Real sites/products, with justification]
```

**Rules:**
- The following themes are **forbidden** (detected and blocking):
  `glassmorphism`, `dark cyberpunk`, `particle background`, `typewriter effect`, `glow cursor`, `neon glow`, `grid background`, `aurora borealis`
- Generic keywords are **forbidden**: `modern`, `elegant`, `premium`, `futuristic`, `immersive`
- References must be real sites — not abstract adjectives

**Validated by:** `validate_design.py` → `_validate_theme_originality()`

---

### § 2 — Color Palette

**Mandatory.** The only place where hex values are defined.

```markdown
## 2. Color Palette

| Role | Hex | Usage |
| :--- | :--- | :--- |
| Primary    | #XXXXXX | [Specific usage] |
| Secondary  | #XXXXXX | [Specific usage] |
| Background | #XXXXXX | Main background |
| Text       | #XXXXXX | Main body text |
| Accent     | #XXXXXX | [Specific usage] |
| Success    | #XXXXXX | [Specific usage] |
| Warning    | #XXXXXX | [Specific usage] |
| Danger     | #XXXXXX | Destructive actions, errors |
```

**Rules:**
- **4 to 8 hex values** in this section — no more (hex values in §6, §7, §8 are not counted)
- Do not write hex values in the WCAG text of this section — compute them separately
- `Background` and `Text` roles are **mandatory** — used for automatic WCAG calculation
- **WCAG AA mandatory:** Text/Background >= 4.5:1, Primary/Background >= 3.0:1

**Validated by:** `validate_design.py` → `_validate_colors()` + `_validate_wcag_contrast()`

**Quick contrast calculation:**
```
L = 0.2126xR + 0.7152xG + 0.0722xB  (values 0-1 linearized)
Contrast = (L_light + 0.05) / (L_dark + 0.05)
```

---

### § 3 — Typography

**Mandatory.** Max 2 font families.

```markdown
## 3. Typography

- **FontName** (Display) — [justification for choice]
- **FontName** (Body) — [justification for choice]

```css
@import url('https://fonts.googleapis.com/...');
```
```

**Rules:**
- **Exactly 1 or 2 fonts** — never more
- Mandatory format: `**FontName** (Display)` or `**FontName** (Body)`
  → This exact pattern is what `validate_design.py` detects
- If a single font: use weight variations for hierarchy (300/400/600/700)
- Allowed system fonts: `Inter`, `system-ui`, `-apple-system` (no import needed)

**Validated by:** `validate_design.py` → `_validate_typography()`

---

### § 4 — Typography Hierarchy

**Mandatory.** Defines exact sizes — removes all ambiguity for the AI.

```markdown
## 4. Typography Hierarchy

- **H1**: [px] / [weight] / [line-height]
- **H2**: [px] / [weight] / [line-height]
- **H3**: [px] / [weight] / [line-height]
- **P**:  [px] / [weight] / [line-height]
- **Small**: [px] / [weight] / [line-height]
```

**Rules:**
- H1 between 28px and 80px
- P between 13px and 18px
- Small between 11px and 14px
- No font-size at 16px for everything — that's the signal of a hierarchy that wasn't thought through

**Not automatically validated** — human verification required.

---

### § 5 — Spacing & Grid

**Mandatory.** Defines the base grid and all spacing.

```markdown
## 5. Spacing & Grid

- **Grid base:** 8px
- **[Padding/Gap/Height]:** [value]px
- **Radius:** [value]px
```

**Rules:**
- **All px values must be multiples of 8** (exception: 4px for micro-spacing)
- `audit_spacing.py` scans the CSS/JSX code and flags non-conforming values
- A 0px radius is allowed (Neo-Brutalism style)
- Explicitly mention "Grid base: 8px" — `validate_design.py` looks for it

**Validated by:** `validate_design.py` → `_validate_spacing()` + `audit_spacing.py` on code

---

### § 6 — Components & States

**Mandatory.** Defines UI components and all of their states.

```markdown
## 6. Components & States

### Buttons
- **Primary (Normal):** [description]
- **Primary (Hover):** [description]
- **Secondary (Normal):** [description]
- **Ghost (Normal):** [description]

### Cards
- **Structure:** [description]
- **Inner Padding:** [value]px
- **Shadow:** [value or "none"]
```

**Rules:**
- **Maximum 3 button variants** in this section
- Each state (normal, hover, disabled) must be documented
- Colors in §6 use the hex values defined in §2 — no new colors

**Validated by:** `validate_design.py` → `_validate_components()`

---

### § 7 — Motion & Animations

**Mandatory.** Defines dynamic behavior.

```markdown
## 7. Motion & Animations

- **General transitions:** [duration]ms ease-out
- **Hover states:** [duration]ms ease-in-out
- **Stagger entries:** duration [duration]ms, stagger [duration]ms
- **Accessibility:** `prefers-reduced-motion` mandatory.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```
```

**Rules:**
- **All durations <= 400ms** — beyond that it is perceived as slow
- Exception documented in §1 if a long animation is intentional (e.g. gradient mesh <= 30s)
- `prefers-reduced-motion` must be mentioned explicitly in §7
- `diff_design_vs_code.py` scans the actual code and flags durations exceeding the max defined in §7

**Validated by:** `validate_design.py` → `_validate_animations()` + `diff_design_vs_code.py`

---

### § 8 — Dark Mode

**Mandatory since v3.** Improvised dark mode is the main source of post-delivery regressions.

```markdown
## 8. Dark Mode

| Role | Hex | Light Equivalent |
| :--- | :--- | :--- |
| Background       | #XXXXXX | #XXXXXX |
| Surface          | #XXXXXX | #XXXXXX |
| Text             | #XXXXXX | #XXXXXX |
| Secondary text   | #XXXXXX | #XXXXXX |
| Border           | #XXXXXX | #XXXXXX |
| Primary          | #XXXXXX | #XXXXXX |
| Accent           | #XXXXXX | #XXXXXX |

**Dark mode rules:**
- [Background luminance check]
- [Text/background contrast check]
- [Strategy: prefers-color-scheme vs JS toggle]
```

**Rules:**
- **>= 3 colors** in the dark mode table
- `background`, `text`, `surface` roles are **mandatory**
- **Dark background: relative luminance < 9%** — i.e. approximately < #333333
  Compliant examples: `#0A0A0A`, `#0F172A`, `#111827`, `#1C1C1E`
  Non-compliant examples: `#4A4A4A`, `#555555`, `#666666`
- Dark text on dark background >= 4.5:1 WCAG AA
- Recommended: `prefers-color-scheme: dark` only — no JS toggle unless requested

**Validated by:** `validate_design.py` → `_validate_dark_mode()`

---


---

### § 9 — Mobile

**Optional for web-only projects. Mandatory as soon as a native or hybrid app is in scope.**

`validate_design.py` automatically validates this section if it is present.

**Automatically verified rules:**

| Rule | Blocking | Script |
| :--- | :--- | :--- |
| Touch targets >= 44pt (iOS) / 48dp (Android) mentioned | Warning | `validate_design.py` |
| Safe Areas documented | Warning | `validate_design.py` |
| Native units (pt/dp) instead of px | Warning | `validate_design.py` |
| Mobile accessibility mentioned (VoiceOver/TalkBack) | Warning | `validate_design.py` |

**Antipatterns detected in code by `detect_ai_slop.py`:**

| Pattern | Signal | Remedy |
| :--- | :--- | :--- |
| Hardcoded screen widths (375, 390, 412px) | Fixed iPhone/Android dimension | `.frame(maxWidth: .infinity)` / `LayoutBuilder` |
| Hardcoded `Color.white` without `colorScheme` | Dark mode not handled | `Color(.systemBackground)` / `MaterialTheme.colorScheme.background` |
| `Image` without `accessibilityLabel` / `contentDescription` | VoiceOver/TalkBack inaccessible | Add the mandatory label |
| Hardcoded touch target < 40pt | Touch area too small | `.frame(width: 44, height: 44)` minimum |
| Generic SF Symbols / Material Icons | AI signal identical to web | Only justified functional icons |

**Units per platform:**

```
iOS / SwiftUI       -> pt    (points)       -- 4pt grid
Android / Compose   -> dp    (density-ind)  -- 4dp grid
Flutter             -> px    (logical)      -- 4 grid
React Native        -> dp    (auto-scaled)  -- 4 grid
```

**Minimal valid format:**

```markdown
## 9. Mobile

- **Stack:** SwiftUI
- **Platforms:** iOS 16+
- **Touch targets:** Buttons >= 44x44pt, extended touch areas on icons
- **Safe Areas:** .safeAreaInset() for content, background ignoreSafeArea()
- **Animations:** spring() for interactions, system animation for navigation
- **Dark mode:** Color(.systemBackground), Color(.label) — semantic colors only
- **Accessibility:** .accessibilityLabel() on all Images, Dynamic Type supported
```

---

### § 10 — Three.js

**Optional.** Required only if the project includes 3D scenes rendered with Three.js / React Three Fiber.

See `references/threejs-best-practices.md` for detailed guidance on performance, lighting, and asset handling.

---

## Final checklist (summary)

| § | Section | Validator | Blocking |
| :--- | :--- | :--- | :--- |
| 0 | Sources Phase 0 | `check.py --gate 0` | Yes |
| 1 | Theme & Concept | `validate_design.py` | Yes (forbidden themes) |
| 2 | Palette | `validate_design.py` | Yes (4–8 hex, WCAG) |
| 3 | Typography | `validate_design.py` | Yes (max 2 fonts) |
| 4 | Hierarchy | — | Manual |
| 5 | Spacing | `validate_design.py` + `audit_spacing.py` | Yes (multiples of 8px) |
| 6 | Components | `validate_design.py` | Yes (max 3 variants) |
| 7 | Motion | `validate_design.py` + `diff_design_vs_code.py` | Yes (<= 400ms) |
| 8 | Dark Mode | `validate_design.py` | Warning if missing |
| 9 | Mobile | `validate_design.py` | Optional, validated if present |
| 10 | Three.js | manual | Optional, validated if present |

---

## Common errors

**"Too many colors (X > 8)"**
-> Hex values in the WCAG text of §2 are being counted. Write ratios as plain text without hex: `Text on Background: 9.2:1` instead of `#1E3A8A on #F8FAFC: 9.2:1`.

**"Not enough fonts (0)"**
-> The format must be exactly `**FontName** (Display)` or `**FontName** (Body)`.
Unrecognized formats: `- Display: **Fira Code**` or `- Font: Fira Code`.

**"Generic icon detected: check"**
-> Unavoidable false positive caused by the word "Checklist". Add to `.slop-ignore`:
```ini
[icons]
check           # the word "check" inside "Checklist" — known validator false positive
```

**"Dark Mode section missing"**
-> Warning (non-blocking). Add `## 8. Dark Mode` with >= 3 colors, dark background, `background`/`text`/`surface` roles.

**"Animation Xms exceeds max"**
-> `diff_design_vs_code.py` detected a duration in the code exceeding the max from §7.
If intentional (e.g. decorative background animation), document the exception in §1 and §7.
