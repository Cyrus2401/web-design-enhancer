# DESIGN.md — Manus Demo

Contrat de design pour **Manus**, un outil d'orchestration d'agents IA.
Validé par `python3 scripts/validate_design.py DESIGN.md` : 0 erreur.

---

## 0. Sources Phase 0

- **Brand utilisée :** Vercel
- **Commande exécutée :** `npx getdesign@latest add vercel`
- **Requête exécutée :** `python3 scripts/search.py "ai agent orchestration developer tool" --design-system -p "Manus"`
- **Style retenu :** Clean Tech + Neo-Brutalism
- **Justification :** Outil développeur orienté agent IA. Vercel apporte la précision extrême (radius 0, bords vifs, noir/blanc absolu). Neo-Brutalism pour l'identité forte. Zéro ornement — chaque pixel a une fonction.

---

## 1. Thème Visuel & Concept

- **Concept :** Minimalisme tech haute précision — interfaces axées sur la performance, contrastes absolus, aucune fioriture.
- **Mots-clés :** Géométrique, contrasté, fonctionnel, terminal, précis.
- **Références :** Vercel (noir/blanc absolu, typographie fine), Linear (densité, tokens serrés).

---

## 2. Palette de Couleurs

| Rôle | Hex | Utilisation |
| :--- | :--- | :--- |
| Primaire | #000000 | Boutons principaux, texte fort, bordures |
| Secondaire | #171717 | Surfaces sombres, nav, sidebar |
| Fond | #FFFFFF | Arrière-plan principal |
| Texte | #0A0A0A | Corps de texte, headings |
| Muet | #737373 | Labels secondaires, placeholders |
| Accent | #0066FF | Liens actifs, focus, highlights |
| Succès | #10B981 | Confirmations, états OK |
| Danger | #EF4444 | Erreurs, actions destructives |

Contraste WCAG AA — Texte sur Fond : 20.3:1 (min 4.5:1). Accent sur Fond : 4.6:1 (min 3.0:1).

---

## 3. Typographie

- **Geist Mono** (Display, Titres, UI labels) — monospace technique, identité terminal.
- **Geist Sans** (Body, corps de texte) — lisible, neutre, même famille.

```css
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600;700&family=Geist:wght@400;500;600&display=swap');
```

---

## 4. Hiérarchie Typographique

- **H1 :** 40px / 600 / 1.1
- **H2 :** 28px / 600 / 1.2
- **H3 :** 18px / 500 / 1.3
- **P :** 15px / 400 / 1.6
- **Small :** 12px / 400 / 1.5
- **Mono (IDs, logs, code) :** 13px / 400 / 1.4

---

## 5. Espacement et Grille

- **Base de la grille :** 8px
- **Padding section vertical :** 64px
- **Padding section horizontal :** 24px
- **Padding card interne :** 16px
- **Gap entre éléments :** 8px, 16px, 24px
- **Hauteur ligne de log :** 32px
- **Radius :** 0px (bords vifs — identité tech précis)

---

## 6. Composants et États

### Boutons

- **Primaire (Normal) :** Fond #000000, texte #FFFFFF, padding 8px 16px, font-weight 500, radius 0
- **Primaire (Hover) :** Fond #171717, transition 150ms ease-out
- **Secondaire (Normal) :** Fond #FFFFFF, bordure 1px solid #000000, texte #000000, radius 0
- **Ghost (Normal) :** Fond transparent, texte #737373, sans bordure

### Section Contact / CTA
- **Titre :** H2 visible (28–32px)
- **Sous-titre :** Texte descriptif, 1–2 lignes
- **Action :** Bouton primaire ou champ email + CTA
- **Padding vertical max :** 96px (jamais plus — densité minimale obligatoire)

### Comportement grille sur nombre impair de cartes
- **Stratégie :** Last card en `grid-column: 1 / -1` (full-width) si N%3 ≠ 0
- **Alignement :** Centré sur la ligne incomplète

### Cartes (Cards)

- **Structure :** Fond #FFFFFF, bordure 1px solid #E5E5E5, radius 0
- **Padding Interne :** 16px
- **Ombre :** aucune (bords vifs suffisent)

### Console / Logs

- **Fond :** #0A0A0A
- **Texte :** #E5E5E5 (monospace)
- **Accent success :** #10B981
- **Accent error :** #EF4444
- **Prompt :** #0066FF

---

## 7. Motion et Animations

- **Transitions générales :** 150ms ease-out
- **Hover états :** 100ms ease-in-out
- **Entrées stagger :** duration 300ms, stagger 40ms, ease power2.out
- **Logs stream :** apparition ligne par ligne, 50ms entre chaque
- **Accessibilité :** `prefers-reduced-motion` obligatoire.

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

| Rôle | Hex | Équivalent Light |
| :--- | :--- | :--- |
| Fond | #0A0A0A | #FFFFFF |
| Surface | #171717 | #F5F5F5 |
| Texte | #FAFAFA | #0A0A0A |
| Texte secondaire | #A3A3A3 | #737373 |
| Bordure | #262626 | #E5E5E5 |
| Primaire | #FFFFFF | #000000 |
| Accent | #3B82F6 | #0066FF |

**Règles dark mode :**
- Fond #0A0A0A : luminosité relative ~0.002 — largement sous le seuil 9%
- Texte #FAFAFA sur Fond #0A0A0A : 19.8:1 — conforme WCAG AAA
- Accent #3B82F6 adapté pour contraste suffisant sur fond sombre
- Pas de toggle JS : `prefers-color-scheme: dark` uniquement

---

## ✅ Checklist de Validation Anti-Slop

- [x] **DESIGN.md** : Complet, Phase 0 documentée.
- [x] **Polices** : 2 polices (Geist Mono + Geist Sans — même famille, cohérence garantie).
- [x] **Espacements** : Tous multiples de 8px (8, 16, 24, 32, 40, 48, 64).
- [x] **Rayons** : 0px — bords vifs intentionnels, identité Neo-Brutalism.
- [x] **Icônes** : Mono uniquement pour fonctions justifiées dans la console.
- [x] **Gradients** : Aucun gradient décoratif.
- [x] **Artefacts** : Aucun emoji, aucun sticker.
- [x] **Logo** : Texte stylisé "MANUS" en Geist Mono 600.
- [x] **Structure** : Terminal-first layout — pas une landing générique.
- [x] **Texte** : Descriptions précises, zéro buzzword.
- [x] **Boutons** : 3 variantes (Primaire, Secondaire, Ghost).
- [x] **Couleurs** : 8 couleurs avec rôles sémantiques.
- [x] **Animations** : Toutes ≤ 400ms. prefers-reduced-motion documenté.
- [x] **WCAG AA** : 20.3:1 Texte/Fond — largement conforme.
- [x] **Dark Mode** : Section §8 complète, fond #0A0A0A, 7 tokens inversés.
