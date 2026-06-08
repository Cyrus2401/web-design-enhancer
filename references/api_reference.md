# Technical Reference — Web Design Enhancer

Complete technical specifications of the skill's scripts and formats.

---

## 1. Validation Scripts

### `validate_design.py`

Validates the `DESIGN.md` file against the skill's full contract.

```bash
python3 scripts/validate_design.py DESIGN.md
python3 scripts/validate_design.py DESIGN.md --strict
```

**Rules checked:**
- Section `## 0. Sources Phase 0` present and without placeholders
- Required sections present (§1 through §8 inclusive)
- Max 2 fonts — detected via `**FontName** (Display)` or `Font: FontName`
- Spacing values as multiples of 8px in §5
- 4 to 8 hex colors in §2 with semantic roles
- WCAG AA contrast: Text/Background ≥ 4.5:1, Primary/Background ≥ 3.0:1
- Animations ≤ 400ms in §7, mention of `prefers-reduced-motion`
- Max 3 button variants in §6
- Section `## 8. Dark Mode` present with ≥ 3 colors, background < #333 (luminance < 9%), roles `background`, `text`, `surface`
- Forbidden themes absent (glassmorphism, dark cyberpunk, particle background, typewriter effect, glow cursor, neon glow, grid background)
- Buzzwords absent (premium, modern, elegant...)

**Exit codes:** `0` = valid, `1` = blocking errors

---

### `detect_ai_slop.py`

Detects AI antipatterns in the DESIGN.md and/or the source code.

```bash
python3 scripts/detect_ai_slop.py --design DESIGN.md --code ./src
python3 scripts/detect_ai_slop.py --design DESIGN.md
```

**Detections:**
- Generic Lucide icons (sparkles, zap, star, bot, magic...)
- Cliché gradients (blue→purple, pink→purple, cyan→blue)
- Vague buzzwords (premium, modern, elegant, futuristic...)
- Unsolicited status badges (● LIVE NOW, SYS_STATUS: ONLINE...)
- Generic fonts (Arial, Helvetica, Georgia, Verdana...)
- shadcn/ui components left at default (variant="default" uncustomized)
- Placeholder logos (logo-placeholder, your-logo, brandname)

**Score:** Starts at 100, penalties applied per violation. Threshold: ≥ 80 for validation.

**Whitelist:** Create `.slop-ignore` at the project root to exempt false positives.
Each entry must include a justification comment — without a comment, the rule is ignored.

```ini
[icons]
search          # functional search bar in the nav

[buzzwords]
premium         # name of the pricing plan (not a vague adjective)

[files]
scripts/        # internal scripts — known false positives
```

---

### `diff_design_vs_code.py`

Compares the DESIGN.md contract against the actual CSS/JS/TSX code implemented.

```bash
python3 scripts/diff_design_vs_code.py DESIGN.md --code ./src
python3 scripts/diff_design_vs_code.py DESIGN.md --file index.css
python3 scripts/diff_design_vs_code.py DESIGN.md --code ./src --strict
```

**Comparisons performed:**
- Colors from §2 present in the code (exact + near-drift detection via RGB distance)
- Fonts from §3 loaded in font-family, Google Fonts imports, fontsource
- Animation durations in the code (CSS transitions, `@keyframes`, GSAP `duration:`) vs §7 max
- `--custom` CSS variables referencing DESIGN.md hex values (`--strict` only)

**Exit codes:** `0` = compliant, `1` = divergences detected

---

### `audit_spacing.py`

Analyzes CSS/JS/TSX files to detect spacing values off the 8px grid.

```bash
python3 scripts/audit_spacing.py --path ./src
python3 scripts/audit_spacing.py --file index.css
python3 scripts/audit_spacing.py --path ./src --output report.json
```

**Audited properties:** `padding`, `margin`, `gap`, `border-radius`, `width`, `height`
**Rule:** Every `px` value must be a multiple of 8 (exception: 4px for micro-spacing).

---

### `visual_audit.py`

Playwright visual audit on the actual rendered site — 4 breakpoints.

```bash
python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
```

**Breakpoints:** 375px (mobile), 768px (tablet), 1280px (desktop), 1920px (wide)

**Audits performed:**
- PNG screenshots per breakpoint
- Computed fonts (DOM computed styles)
- Actual spacing values (padding/margin non-multiples of 8px)
- Visual AI artifacts (emojis, placeholder logos, suspicious SVGs)

