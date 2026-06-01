---
name: web-design-enhancer
description: Amélioration du design UI/UX de sites web en utilisant les principes DESIGN.md, les composants rigides shadcn/ui, les animations GSAP et une validation visuelle via le MCP Playwright. À utiliser pour éradiquer l'improvisation visuelle de l'IA et livrer des interfaces premium, épurées et professionnelles.
---

# Web Design Enhancer

Ce skill transforme n'importe quel site générique en une expérience visuelle haut de gamme. Il s'appuie sur le format `DESIGN.md` pour l'intention, `shadcn/ui` pour la structure, `GSAP` pour l'animation, et le **MCP Playwright** pour l'auto-correction visuelle obligatoire.

## Workflow d'Amélioration

### 1. Audit et Définition (Le "Cerveau")
Avant de coder, définir le système de design dans un fichier `DESIGN.md`.
- **Analyse** : Identifier les faiblesses actuelles (espacement incohérent, fioritures IA superflues, manque de hiérarchie).
- **Sémantique** : Créer le fichier `DESIGN.md` (voir `references/design-md-spec.md`) définissant l'atmosphère, les variables de thème shadcn/ui et la typographie.
- **Rationale** : Expliquer *pourquoi* chaque choix est fait (ex: "Bords arrondis `--radius: 0rem` pour affirmer un style brut et technique").

### 2. Implémentation Structurelle (Le "Corps")
Bâtir une interface propre et rigide sans improvisation.
- **Primitives** : Utiliser exclusivement les composants de **shadcn/ui** (Buttons, Dialogs, Cards) pour les éléments d'interface standard. Interdiction de recréer ces blocs à partir de divs brutes.
- **Variables** : Configurer le fichier de style global (`globals.css`) uniquement via les variables sémantiques définies dans le `DESIGN.md` (`--primary`, `--background`, etc.).

### 3. Dynamisme avec GSAP (L' "Âme")
Ajouter de la vie avec des animations intentionnelles et fluides (voir `references/gsap-best-practices.md`).
- **Complémentarité** : Laisser shadcn/ui et Tailwind gérer les états natifs (hover, focus). Utiliser GSAP uniquement pour l'orchestration (entrées échelonnées *staggers*, effets au scroll via ScrollTrigger).

### 4. Inspection Visuelle & Auto-Correction (Les "Yeux" via MCP Playwright) - CRITIQUE
Une tâche n'est jamais terminée tant qu'elle n'a pas été inspectée visuellement.
- **Rendu actif** : Lancer le serveur local et utiliser le MCP Playwright pour afficher l'interface.
- **Audit Anti-Slop (Chasse à l'odeur d'IA)** : Inspecter le rendu visuel et corriger immédiatement si l'un de ces défauts est présent :
  - *Artefacts* : Présence d'emojis, de stickers ou d'icônes décoratives non demandés.
  - *Logos inventés* : Formes bizarres ou placeholders graphiques improvisés pour remplir le vide.
  - *Géométrie bancale* : Non-respect de la grille stricte de 8px (paddings ou margins asymétriques).
- **Boucle de validation** : Modifier le code en cas de défaut, relancer l'inspection Playwright, et répéter jusqu'à obtenir un rendu humain et impeccable.

### Phase de Validation Automatisée (CI/CD du Design)

Avant de soumettre toute modification, vous devez obligatoirement exécuter la suite de tests intégrée :

1. Run `python scripts/detect_ai_slop.py` pour nettoyer le code de toute fioriture ou mauvaise pratique d'IA.
2. Run `python scripts/audit_spacing.py` pour valider la parfaite symétrie et l'alignement de la grille.
3. Run `python scripts/validate_design.py` pour orchestrer la vérification finale par rapport aux exigences du fichier DESIGN.md local.

Si un script renvoie une erreur ou un avertissement, l'agent doit immédiatement corriger le code source en se référant à `references/antipatterns-guide.md` et relancer la suite de tests. Tout rendu visuel non validé par les scripts sera rejeté.


## Directives d'Hygiène Visuelle Stricte
- **Moins mais mieux** : Si un élément visuel (bordure, ombre, dégradé) n'a pas de fonction claire, l'éliminer.
- **Grille de 8px stricte** : Utiliser uniquement les multiples de 8 pour les espacements (Tailwind: `p-2`, `p-4`, `m-8`, `gap-4`). Aucune valeur arbitraire ou impaire (interdiction des `p-[11px]`).
- **Logos textuels** : Si aucun logo n'est fourni, utiliser uniquement du texte stylisé de manière haut de gamme (`font-bold tracking-tight uppercase`).

## Ressources
- `references/design-md-spec.md` : Détails et structure du format DESIGN.md adapté à shadcn/ui.
- `references/gsap-best-practices.md` : Guide d'utilisation de GSAP.
- `scripts/visual_audit.py` : Script d'audit visuel utilisant Playwright.
- `scripts/detect_ai_slop.py` : Détecteur d'antipatterns IA.
