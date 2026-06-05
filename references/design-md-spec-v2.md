# Spécification DESIGN.md — Format v3

Le fichier `DESIGN.md` est le **contrat de design unique** du projet. Il est lu par les agents IA avant toute implémentation, et validé mécaniquement par `validate_design.py` avant tout code.

> **Règle fondamentale :** Si le DESIGN.md n'est pas valide, aucun code ne doit être écrit.
> `check.py --gate 1` bloque l'avancement si `validate_design.py` retourne une erreur.

---

## Philosophie

Le DESIGN.md n'est pas un document de référence passif — c'est un **contrat d'exécution**.
Chaque section correspond à une règle mécanique vérifiable automatiquement.
L'objectif : rendre impossible la production de "AI slop" même avec un agent non supervisé.

**3 principes :**
1. **Explicite > implicite** — tout ce qui n'est pas écrit sera inventé par l'IA
2. **Vérifiable > subjectif** — chaque règle doit pouvoir être testée par un script
3. **Minimal > exhaustif** — un contrat trop long n'est pas lu

---

## Structure complète (§0 à §8)

### § 0 — Sources Phase 0

**Obligatoire.** Prouve que le design est ancré dans des références réelles, pas dans le training data de l'IA.

```markdown
## 0. Sources Phase 0

- **Brand utilisée :** [NomBrand]
- **Commande exécutée :** `npx getdesign@latest add [brand]`
- **Requête exécutée :** `python3 scripts/search.py "[requête]" --design-system -p "[Projet]"`
- **Style retenu :** [Style]
- **Justification :** [Pourquoi ce style pour ce projet]
```

**Validé par :** `check.py --gate 0`
**Bloque si :** fichiers `getdesign-*.md` ou `design-system-output*.md` manquants, ou placeholders non remplacés (`[NomBrand]`, `TODO`, `à remplir`).

---

### § 1 — Thème Visuel & Concept

**Obligatoire.** Définit l'intention — le "pourquoi" du design.

```markdown
## 1. Thème Visuel & Concept

- **Concept :** [Description précise de l'identité visuelle]
- **Mots-clés :** [3–5 mots, pas de buzzwords génériques]
- **Références :** [Sites/produits réels, avec justification]
```

**Règles :**
- Les thèmes suivants sont **interdits** (détectés et bloquants) :
  `glassmorphism`, `dark cyberpunk`, `particle background`, `typewriter effect`, `glow cursor`, `neon glow`, `grid background`, `aurora borealis`
- Les mots-clés génériques sont **interdits** : `moderne`, `élégant`, `premium`, `futuriste`, `immersif`
- Les références doivent être des sites réels — pas des adjectifs abstraits

**Validé par :** `validate_design.py` → `_validate_theme_originality()`

---

### § 2 — Palette de Couleurs

**Obligatoire.** Le seul endroit où les hex sont définis.

```markdown
## 2. Palette de Couleurs

| Rôle | Hex | Utilisation |
| :--- | :--- | :--- |
| Primaire   | #XXXXXX | [Usage précis] |
| Secondaire | #XXXXXX | [Usage précis] |
| Fond       | #XXXXXX | Arrière-plan principal |
| Texte      | #XXXXXX | Corps de texte principal |
| Accent     | #XXXXXX | [Usage précis] |
| Succès     | #XXXXXX | [Usage précis] |
| Attention  | #XXXXXX | [Usage précis] |
| Danger     | #XXXXXX | Actions destructives, erreurs |
```

**Règles :**
- **4 à 8 hex** dans cette section — pas plus (les hex dans §6, §7, §8 ne sont pas comptés)
- Ne pas écrire les hex dans le texte WCAG de cette section — les calculer séparément
- Rôles `Fond` et `Texte` **obligatoires** — utilisés pour le calcul WCAG automatique
- **WCAG AA obligatoire :** Texte/Fond ≥ 4.5:1, Primaire/Fond ≥ 3.0:1

**Validé par :** `validate_design.py` → `_validate_colors()` + `_validate_wcag_contrast()`

**Calcul de contraste rapide :**
```
L = 0.2126×R + 0.7152×G + 0.0722×B  (valeurs 0–1 linearisées)
Contraste = (L_clair + 0.05) / (L_sombre + 0.05)
```

---

### § 3 — Typographie

**Obligatoire.** Max 2 familles de polices.

```markdown
## 3. Typographie

- **NomPolice** (Display) — [justification du choix]
- **NomPolice** (Body) — [justification du choix]

```css
@import url('https://fonts.googleapis.com/...');
```
```

**Règles :**
- **Exactement 1 ou 2 polices** — jamais plus
- Format obligatoire : `**NomPolice** (Display)` ou `**NomPolice** (Body)`
  → Ce pattern exact est celui que `validate_design.py` détecte
