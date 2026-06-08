# Web Design Enhancer Pro

**Éradiquer l'improvisation visuelle des IA — livrer des interfaces propres, précises, professionnelles.**

---

## Philosophie : Anti-"AI Slop"

Ce skill transforme n'importe quelle interface générée par une IA en un résultat de qualité professionnelle. Il impose une rigueur mécanique qui rend impossible la production de patterns "AI slop" — même avec un agent non supervisé.

**3 principes fondamentaux :**
- **Contrat avant code** — le DESIGN.md est validé mécaniquement avant qu'une seule ligne de code soit écrite
- **Vérifiable > subjectif** — chaque règle design est testable par un script Python
- **Références réelles > training data** — Phase 0 force l'ancrage sur des designs existants (Stripe, Linear, Vercel...)

---

## Architecture : 3 Piliers

```
Pilier 1 — getdesign.md           Pilier 2 — UI/UX Pro Max
(références visuelles réelles)    (intelligence sectorielle, 161 règles, 67 styles)
           ↓                                    ↓
                      DESIGN.md
                  (contrat de design)
                         ↓
           Pilier 3 — web-design-enhancer-pro
           (validation + implémentation + audit)
```

---

## Workflow en 5 Phases

### Phase 0 — Ancrage (obligatoire, bloquante)
```bash
# 1. Récupérer les références visuelles réelles
npx getdesign@latest add stripe

# 2. Interroger la base UI/UX Pro Max
python3 scripts/search.py "saas analytics dashboard" --design-system -p "MonProjet"

# 3. Vérifier que Phase 0 est prouvée
python3 scripts/check.py --gate 0
```

### Phase 1 — Contrat DESIGN.md
Remplir `DESIGN.md` avec les §0 à §10 (template : `templates/design-md-template.md`).
Sections validées : §0 Sources Phase 0, §1–§7 cœur, **§4 plages H1/P** auto-vérifiées, §8 Dark Mode (obligatoire si fond sombre), §9 Mobile (si app native), **§10 Three.js (si scène WebGL — voir `references/threejs-best-practices.md`)**.
```bash
python3 scripts/check.py --gate 1   # Point d'entrée canonique, invoque validate_design.py
```

### Phase 2 — Implémentation CSS/HTML
Mapper les tokens du DESIGN.md vers `globals.css` ou les variables CSS.

### Phase 3 — Animations GSAP
Orchestrer les entrées et effets de scroll selon `references/gsap-best-practices.md`.

### Phase 4 — Audit visuel Playwright
```bash
python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
```

### Phase 5 — Validation finale (gate bloquant)
```bash
python3 scripts/check.py --final --code ./src
# Séquence : detect_ai_slop → audit_spacing → validate_design → diff_design_vs_code
```

---

## Scripts disponibles

| Script | Usage | Rôle |
| :--- | :--- | :--- |
| `validate_design.py` | `DESIGN.md` | Valide les §0–8, WCAG AA, dark mode |
| `detect_ai_slop.py` | `--design` + `--code` | Score antipatterns IA (0–100, seuil 80) |
| `diff_design_vs_code.py` | `DESIGN.md --code ./src` | Divergences contrat ↔ implémentation |
| `audit_spacing.py` | `--path ./src` | Grille 8px sur le CSS/JSX réel |
| `visual_audit.py` | `--url localhost:3000` | Screenshots + audit Playwright 4 breakpoints |
| `check.py` | `--gate 0/1/final` | Orchestrateur de gates séquentiels |
| `search.py` | `"requête" --domain` | Recherche BM25 dans les CSV UI/UX Pro Max |

---

## Antipatterns détectés automatiquement

| Antipattern | Signal IA | Remède |
| :--- | :--- | :--- |
| Emojis décoratifs | ✨🚀💡 dans le code | Suppression radicale |
| Icônes Lucide génériques | sparkles, zap, star, bot, magic | Pack cohérent ou SVG custom |
| Gradients clichés | bleu→violet, rose→violet | Couleurs sémantiques solides |
| Badges statut non demandés | ● LIVE NOW, SYS_STATUS: ONLINE | Suppression ou justification §1 |
| Buzzwords vagues | premium, moderne, élégant | Descriptions précises et mesurables |
| Typographie uniforme | font-size: 16px partout | Hiérarchie §4 respectée |
| Hover excessif | translateY(-8px), ombre 32px | ≤ -4px, ombre discrète |
| Dark mode improvisé | couleurs inventées à la génération | Section §8 obligatoire |
| Thèmes interdits | glassmorphism, typewriter effect | Détecté et bloqué par validate_design |
| Three.js antipatterns | geometry dans animate(), renderer dans useEffect, pixel ratio non capé | Bloqué par detect_ai_slop sur .js/.ts/.jsx/.tsx |

---

## Structure du projet

```
web-design-enhancer-pro/
├── SKILL.md                          # Documentation principale (workflow complet)
├── README.md                         # Ce fichier
├── requirements.txt                  # Dépendances Python
├── .slop-ignore                      # Whitelist anti-faux positifs
├── data/                             # CSV UI/UX Pro Max (styles, couleurs, typo...)
│   └── stacks/                       # Guidelines par stack (16 frameworks)
├── scripts/
│   ├── validate_design.py            # Validateur DESIGN.md (§0–8, WCAG, dark mode)
│   ├── detect_ai_slop.py             # Détecteur antipatterns IA (score 0–100)
│   ├── diff_design_vs_code.py        # Diff DESIGN.md ↔ code réel
│   ├── audit_spacing.py              # Audit grille 8px sur CSS/JSX
│   ├── visual_audit.py               # Audit Playwright 4 breakpoints
│   ├── check.py                      # Orchestrateur de gates
│   ├── search.py                     # Moteur BM25 UI/UX Pro Max
│   ├── core.py                       # Moteur de recherche BM25 (dépendance search.py)
│   └── design_system.py              # Générateur de design system (dépendance search.py)
├── references/
│   ├── design-md-spec-v2.md          # Spécification DESIGN.md v3 (§0–8 détaillés)
│   ├── api_reference.md              # Référence technique complète
│   ├── antipatterns-guide.md         # Guide antipatterns ❌ vs ✅
│   └── gsap-best-practices.md        # Guide GSAP (Phase 3)
├── templates/
│   ├── design-md-template.md         # Template DESIGN.md §0–8 + checklist
│   ├── design-system.css             # Variables CSS prêtes à personnaliser
│   └── brand-kit.json                # Structure brand kit exportable
└── examples/
    ├── manus-demo/DESIGN.md          # Exemple validé — dev tool, Neo-Brutalism
    └── dataflow-saas/DESIGN.md       # Exemple validé — SaaS analytics, Dense Dashboard
```

---

## Checklist avant livraison

- [ ] `DESIGN.md` §0–8 complet, `check.py --gate 0` passé
- [ ] `validate_design.py` : 0 erreur
- [ ] `detect_ai_slop.py` : score ≥ 80/100
- [ ] `diff_design_vs_code.py` : 0 divergence
- [ ] `audit_spacing.py` : 0 violation grille 8px
- [ ] `visual_audit.py` : screenshots validés sur 4 breakpoints
- [ ] Section §8 Dark Mode présente avec fond < #333 et WCAG AA
- [ ] `prefers-reduced-motion` dans le code CSS/JS
- [ ] Zéro emoji décoratif, zéro gradient cliché, zéro icône générique non justifiée

---

*Conçu pour transformer le code IA en design d'exception.*
