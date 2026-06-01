# Web Design Enhancer v2.3

**Éradiquez l'improvisation visuelle de l'IA et livrez des interfaces premium, épurées et professionnelles.**

## Philosophie : Anti-"Odeur d'IA"

Ce skill transforme n'importe quel site générique en une expérience visuelle haut de gamme. Il impose une rigueur absolue pour éviter les tics de conception des IA (emojis superflus, espacements aléatoires, composants génériques).

### Principes d'Hygiène Visuelle Stricte
- **Moins mais mieux** : Élimination de toute fioriture sans fonction claire.
- **Grille de 8px stricte** : Multiples de 8 pour tous les espacements (Tailwind: `p-2`, `m-8`, etc.).
- **Logos textuels** : Utilisation de texte stylisé haut de gamme si aucun logo n'est fourni.
- **Auto-correction visuelle** : Utilisation obligatoire de Playwright pour chasser "l'odeur d'IA".

## Workflow d'Amélioration

### 1. Audit et Définition (Le "Cerveau")
Définir le système de design dans `DESIGN.md`.
- Mapper les variables sémantiques vers **shadcn/ui**.
- Justifier chaque choix technique.

### 2. Implémentation Structurelle (Le "Corps")
- Utiliser exclusivement les primitives **shadcn/ui**.
- Configurer `globals.css` via les variables du `DESIGN.md`.

### 3. Dynamisme avec GSAP (L' "Âme")
- Orchestration des entrées et effets au scroll.
- Respecter les timings stricts de `gsap-best-practices.md`.

### 4. Inspection Visuelle (Les "Yeux" via Playwright)
- Audit obligatoire du rendu réel.
- Correction immédiate des défauts de géométrie ou d'artefacts IA.

## Chasse à l'Odeur d'IA (Antipatterns)

| Antipattern | "Odeur d'IA" | Remède Professionnel |
|------------|-----------|-----------|
| **Artefacts** | Emojis, stickers, sparkles | Suppression radicale |
| **Logos inventés** | Placeholders graphiques bizarres | Logos textuels stylisés |
| **Géométrie bancale** | Espacements asymétriques | Grille 8px stricte |
| **shadcn/ui générique** | Look "out of the box" | Personnalisation via variables CSS |
| **Icônes génériques** | Lucide random sans contexte | Pack cohérent ou custom SVG |
| **Gradients clichés** | Dégradés bleu/violet sans but | Couleurs sémantiques solides |

## Structure du Skill

```
web-design-enhancer/
├── SKILL-v2.md                      # Documentation principale
├── README.md                         # Ce fichier
├── references/
│   ├── design-md-spec-v2.md        # Spécification DESIGN.md (Format shadcn/ui)
│   ├── gsap-best-practices.md      # Guide GSAP
│   └── api_reference.md            # Référence technique
├── scripts/
│   ├── detect_ai_slop.py           # Détecteur d'antipatterns
│   └── visual_audit.py             # Audit visuel (Playwright)
└── templates/
    ├── design-system.css           # Template variables CSS
    └── design-md-template.md       # Template DESIGN.md
```

## Checklist Avant Livraison

- [ ] `DESIGN.md` créé et mappé sur shadcn/ui.
- [ ] Grille de 8px respectée sur tout le site.
- [ ] Zéro emoji ou sticker "décoratif".
- [ ] Audit visuel Playwright passé avec succès.
- [ ] Animations GSAP fluides et intentionnelles.

---
**Créé pour transformer le code IA en design d'exception.**