- Si une seule police : variation de poids pour la hiérarchie (300/400/600/700)
- Polices système autorisées : `Inter`, `system-ui`, `-apple-system` (pas besoin d'import)

**Validé par :** `validate_design.py` → `_validate_typography()`

---

### § 4 — Hiérarchie Typographique

**Obligatoire.** Définit les tailles exactes — supprime toute ambiguïté pour l'IA.

```markdown
## 4. Hiérarchie Typographique

- **H1 :** [px] / [weight] / [line-height]
- **H2 :** [px] / [weight] / [line-height]
- **H3 :** [px] / [weight] / [line-height]
- **P :**  [px] / [weight] / [line-height]
- **Small :** [px] / [weight] / [line-height]
```

**Règles :**
- H1 entre 28px et 80px
- P entre 13px et 18px
- Small entre 11px et 14px
- Pas de font-size à 16px pour tout — c'est le signal d'une hiérarchie non pensée

**Non validé automatiquement** — vérification humaine.

---

### § 5 — Espacement et Grille

**Obligatoire.** Définit la grille de base et tous les espacements.

```markdown
## 5. Espacement et Grille

- **Base de la grille :** 8px
- **[Padding/Gap/Hauteur] :** [valeur]px
- **Radius :** [valeur]px
```

**Règles :**
- **Toutes les valeurs en px doivent être multiples de 8** (exception : 4px pour micro-espacements)
- `audit_spacing.py` scanne le code CSS/JSX et signale les valeurs non conformes
- Le radius 0px est autorisé (style Neo-Brutalism)
- Mentionner explicitement "Base de la grille : 8px" — `validate_design.py` le cherche

**Validé par :** `validate_design.py` → `_validate_spacing()` + `audit_spacing.py` sur le code

---

### § 6 — Composants et États

**Obligatoire.** Définit les composants UI et tous leurs états.

```markdown
## 6. Composants et États

### Boutons
- **Primaire (Normal) :** [description]
- **Primaire (Hover) :** [description]
- **Secondaire (Normal) :** [description]
- **Ghost (Normal) :** [description]

### Cartes (Cards)
- **Structure :** [description]
- **Padding Interne :** [valeur]px
- **Ombre :** [valeur ou "aucune"]
```

**Règles :**
- **Maximum 3 variantes de boutons** dans cette section
- Chaque état (normal, hover, disabled) doit être documenté
- Les couleurs dans §6 utilisent les hex définis en §2 — pas de nouvelles couleurs

**Validé par :** `validate_design.py` → `_validate_components()`

---

### § 7 — Motion et Animations

**Obligatoire.** Définit le comportement dynamique.

```markdown
## 7. Motion et Animations

- **Transitions générales :** [durée]ms ease-out
- **Hover états :** [durée]ms ease-in-out
- **Entrées stagger :** duration [durée]ms, stagger [durée]ms
- **Accessibilité :** `prefers-reduced-motion` obligatoire.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```
```

**Règles :**
- **Toutes les durées ≤ 400ms** — au-delà c'est perçu comme lent
- Exception documentée dans §1 si une animation longue est intentionnelle (ex: gradient mesh ≤30s)
- `prefers-reduced-motion` doit être mentionné explicitement dans §7
- `diff_design_vs_code.py` scanne le code réel et signale les durées dépassant le max de §7

**Validé par :** `validate_design.py` → `_validate_animations()` + `diff_design_vs_code.py`

---

### § 8 — Dark Mode

**Obligatoire depuis v3.** Le dark mode improvisé est la principale source de régression post-livraison.

```markdown
## 8. Dark Mode

| Rôle | Hex | Équivalent Light |
| :--- | :--- | :--- |
| Fond       | #XXXXXX | #XXXXXX |
| Surface    | #XXXXXX | #XXXXXX |
| Texte      | #XXXXXX | #XXXXXX |
| Texte secondaire | #XXXXXX | #XXXXXX |
| Bordure    | #XXXXXX | #XXXXXX |
| Primaire   | #XXXXXX | #XXXXXX |
| Accent     | #XXXXXX | #XXXXXX |

**Règles dark mode :**
- [Vérification luminosité fond]
- [Vérification contraste texte/fond]
- [Stratégie : prefers-color-scheme vs toggle JS]
```

**Règles :**
- **≥ 3 couleurs** dans le tableau dark mode
- Rôles `fond`, `texte`, `surface` **obligatoires**
- **Fond dark : luminosité relative < 9%** — soit approximativement < #333333
  Exemples conformes : `#0A0A0A`, `#0F172A`, `#111827`, `#1C1C1E`
  Exemples non conformes : `#4A4A4A`, `#555555`, `#666666`
- Texte dark sur fond dark ≥ 4.5:1 WCAG AA
- Recommandé : `prefers-color-scheme: dark` uniquement — pas de toggle JS non demandé

**Validé par :** `validate_design.py` → `_validate_dark_mode()`

---


---

### § 9 — Mobile

**Optionnel pour les projets web-only. Obligatoire dès qu'une app native ou hybrid est dans le scope.**

`validate_design.py` valide automatiquement cette section si elle est présente.

**Règles vérifiées automatiquement :**

| Règle | Bloquant | Script |
| :--- | :--- | :--- |
| Touch targets ≥ 44pt (iOS) / 48dp (Android) mentionnés | ⚠️ Warning | `validate_design.py` |
| Safe Areas documentées | ⚠️ Warning | `validate_design.py` |
| Unités natives (pt/dp) au lieu de px | ⚠️ Warning | `validate_design.py` |
| Accessibilité mobile mentionnée (VoiceOver/TalkBack) | ⚠️ Warning | `validate_design.py` |

**Antipatterns détectés dans le code par `detect_ai_slop.py` :**

| Pattern | Signal | Remède |
| :--- | :--- | :--- |
| Largeurs d'écran hardcodées (375, 390, 412px) | Dimension iPhone/Android fixe | `.frame(maxWidth: .infinity)` / `LayoutBuilder` |
| `Color.white` fixe sans `colorScheme` | Dark mode non géré | `Color(.systemBackground)` / `MaterialTheme.colorScheme.background` |
| `Image` sans `accessibilityLabel` / `contentDescription` | VoiceOver/TalkBack inaccessible | Ajouter le label obligatoire |
| Touch target < 40pt en dur | Zone tactile trop petite | `.frame(width: 44, height: 44)` minimum |
| Icônes SF Symbols / Material Icons génériques | Signal IA identique au web | Icônes fonctionnelles justifiées uniquement |

**Unités par plateforme :**

```
iOS / SwiftUI       → pt    (points)      — grille 4pt
Android / Compose   → dp    (density-ind) — grille 4dp
Flutter             → px    (logical)     — grille 4
React Native        → dp    (auto-scaled) — grille 4
```

**Format minimal valide :**

```markdown
## 9. Mobile

- **Stack :** SwiftUI
- **Plateformes :** iOS 16+
- **Touch targets :** Boutons ≥ 44×44pt, zones tactiles étendues sur icônes
- **Safe Areas :** .safeAreaInset() pour le contenu, fond ignoreSafeArea()
- **Animations :** spring() pour les interactions, animation système pour navigation
- **Dark mode :** Color(.systemBackground), Color(.label) — semantic colors uniquement
- **Accessibilité :** .accessibilityLabel() sur toutes les Images, Dynamic Type supporté
```

## Checklist finale (résumé)

| § | Section | Validator | Bloquant |
| :--- | :--- | :--- | :--- |
| 0 | Sources Phase 0 | `check.py --gate 0` | ✅ Oui |
| 1 | Thème & Concept | `validate_design.py` | ✅ Oui (thèmes interdits) |
| 2 | Palette | `validate_design.py` | ✅ Oui (4–8 hex, WCAG) |
| 3 | Typographie | `validate_design.py` | ✅ Oui (max 2 polices) |
| 4 | Hiérarchie | — | ⚠️ Manuel |
| 5 | Espacement | `validate_design.py` + `audit_spacing.py` | ✅ Oui (multiples 8px) |
| 6 | Composants | `validate_design.py` | ✅ Oui (max 3 variantes) |
| 7 | Motion | `validate_design.py` + `diff_design_vs_code.py` | ✅ Oui (≤ 400ms) |
| 8 | Dark Mode | `validate_design.py` | ⚠️ Warning si absent |
| 9 | Mobile | `validate_design.py` | ⚠️ Optionnel, validé si présent |

---

## Erreurs fréquentes

**"Trop de couleurs (X > 8)"**
→ Des hex dans le texte WCAG de §2 sont comptabilisés. Écrire les ratios en texte pur sans hex : `Texte sur Fond : 9.2:1` au lieu de `#1E3A8A sur #F8FAFC : 9.2:1`.

**"Polices insuffisantes (0)"**
→ Le format doit être exactement `**NomPolice** (Display)` ou `**NomPolice** (Body)`.
Formats non reconnus : `- Display: **Fira Code**` ou `- Font: Fira Code`.

**"Icône générique détectée : check"**
→ Faux positif inévitable causé par le mot "Checklist". Ajouter dans `.slop-ignore` :
```ini
[icons]
check           # mot "check" dans "Checklist" — faux positif connu du validateur
```

**"Section Dark Mode absente"**
→ Warning (non bloquant). Ajouter `## 8. Dark Mode` avec ≥ 3 couleurs, fond sombre, rôles `fond`/`texte`/`surface`.

**"Animation Xms dépasse le max"**
→ `diff_design_vs_code.py` a détecté une durée dans le code dépassant le max de §7.
Si c'est intentionnel (ex: animation de fond décorative), documenter l'exception dans §1 et §7.
