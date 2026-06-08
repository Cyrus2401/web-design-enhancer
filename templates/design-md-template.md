# DESIGN.md - Contrat de Design du Projet

Ce document définit les règles strictes de design pour le projet. Toute implémentation doit respecter ces spécifications pour éviter le "AI slop" et garantir une qualité professionnelle.

---

## 0. Sources Phase 0

> **Bloc obligatoire — preuve d'exécution de Phase 0.** `scripts/check.py --gate 0` lit cette section et bloque tant qu'elle n'est pas remplie.
> Tous les placeholders `[Ex: ...]`, `<brand>`, `<description>`, `<Projet>` doivent être remplacés par de vraies valeurs avant de passer à Phase 1.

### 0a. Référence visuelle — getdesign.md
- **Brand utilisée**: [Ex: stripe]
- **Commande exécutée**: `npx getdesign@latest add <brand>`
- **Tokens extraits du DESIGN.md de référence**: [Ex: palette gris + accent #635BFF, radius 8px, ombres douces]

### 0b. Intelligence design — UI/UX Pro Max
- **Description du produit**: [Ex: "fintech analytics dashboard"]
- **Requête exécutée**: `python3 scripts/search.py "<description>" --design-system -p "<Projet>"`
- **Style retenu**: [Ex: Clean Tech]
- **Pattern de page recommandé**: [Ex: dashboard split-pane, sidebar gauche, header dense]
- **Anti-patterns sectoriels à éviter**: [Ex: glassmorphism décoratif, neon glow]

### 0c. Justification
- **Justification du thème retenu**: [Ex: combinaison Stripe (palette) + Clean Tech (densité) pour SaaS B2B exigeant]

---

## 1. Thème Visuel & Concept
*Décrivez l'ambiance visuelle en termes techniques (ex: "Néomorphisme doux", "Minimalisme brutaliste", "Dark mode haute fidélité"). Évitez les buzzwords comme "moderne" ou "premium". Référez-vous aux styles UI de UI/UX Pro Max pour l'inspiration.*

- **Concept**: [Ex: Minimalisme Tech Haute Précision, Esthétique Industrielle]
- **Mots-clés**: [Ex: Géométrique, Contrasté, Fonctionnel, Brutaliste, Épuré]
- **Inspiration UI/UX Pro Max**: [Ex: Style "Neo-Brutalism", "Clean Tech", "Glassmorphism"]

## 2. Palette de Couleurs
*Utilisez des rôles sémantiques. Maximum 8 couleurs principales. Référez-vous aux palettes de couleurs de UI/UX Pro Max ou aux exemples de `getdesign.md` pour des combinaisons éprouvées.*

| Rôle | Hex | Utilisation |
| :--- | :--- | :--- |
| Primaire | # | [Ex: Boutons d'action, éléments clés] |
| Secondaire | # | [Ex: Éléments secondaires, accents] |
| Fond | # | [Ex: Arrière-plan principal] |
| Texte | # | [Ex: Texte principal] |
| Accent | # | [Ex: Éléments interactifs, mises en avant] |
| Succès | # | [Ex: Messages de succès] |
| Attention | # | [Ex: Alertes, avertissements] |
| Danger | # | [Ex: Actions destructives] |

## 3. Typographie
*Maximum 2 polices (une pour les titres/display, une pour le corps de texte). Référez-vous aux paires de polices de UI/UX Pro Max ou aux exemples de `getdesign.md`.*

- **Display (Titres)**: [Nom de la police] (Source: Google Fonts, Adobe Fonts, etc.)
- **Body (Corps de texte)**: [Nom de la police] (Source: Google Fonts, Adobe Fonts, etc.)
- **Monospace (Code/Données)**: [Nom de la police] (Optionnel, si nécessaire)

## 4. Hiérarchie Typographique
*Toutes les tailles doivent suivre une échelle harmonique. Définissez les tailles, poids et interlignes pour chaque niveau.*

- **H1**: [Taille] / [Poids] / [Interligne]
- **H2**: [Taille] / [Poids] / [Interligne]
- **H3**: [Taille] / [Poids] / [Interligne]
- **P (Paragraphe)**: [Taille] / [Poids] / [Interligne]
- **Small (Texte secondaire)**: [Taille] / [Poids] / [Interligne]

## 5. Espacement et Grille
*Base: 8px. Tous les multiples sont autorisés (8, 16, 24, 32, 48, 64, etc.). Référez-vous aux systèmes d'espacement de `getdesign.md`.*

- **Base de la grille**: 8px
- **Gouttière (Colonnes)**: [Ex: 24px, 32px]
- **Padding Section Vertical**: [Ex: 64px, 96px]
- **Padding Section Horizontal**: [Ex: 32px, 48px]
- **Radius (Arrondis)**: [Ex: 0px, 4px, 8px, 12px] (Multiples de 4px acceptés)

## 6. Composants et États
*Définissez les interactions et les variations des composants clés. Utilisez `shadcn/ui` comme base et personnalisez selon ces spécifications. Référez-vous aux directives UX de UI/UX Pro Max.*

### Boutons
- **Primaire (Normal)**: [Description visuelle: couleur de fond, texte, bordure]
- **Primaire (Hover)**: [Description visuelle: changement de couleur, ombre]
- **Secondaire (Normal)**: [Description visuelle]
- **Secondaire (Hover)**: [Description visuelle]
- **Ghost/Link (Normal)**: [Description visuelle]

### Cartes (Cards)
- **Structure**: [Ex: Fond `surface-card`, bordure `hairline`]
- **Padding Interne**: [Ex: 24px]
- **Ombre**: [Ex: `0px 4px 12px rgba(0,0,0,0.1)`]

## 7. Motion et Animations
*Timings stricts (≤ 400ms). Référez-vous aux bonnes pratiques GSAP et aux directives de UI/UX Pro Max pour des animations fluides et intentionnelles.*

- **Transitions Générales**: [Ex: 200ms ease-out]
- **Entrées d'éléments (Stagger)**: [Ex: Stagger 50ms, Duration 300ms]
- **Interactions (Hover/Click)**: [Ex: 150ms ease-in-out]
- **Accessibilité**: `prefers-reduced-motion` obligatoire.

---


---

## 8. Dark Mode

> **Obligatoire.** Sans contrat dark mode explicite, l'implémentation sera improvisée.
> `validate_design.py` bloque si cette section est absente ou insuffisante (< 3 couleurs).

| Rôle | Hex | Équivalent Light |
| :--- | :--- | :--- |
| Fond | [Ex: #0F1117] | [Ex: #FFFFFF] |
| Surface | [Ex: #1C1E26] | [Ex: #F8FAFC] |
| Texte | [Ex: #E8EAF0] | [Ex: #1E3A8A] |
| Texte secondaire | [Ex: #94A3B8] | [Ex: #64748B] |
| Bordure | [Ex: #2D3142] | [Ex: #E2E8F0] |
| Primaire (inchangé) | [Ex: #533afd] | [Ex: #533afd] |
| Accent dark | [Ex: #7C6FFF] | [Ex: #D97706] |

**Règles dark mode :**
- Le fond doit être < `#333` (luminosité relative < 9%)
- Le texte sur fond dark doit passer WCAG AA (≥ 4.5:1)
- Les couleurs sémantiques (Succès, Danger, Attention) restent lisibles sur fond dark
- Utiliser `prefers-color-scheme: dark` en CSS, pas de toggle JS non demandé


---

## 9. Mobile

> **Optionnel pour les projets web-only. Obligatoire dès qu'une app native ou hybrid est dans le scope.**
> `validate_design.py` valide cette section si elle est présente — touch targets, safe areas, unités natives, accessibilité.

### Plateforme(s) cible(s)

- **Stack :** [SwiftUI | Flutter | React Native | Jetpack Compose | Expo]
- **Plateformes :** [iOS | Android | Les deux]
- **Version minimum :** [Ex: iOS 16+, Android 8+ (API 26)]

### Unités et Grille Mobile

> Ne jamais utiliser `px` en dur dans du code natif — utiliser les unités de la plateforme.

| Plateforme | Unité | Grille base | Exemple |
| :--- | :--- | :--- | :--- |
| iOS / SwiftUI | pt (points) | 4pt | `padding(16)` = 16pt |
| Android / Compose | dp | 4dp | `Modifier.padding(16.dp)` |
| Flutter | logical pixels | 4 | `SizedBox(height: 16)` |
| React Native | dp (auto) | 4 | `padding: 16` |

- **Grille de base :** [4pt / 4dp — multiples de 4 uniquement en mobile]
- **Padding horizontal :** [Ex: 16pt / 16dp]
- **Padding vertical section :** [Ex: 24pt / 24dp]
- **Espacement entre éléments :** [Ex: 8pt, 12pt, 16pt, 24pt]

### Touch Targets

> iOS HIG minimum : **44×44pt**. Material Design minimum : **48×48dp**.

- **Boutons principaux :** [Ex: hauteur 44pt minimum, largeur full-width ou ≥ 120pt]
- **Icônes interactives :** [Ex: zone tactile 44×44pt même si l'icône est plus petite]
- **Éléments de liste :** [Ex: hauteur ligne ≥ 44pt]
- **Champs de formulaire :** [Ex: hauteur 44pt minimum]

```swift
// SwiftUI — zone tactile explicite
Button(action: {}) {
    Image(systemName: "heart")
        .frame(width: 44, height: 44) // Touch target iOS HIG
}
```

```kotlin
// Compose — zone tactile Material
IconButton(
    modifier = Modifier.size(48.dp), // Touch target Material
    onClick = {}
) { Icon(Icons.Default.Favorite, contentDescription = "Favoris") }
```

### Safe Areas

> Ne jamais hardcoder les hauteurs de status bar, notch ou home indicator.

- **Stratégie iOS :** `.safeAreaInset()` ou `.ignoresSafeArea()` uniquement pour le fond
- **Stratégie Android :** `WindowInsets` via `Modifier.windowInsetsPadding()`
- **Stratégie RN :** `useSafeAreaInsets()` depuis `react-native-safe-area-context`
- **Stratégie Flutter :** `MediaQuery.of(context).padding` ou `SafeArea` widget

### Navigation Mobile

- **Pattern :** [Tab Bar (iOS) | Bottom Navigation (Android) | Navigation Drawer | Stack]
- **Tab Bar :** [Ex: 5 onglets maximum, icône + label, hauteur 83pt sur iPhone avec home indicator]
- **Transitions :** [Ex: push/pop natif, modal sheet, fullscreen cover]

### Animations Mobiles

> Sur mobile, les animations système (spring) sont préférées aux durées fixes.

- **Transitions de navigation :** Animation système native (pas de durée custom)
- **Micro-interactions :** [Ex: spring() pour les bounces, 200ms pour les fades]
- **Feedback tactile :** [Ex: UIImpactFeedbackGenerator / HapticFeedback.lightImpact()]
- **prefers-reduced-motion :** iOS `isReduceMotionEnabled`, Android `isReducedMotionEnabled`

### Dark Mode Mobile

> Le dark mode natif est automatique sur iOS/Android si les semantic colors sont utilisées.

- **iOS :** Utiliser `Color(.systemBackground)`, `Color(.label)`, `Color(.secondaryLabel)`
- **Android :** Utiliser `MaterialTheme.colorScheme.background`, `.onBackground`, `.surface`
- **Flutter :** `Theme.of(context).colorScheme` avec `ThemeData.dark()`
- **React Native :** `useColorScheme()` + `StyleSheet.create` avec variables conditionnelles

### Accessibilité Mobile

- **VoiceOver (iOS) :** `.accessibilityLabel()` sur chaque `Image` et élément interactif
- **TalkBack (Android) :** `contentDescription` sur chaque `Image` (null si décoratif)
- **Focus order :** `.accessibilitySortPriority()` (iOS) / `Modifier.semantics` (Compose)
- **Taille de texte dynamique :** Supporter Dynamic Type (iOS) / Text Scaling (Android)

---


---

## 10. Three.js

> **Optionnel. Obligatoire dès qu'une scène WebGL/Three.js est dans le scope.**
> `validate_design.py` valide cette section si présente. `detect_ai_slop.py` scanne le code `.js`/`.ts`/`.jsx`/`.tsx` pour les antipatterns Three.js critiques.

### Type de scène

- **Type :** [Hero background | Interactive viewer | Scroll-driven storytelling | Particle system | Product showcase]
- **Rôle visuel :** [Ex: fond animé statique, modèle 3D interactif, caméra scroll-driven]
- **Stack :** Three.js r128 via CDN épinglé (jamais `@latest`)

### Renderer

- **Instance :** Un seul `WebGLRenderer` par page — lifetime = page entière
- **Pixel ratio :** `renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))` — cap obligatoire
- **Alpha :** `alpha: true` sur le renderer + fond via CSS (pas `setClearColor`)
- **Antialias :** `antialias: true` pour desktop, `false` sur mobile si perf insuffisante

### Budget Géométrie

| Rôle | Segments recommandés |
| :--- | :--- |
| Hero mesh (foreground) | 32–64 |
| Background meshes | 8–16 |
| Particles stand-in | 6–8 |
| Ground plane | 1 (PlaneGeometry) |

**Règle absolue :** Jamais de `new THREE.XxxGeometry()` dans `animate()` — créer avant la boucle.

### Lighting

- **Minimum :** `AmbientLight` (fill, intensity 0.4) + `DirectionalLight` (key, intensity 1.0)
- **Shadows :** Activé uniquement sur la `DirectionalLight` principale et le hero mesh
- **`MeshBasicMaterial` :** Pas besoin de lights — utiliser pour éléments décoratifs plats

### Dispose Strategy

Toujours appeler avant `scene.remove()` :
```js
mesh.geometry.dispose()
mesh.material.dispose()
mesh.material.map?.dispose()       // textures
mesh.material.normalMap?.dispose() // normal maps
```

### Fallback WebGL

- **Détection :** `WebGL2RenderingContext` ou `WebGLRenderingContext` dans `window`
- **Fallback :** [Image statique PNG | Canvas 2D simplifié | Message discret]

### Animations Three.js

> Note : La règle ≤ 400ms du §7 s'applique aux transitions UI, **pas** aux animations Three.js.
> Les boucles 60fps, scrub scroll, et rotations continues sont exemptées.

- **UI transitions** (fondu, apparition) : ≤ 400ms via GSAP
- **Boucles Three.js** : clock.getDelta(), requestAnimationFrame — pas de durée fixe
- **Scroll scrub** : GSAP ScrollTrigger + `scrub: 1` — durée relative au scroll, pas en ms
- **prefers-reduced-motion :** Scène figée (`renderer` toujours actif mais `delta = 0`) ou rotation lente (0.001 rad/frame max)

### Accessibilité WebGL

- **`<canvas>` :** Attribut `aria-label` descriptif + `role="img"`
- **Interactivité 3D :** Cursor `pointer` sur hover (raycasting), feedback tactile si mobile
- **Screen readers :** Contenu alternatif visible dans `<noscript>` ou `aria-describedby`

---

## ✅ Checklist de Validation Anti-Slop

Avant livraison, vérifier:

- [ ] **DESIGN.md** : Complet et respecte toutes les sections définies.
- [ ] **Polices** : Maximum 2 polices principales, issues de paires intentionnelles.
- [ ] **Espacements** : Tous les espacements (padding, margin, gap) sont des multiples de 8px.
- [ ] **Rayons** : Tous les rayons (border-radius) sont des multiples de 4px.
- [ ] **Icônes** : Utilisation de Custom SVG ou d'un pack cohérent (pas d'icônes Lucide génériques non justifiées).
- [ ] **Gradients** : Justifiés par un rôle sémantique clair, maximum 2-3 gradients distincts.
- [ ] **Artefacts Visuels** : Absence d'emojis, stickers, ou éléments décoratifs non demandés.
- [ ] **Logos/Noms** : Pas de placeholders génériques ("your-logo", "brandname"). Utiliser du texte stylisé si aucun logo n'est fourni.
- [ ] **Structure** : Layout unique et intentionnel, pas une structure de template générique (Hero, Features, Testimonials, CTA, Pricing, FAQ, Footer).
- [ ] **Texte** : Descriptions précises, pas de buzzwords vagues ("premium", "moderne", "incroyable").
- [ ] **Boutons** : Hiérarchie claire (Primaire, Secondaire, Ghost, Destructive) avec des styles distincts.
- [ ] **Couleurs** : Palette de 4-8 couleurs avec des rôles sémantiques clairs, définies dans le DESIGN.md.
- [ ] **Animations** : Toutes les animations sont ≤ 400ms et respectent `prefers-reduced-motion`.
- [ ] **Shadcn/ui** : Composants personnalisés et non laissés par défaut.
- [ ] **Dark Mode** : Section ## 8. Dark Mode présente, ≥ 3 couleurs, fond < #333, WCAG AA validé.
- [ ] **Mobile** (si applicable) : Section ## 9. Mobile présente, touch targets ≥ 44pt/48dp, safe areas documentées, unités natives (pas de px).

**Exécuter l'audit automatique:**
```bash
python3 scripts/detect_ai_slop.py --design DESIGN.md --code ./client/src
python3 scripts/visual_audit.py --url http://localhost:3000 --output ./audit-results
```

Score de qualité attendu ≥ 80/100 pour la livraison.
