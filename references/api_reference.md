# Référence Technique — Web Design Enhancer

Spécifications techniques complètes des scripts et formats du skill.

---

## 1. Scripts de Validation

### `validate_design.py`

Valide le fichier `DESIGN.md` contre le contrat complet du skill.

```bash
python3 scripts/validate_design.py DESIGN.md
python3 scripts/validate_design.py DESIGN.md --strict
```

**Règles vérifiées :**
- Section `## 0. Sources Phase 0` présente et sans placeholders
- Sections obligatoires présentes (§1 à §8 inclus)
- Max 2 polices — détectées via `**NomPolice** (Display)` ou `Font: NomPolice`
- Espacements multiples de 8px dans §5
- 4 à 8 couleurs hex dans §2 avec rôles sémantiques
- Contraste WCAG AA : Texte/Fond ≥ 4.5:1, Primaire/Fond ≥ 3.0:1
- Animations ≤ 400ms dans §7, mention de `prefers-reduced-motion`
- Max 3 variantes de boutons dans §6
- Section `## 8. Dark Mode` présente avec ≥ 3 couleurs, fond < #333 (luminosité < 9%), rôles `fond`, `texte`, `surface`
- Thèmes interdits absents (glassmorphism, dark cyberpunk, particle background, typewriter effect, glow cursor, neon glow, grid background)
- Buzzwords absents (premium, moderne, élégant...)

**Codes de sortie :** `0` = valide, `1` = erreurs bloquantes

---

### `detect_ai_slop.py`

Détecte les antipatterns IA dans le DESIGN.md et/ou le code source.

```bash
python3 scripts/detect_ai_slop.py --design DESIGN.md --code ./src
python3 scripts/detect_ai_slop.py --design DESIGN.md
```

**Détections :**
- Icônes Lucide génériques (sparkles, zap, star, bot, magic...)
- Gradients clichés (bleu→violet, rose→violet, cyan→bleu)
- Buzzwords vagues (premium, moderne, élégant, futuriste...)
- Badges statut non demandés (● LIVE NOW, SYS_STATUS: ONLINE...)
- Polices génériques (Arial, Helvetica, Georgia, Verdana...)
- Composants shadcn/ui laissés par défaut (variant="default" non personnalisé)
- Logos placeholders (logo-placeholder, your-logo, brandname)

**Score :** Démarre à 100, pénalités par infraction. Seuil : ≥ 80 pour validation.

**Whitelist :** Créer `.slop-ignore` à la racine pour exempter les faux positifs.
Chaque entrée doit avoir un commentaire justificatif — sans commentaire, la règle est ignorée.

```ini
[icons]
search          # barre de recherche fonctionnelle dans la nav

[buzzwords]
premium         # nom du plan tarifaire (pas un adjectif vague)

[files]
scripts/        # scripts internes — faux positifs connus
```

---

### `diff_design_vs_code.py`

Compare le contrat DESIGN.md contre le code CSS/JS/TSX réellement implémenté.

```bash
python3 scripts/diff_design_vs_code.py DESIGN.md --code ./src
python3 scripts/diff_design_vs_code.py DESIGN.md --file index.css
python3 scripts/diff_design_vs_code.py DESIGN.md --code ./src --strict
```

**Comparaisons effectuées :**
- Couleurs §2 présentes dans le code (exact + détection de dérive proche via distance RGB)
- Polices §3 chargées dans les font-family, imports Google Fonts, fontsource
- Durées d'animation dans le code (CSS transitions, `@keyframes`, GSAP `duration:`) vs max §7
- Variables CSS `--custom` référençant les hex du DESIGN.md (`--strict` seulement)

**Codes de sortie :** `0` = conforme, `1` = divergences détectées

---

### `audit_spacing.py`

Analyse les fichiers CSS/JS/TSX pour détecter les espacements hors grille 8px.

```bash
python3 scripts/audit_spacing.py --path ./src
python3 scripts/audit_spacing.py --file index.css
python3 scripts/audit_spacing.py --path ./src --output report.json
```

**Propriétés auditées :** `padding`, `margin`, `gap`, `border-radius`, `width`, `height`
**Règle :** Toute valeur `px` doit être multiple de 8 (exception : 4px pour micro-espacements).

---

### `visual_audit.py`

Audit visuel Playwright sur le rendu réel du site — 4 breakpoints.

```bash
python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
```

**Breakpoints :** 375px (mobile), 768px (tablet), 1280px (desktop), 1920px (wide)

**Audits effectués :**
- Screenshots PNG par breakpoint
- Polices calculées (computed styles DOM)
- Espacements réels (padding/margin non-multiples de 8px)
- Artefacts IA visuels (emojis, logos placeholders, SVG suspects)