**Prerequisites:** `pip install playwright --break-system-packages && playwright install chromium`

**Output:** `audit-results/audit_report.json` + 4 PNG files

---

### `check.py`

Gate orchestrator — converts SKILL.md phases into sequential mechanical validations.

```bash
python3 scripts/check.py --gate 0           # Phase 0 performed?
python3 scripts/check.py --gate 1           # DESIGN.md valid?
python3 scripts/check.py --final            # Full validation before delivery
python3 scripts/check.py --final --code ./src
```

**Gate sequence:**

| Gate | Condition | Blocks if |
| :--- | :--- | :--- |
| 0 | `design-system-output*.md` + `getdesign-*.md` + `DESIGN.md` with §0 | Files missing or placeholders not replaced |
| 1 | `validate_design.py` without error | Gate 0 not passed or DESIGN.md invalid |
| Final | 4 scripts in sequence | Gate 1 not passed or any script fails |

**Final Gate — 4 steps:**
1. `detect_ai_slop.py` — AI antipatterns
2. `audit_spacing.py` — 8px grid
3. `validate_design.py` — DESIGN.md contract
4. `diff_design_vs_code.py` — DESIGN.md ↔ code divergences (if `--code` provided)

**Persistent log:** `.phase-log.json` at the project root — tracks passed gates.

---

### `search.py`

BM25 search engine across the UI/UX Pro Max data (CSV).

```bash
python3 scripts/search.py "saas analytics dashboard" --design-system -p "MyProject"
python3 scripts/search.py "fintech banking" --domain color
python3 scripts/search.py "button hover" --stack nextjs
```

**Available domains:** `style`, `color`, `chart`, `landing`, `product`, `ux`, `typography`, `icons`, `react`, `web`, `google-fonts`

**Available stacks:** `react`, `nextjs`, `vue`, `svelte`, `astro`, `swiftui`, `react-native`, `flutter`, `nuxtjs`, `shadcn`, `html-tailwind`, `angular`, `laravel`, `threejs`, `jetpack-compose`, `nuxt-ui`

---

## 2. DESIGN.md Format (v3)

The DESIGN.md is the single source of truth contract. Placed at the project root, read by `validate_design.py` before any code is written.

**Required sections:**

| # | Section | Validated by | Key rule |
| :--- | :--- | :--- | :--- |
| 0 | Phase 0 Sources | `check.py --gate 0` | getdesign + UI/UX Pro Max proven |
| 1 | Visual Theme & Concept | `validate_design.py` | No forbidden theme |
| 2 | Color Palette | `validate_design.py` | 4–8 hex, semantic roles, WCAG AA |
| 3 | Typography | `validate_design.py` | Max 2 fonts, format `**FontName** (Display)` |
| 4 | Typographic Hierarchy | — | H1 to Small with px / weight / line-height |
| 5 | Spacing and Grid | `validate_design.py` + `audit_spacing.py` | Multiples of 8px, grid mentioned |
| 6 | Components and States | `validate_design.py` | Max 3 button variants |
| 7 | Motion and Animations | `validate_design.py` | ≤ 400ms, prefers-reduced-motion |
| 8 | Dark Mode | `validate_design.py` | ≥ 3 colors, background < #333, WCAG AA |

---

## 3. Support files

| File | Role |
| :--- | :--- |
| `templates/design-md-template.md` | DESIGN.md template to fill in (§0 to §8 + checklist) |
| `templates/design-system.css` | CSS variables ready to be customized from the DESIGN.md |
| `templates/brand-kit.json` | Exportable brand kit structure |
| `references/design-md-spec-v2.md` | Detailed specification of the DESIGN.md format |
| `references/antipatterns-guide.md` | AI antipatterns guide — ❌ vs ✅ examples |
| `references/gsap-best-practices.md` | GSAP guide (Phase 3) |
| `.slop-ignore` | Anti-false-positive whitelist for `detect_ai_slop.py` |
| `data/*.csv` | UI/UX Pro Max data (styles, colors, typography...) |
| `data/stacks/*.csv` | Per-stack guidelines (React, Next.js, Vue, Svelte...) |
| `examples/manus-demo/` | Validated example — dev tool, Clean Tech + Neo-Brutalism style |
| `examples/dataflow-saas/` | Validated example — SaaS analytics, Data-Dense Dashboard style |
