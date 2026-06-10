# web-design-enhancer-pro

**Élimine les mauvaises habitudes des IA en design web.** Valide, bloque et corrige automatiquement les outputs génériques des modèles avant livraison.

---

## Ce que ça fait

Chaque IA génère par défaut le même site : hero sombre + gradient bleu→violet + 3 colonnes de cartes + testimonials + CTA bleu. Ce skill rend ça **impossible à livrer**.

Il force l'IA à :
1. **Choisir un style visuel** adapté au projet (pas le template par défaut)
2. **Valider le design** contre un contrat DESIGN.md
3. **Bloquer la livraison** si le résultat ressemble à un template générique

---

## Utilisation — ce que tu fais

Tu utilises l'IA normalement :

```
"Crée-moi un site pour mon agence de cosmétiques premium"
```

Le skill oblige l'IA à répondre d'abord :

```
Archétype sélectionné : §3 Luxury/Restrained
Raison : cosmétiques premium → whitespace, typographie fine,
palette ivoire + noir, pas de gradient bleu/violet.
```

Puis elle code avec ce style précis. À la fin, elle run les validations automatiques — et si le résultat ressemble trop à un template générique, c'est **bloqué**.

**Tu n'as rien à faire de plus.** Le skill gère tout.

---

## Même brief, styles différents

Pour illustrer : un brief "app de finances personnelles" donne des résultats complètement différents selon l'archétype.

| Archétype | Rendu | Ressemble à |
|---|---|---|
| *(sans skill — défaut IA)* | Dark + bleu-500 + gradient + 3 colonnes | Identique à 1000 autres fintech |
| **§6 Technical/Monochrome** | Zinc/monochrome, dense, nombres tabulaires | Linear, Vercel |
| **§3 Luxury/Restrained** | Ivoire, typo fine, 0 couleur vive | Cabinet privé, Aesop |
| **§8 Data/Dashboard** | Fond sombre, couleur sémantique, charts first | Grafana propre, Amplitude |

### Exemple de rendu : FC Méridien (Archétype §7 Playful/Expressive)

Voici le résultat généré avec ce skill pour un club de football (zéro template générique IA, typographie display forte, palette sur-mesure) :

![Hero Section](assets/football-hero.png)

![Match Section](assets/football-match.png)

![Players Section](assets/football-players.png)

---

## Les 10 archétypes

| # | Nom | Pour quel projet |
|---|---|---|
| §1 | Swiss/Typographic | Agence, culture, print-to-web |
| §2 | Editorial/Magazine | Média, blog premium, journal |
| §3 | Luxury/Restrained | Mode, cosmétiques, premium B2C |
| §4 | Brutalist/Raw | Arte, niches, culturel, avant-garde |
| §5 | Organic/Hand-crafted | Bien-être, artisan, nourriture, nature |
| §6 | Technical/Monochrome | SaaS dev, API, CLI, outils B2B |
| §7 | Playful/Expressive | App grand public, éducation, communauté |
| §8 | Data/Dashboard | Analytics, monitoring, BI, fintech |
| §9 | Retro/Nostalgic | Gaming, niche, culture, expérimental |
| §10 | Material/Tactile | App OS, design system, productivité |

→ Détail complet : [`references/design-archetypes.md`](references/design-archetypes.md)

---

## Les 6 gates de validation automatique

Avant chaque livraison, l'IA run :

```bash
python3 scripts/check.py --final --code ./src
```

| Gate | Outil | Ce qu'il bloque |
|---|---|---|
| 1 | `detect_ai_slop.py` | Emojis, fausses stats, testimonials inventés, badges système, glassmorphism, gradient bleu/violet... |
| 2 | `audit_spacing.py` | Espacements non-multiples de 8px |
| 3 | `validate_design.py` | Contrastes WCAG AA, typographie hors-norme, DESIGN.md incomplet |
| 4 | `diff_design_vs_code.py` | Couleurs/fonts/animations qui dévient du DESIGN.md |
| 5 | `audit_accessibility.py` | `<img>` sans alt, `<button>` sans type, inputs sans label, viewport meta manquant... |
| 6 | `audit_style_uniqueness.py` | **Score > 65/100 = livraison bloquée** — design trop proche du template générique |

---

## Les patterns interdits (§0b)

L'IA ne peut **jamais** produire ces éléments, quel que soit le projet :

| Code | Pattern | Exemple interdit |
|---|---|---|
| G1 | Badges système | `SYS_STATUS: ONLINE`, `NODE_STATUS` |
| G7 | Animations non demandées | `@keyframes float`, `@keyframes pulse` |
| A1 | Emojis dans l'UI | `✨ Nos fonctionnalités`, `🚀 Démarrer` |
| A3 | Section "trusted by" inventée | Logos de clients fictifs |
| A4 | Testimonials hardcodés | `<blockquote>` avec "Sarah, CEO" fictive |
| B7 | Gradient bleu→violet sur hero | `linear-gradient(135deg, #3B82F6, #8B5CF6)` |
| B8 | Glassmorphism sur tout | `backdrop-filter: blur()` sur 3+ éléments |
| C7 | `font-size` en px sur `body` | `body { font-size: 16px }` — casse le zoom WCAG |
| H1 | Viewport meta manquant | `<head>` sans `<meta name="viewport">` |

→ Liste complète : [`SKILL.md §0b`](SKILL.md)

---

## Structure du projet

```
web-design-enhancer-pro/
├── SKILL.md                          # Instructions complètes du skill
├── scripts/
│   ├── check.py                      # Orchestrateur des 6 gates
│   ├── detect_ai_slop.py             # Détecteur de patterns IA (G/A/B/C/D/H)
│   ├── audit_accessibility.py        # WCAG 2.1 AA
│   ├── audit_spacing.py              # Grille 8px
│   ├── audit_style_uniqueness.py     # Détecteur Generic AI Template (T1–T12)
│   ├── validate_design.py            # Contrat DESIGN.md
│   ├── diff_design_vs_code.py        # Drift code vs DESIGN.md
│   └── visual_audit.py              # Audit Playwright 4 breakpoints
├── references/
│   ├── design-archetypes.md          # Les 10 archétypes — tokens CSS complets
│   ├── gsap-best-practices.md        # Animations GSAP
│   └── threejs-best-practices.md     # Scènes WebGL
├── templates/
│   └── design-md-template.md         # Squelette DESIGN.md
└── tests/
    ├── test_audit_accessibility.py   # 33 tests WCAG
    ├── test_audit_style_uniqueness.py # 35 tests anti-template
    └── test_detect_domain.py         # 57 tests détection domaine
```

---

## Lancer les tests

```bash
py -m pytest tests/ -v
# 125 tests — doit afficher 125 passed
```