**Prérequis :** `pip install playwright --break-system-packages && playwright install chromium`

**Sortie :** `audit-results/audit_report.json` + 4 fichiers PNG

---

### `check.py`

Orchestrateur de gates — transforme les phases du SKILL.md en validations mécaniques séquentielles.

```bash
python3 scripts/check.py --gate 0           # Phase 0 exécutée ?
python3 scripts/check.py --gate 1           # DESIGN.md valide ?
python3 scripts/check.py --final            # Validation complète avant livraison
python3 scripts/check.py --final --code ./src
```

**Séquence des gates :**

| Gate | Condition | Bloque si |
| :--- | :--- | :--- |
| 0 | `design-system-output*.md` + `getdesign-*.md` + `DESIGN.md` avec §0 | Fichiers manquants ou placeholders non remplacés |
| 1 | `validate_design.py` sans erreur | Gate 0 non passé ou DESIGN.md invalide |
| Final | 4 scripts en séquence | Gate 1 non passé ou l'un des scripts échoue |

**Gate Final — 4 étapes :**
1. `detect_ai_slop.py` — antipatterns IA
2. `audit_spacing.py` — grille 8px
3. `validate_design.py` — contrat DESIGN.md
4. `diff_design_vs_code.py` — divergences DESIGN.md ↔ code (si `--code` fourni)

**Log persistant :** `.phase-log.json` à la racine — trace les gates passés.

---

### `search.py`

Moteur de recherche BM25 dans les données UI/UX Pro Max (CSV).

```bash
python3 scripts/search.py "saas analytics dashboard" --design-system -p "MonProjet"
python3 scripts/search.py "fintech banking" --domain color
python3 scripts/search.py "button hover" --stack nextjs
```

**Domaines disponibles :** `style`, `color`, `chart`, `landing`, `product`, `ux`, `typography`, `icons`, `react`, `web`, `google-fonts`

**Stacks disponibles :** `react`, `nextjs`, `vue`, `svelte`, `astro`, `swiftui`, `react-native`, `flutter`, `nuxtjs`, `shadcn`, `html-tailwind`, `angular`, `laravel`, `threejs`, `jetpack-compose`, `nuxt-ui`

---

## 2. Format DESIGN.md (v3)

Le DESIGN.md est le contrat de vérité unique. Placé à la racine du projet, lu par `validate_design.py` avant tout code.

**Sections obligatoires :**

| # | Section | Validée par | Règle clé |
| :--- | :--- | :--- | :--- |
| 0 | Sources Phase 0 | `check.py --gate 0` | getdesign + UI/UX Pro Max prouvés |
| 1 | Thème Visuel & Concept | `validate_design.py` | Pas de thème interdit |
| 2 | Palette de Couleurs | `validate_design.py` | 4–8 hex, rôles sémantiques, WCAG AA |
| 3 | Typographie | `validate_design.py` | Max 2 polices, format `**NomPolice** (Display)` |
| 4 | Hiérarchie Typographique | — | H1 à Small avec px / weight / line-height |
| 5 | Espacement et Grille | `validate_design.py` + `audit_spacing.py` | Multiples de 8px, grille mentionnée |
| 6 | Composants et États | `validate_design.py` | Max 3 variantes de boutons |
| 7 | Motion et Animations | `validate_design.py` | ≤ 400ms, prefers-reduced-motion |
| 8 | Dark Mode | `validate_design.py` | ≥ 3 couleurs, fond < #333, WCAG AA |

---

## 3. Fichiers de support

| Fichier | Rôle |
| :--- | :--- |
| `templates/design-md-template.md` | Template DESIGN.md à remplir (§0 à §8 + checklist) |
| `templates/design-system.css` | Variables CSS prêtes à personnaliser depuis le DESIGN.md |
| `templates/brand-kit.json` | Structure brand kit exportable |
| `references/design-md-spec-v2.md` | Spécification détaillée du format DESIGN.md |
| `references/antipatterns-guide.md` | Guide des antipatterns IA — exemples ❌ vs ✅ |
| `references/gsap-best-practices.md` | Guide GSAP (Phase 3) |
| `.slop-ignore` | Whitelist anti-faux positifs pour `detect_ai_slop.py` |
| `data/*.csv` | Données UI/UX Pro Max (styles, couleurs, typographie...) |
| `data/stacks/*.csv` | Guidelines par stack (React, Next.js, Vue, Svelte...) |
| `examples/manus-demo/` | Exemple validé — outil dev, style Clean Tech + Neo-Brutalism |
| `examples/dataflow-saas/` | Exemple validé — SaaS analytics, style Data-Dense Dashboard |
