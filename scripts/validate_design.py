#!/usr/bin/env python3
"""
Design Validation Script for web-design-enhancer

Valide un fichier DESIGN.md pour éviter le "AI slop":
- Vérifie les espacements (multiples de 8px)
- Valide la typographie (max 2 polices)
- Contrôle les couleurs (rôles sémantiques)
- Audit les animations (≤ 400ms) — gère ms ET secondes
- Valide le contraste WCAG AA (4.5:1 texte, 3.0:1 UI)
- Détecte les antipatterns (gradients clichés, icônes génériques)

Usage:
    python3 validate_design.py DESIGN.md
    python3 validate_design.py DESIGN.md --strict
"""

import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple


class DesignValidator:
    """Validateur de DESIGN.md"""

    def __init__(self, filepath: str, strict: bool = False):
        self.filepath = Path(filepath)
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self._has_threejs: bool = False  # Three.js en scope
        self.content = ""
        self.sections = {}

    def run(self) -> bool:
        """Exécute la validation complète. Retourne True si OK."""
        if not self.filepath.exists():
            print(f"❌ Erreur: Fichier {self.filepath} non trouvé")
            return False

        self.content = self.filepath.read_text(encoding="utf-8")
        self._parse_sections()

        # Validations
        self._validate_phase0_evidence()    # Gate 0 — preuve d'exécution Phase 0
        self._validate_structure()
        self._validate_theme_originality()  # Niveau 1 — bloquer dès le DESIGN.md
        self._validate_typography()
        self._validate_hierarchy()  # §4 — plages H1/H2/H3/P/Small (WCAG + lisibilité)
        self._validate_colors()
        self._validate_wcag_contrast()
        self._validate_spacing()
        self._validate_animations()
        self._validate_components()
        self._detect_antipatterns()
        self._validate_dark_mode()  # Section dark mode obligatoire
        self._validate_ux_completeness()  # Règles UX issues de l'audit visuel
        self._validate_mobile()      # Section mobile (optionnelle mais validée si présente)
        self._validate_dark_mode_required()  # §8 obligatoire si fond sombre
        self._validate_section_density()     # Densité Contact/CTA + grille N impair
        self._validate_threejs()           # §10 Three.js (optionnel, validé si présent)

        # Dédupliquer les erreurs identiques
        self.errors   = list(dict.fromkeys(self.errors))
        self.warnings = list(dict.fromkeys(self.warnings))

        # Rapport
        self._print_report()
        return len(self.errors) == 0

    def _parse_sections(self):
        """Parse les sections principales du DESIGN.md"""
        sections = {
            "theme": r"## 1\. Thème Visuel.*?(?=\n## |\Z)",
            "colors": r"## 2\. Palette de Couleurs.*?(?=\n## |\Z)",
            "typography": r"## 3\. Typographie.*?(?=\n## |\Z)",
            "hierarchy": r"## 4\. Hiérarchie Typographique.*?(?=\n## |\Z)",
            "spacing": r"## 5\. Espacement et Grille.*?(?=\n## |\Z)",
            "components": r"## 6\. Composants et États.*?(?=\n## |\Z)",
            "animations": r"## 7\. Motion et Animations.*?(?=\n## |\Z)",
            "checklist": r"## ✅ Checklist.*?(?=\\n## |\\Z)",
            "darkmode": r"## 8\. Dark Mode.*?(?=\n## |\Z)",
            "mobile": r"## 9\. Mobile.*?(?=\n## |\Z)",
            "threejs": r"## 10\. Three\.js.*?(?=\n## |\Z)",
        }

        for name, pattern in sections.items():
            match = re.search(pattern, self.content, re.DOTALL | re.IGNORECASE)
            self.sections[name] = match.group(0) if match else ""

    def _validate_phase0_evidence(self):
        """
        Gate 0 — Vérifie que Phase 0 a été réellement exécutée.
        Sans preuve dans le DESIGN.md → bloque tout le reste.
        Empêche l'IA de sauter Phase 0 et d'inventer le DESIGN.md depuis son training data.
        """
        missing = []

        # Section obligatoire
        if "## 0. Sources Phase 0" not in self.content:
            self.errors.append(
                "[PHASE 0 MANQUANTE] La section '## 0. Sources Phase 0' est absente du DESIGN.md. "
                "Phase 0 (getdesign.md + UI/UX Pro Max) doit être exécutée avant tout code. "
                "Utiliser templates/design-md-template.md comme base."
            )
            return  # Inutile de continuer — preuve totalement absente

        # Vérifier que les placeholders ont été remplacés par de vraies valeurs
        placeholder_patterns = [
            (r"\[Ex:", "Contient encore des placeholders non remplis '[Ex: ...]'"),
            (r"Brand utilisée\s*:\s*\[", "Brand getdesign.md non renseignée"),
            (r"Commande exécutée\s*:\s*`npx getdesign@latest add <brand>`",
             "Commande getdesign.md non exécutée (placeholder '<brand>' non remplacé)"),
            (r"Requête exécutée\s*:\s*`python3 scripts/search\.py \"<description>\"",
             "Commande UI/UX Pro Max non exécutée (placeholder non remplacé)"),
            (r"Style retenu\s*:\s*\[",
             "Style UI/UX Pro Max non renseigné — search.py doit être lancé"),
            (r"Justification.*?:\s*\[",
             "Justification du thème non renseignée"),
        ]

        for pattern, message in placeholder_patterns:
            if re.search(pattern, self.content):
                missing.append(message)

        for msg in missing:
            self.errors.append(f"[PHASE 0 INCOMPLÈTE] {msg}")

        if missing:
            self.errors.append(
                "→ Exécuter Phase 0 avant de continuer : "
                "(1) npx getdesign@latest add <brand>  "
                "(2) python3 scripts/search.py '<description>' --design-system -p '<Projet>'  "
                "(3) Remplir la section '## 0. Sources Phase 0' avec les vraies valeurs."
            )

    def _validate_theme_originality(self):
        """
        Niveau 1 — Détecte les thèmes et concepts IA clichés directement dans le DESIGN.md.
        Bloque avant que le code soit écrit.
        """
        FORBIDDEN_THEMES = [
            (r"\bdark\s+cyberpunk\b",
             "'dark cyberpunk' — cliché IA #1 portfolios tech. Décrire la texture réelle à la place."),
            (r"\bcyberneti[cq]",
             "'cybernétique/cybernetic' — esthétique IA générique. Spécifier les vrais tokens visuels."),
            (r"\bglow[\s-]cursor\b",
             "Glow cursor — effet non demandé, signal IA fort. Supprimer du DESIGN.md."),
            (r"\bgrid[\s-]background\b",
             "Grid background — fond grille présent dans 90% des portfolios dev IA. Utiliser fond uni."),
            (r"\bglassmorphism\b",
             "Glassmorphism — tendance épuisée. Autoriser uniquement pour modals/dropdowns fonctionnels."),
            (r"\bneon[\s-]glow\b|\bneon[\s-]accent",
             "Neon glow/accents — signal IA cyberpunk immédiat."),
            (r"\bparticle(?:s)?[\s-](?:background|effect|js)\b",
             "Particles background — overdone depuis 2018, signal IA fort."),
            (r"\btyp(?:ewriter|ed)[\s-]effect\b|\btyped\.js\b",
             "Typewriter/typed effect — cliché portfolio dev. Titre statique uniquement."),
            (r"\bsys[_\s]status\b",
             "SYS_STATUS badge — injection IA non demandée. Doit être justifié dans le brief."),
            (r"\bhero[\s-]badge\b",
             "Hero badge décoratif — l'information est déjà dans le H1/H2. Supprimer."),
            (r"\bstyle\s+(?:monitoring|grafana|datadog)\b",
             "Style Monitoring/Grafana comme thème — générique IA pour profils sysadmin."),
        ]

        found = []
        for pattern, message in FORBIDDEN_THEMES:
            if re.search(pattern, self.content, re.IGNORECASE):
                found.append(message)

        for msg in found:
            self.errors.append(f"[THÈME INTERDIT] {msg}")

        if found:
            self.errors.append(
                "→ Corriger le DESIGN.md avant tout code. "
                "Chaque concept interdit doit être remplacé par une description "
                "spécifique au projet réel, pas au secteur."
            )

    def _validate_structure(self):
        """Vérifie que toutes les sections obligatoires existent"""
        required = ["theme", "colors", "typography", "spacing", "components", "animations"]
        for section in required:
            if not self.sections.get(section):
                self.errors.append(f"❌ Section obligatoire manquante: {section}")

    def _validate_typography(self):
        """Valide la typographie (max 2 polices)"""
        typography_section = self.sections.get("typography", "")

        # Détecte les polices mentionnées
        font_patterns = [
            r"(?:Font|Police|Typeface):\s*([A-Za-z\s]+?)(?:\n|,|$)",
            r"\*\*([A-Za-z\s]+?)\*\*.*?(?:Display|Body|Monospace)",
        ]

        fonts = set()
        for pattern in font_patterns:
            matches = re.findall(pattern, typography_section, re.IGNORECASE)
            fonts.update(m.strip() for m in matches if m.strip())

        # Exclure les mots-clés non-polices
        exclude = {"font", "police", "typeface", "raison", "utilisation", "poids", "espacement"}
        fonts = {f for f in fonts if f.lower() not in exclude and len(f) > 2}

        # Max 2 familles — la police monospace compte comme 3e famille
        # Justification : 3 familles = signal AI slop (le générateur ajoute toujours une mono)
        # Si une mono est nécessaire, elle doit remplacer display ou body, pas s'y ajouter
        if len(fonts) > 2:
            self.errors.append(
                f"❌ Trop de polices ({len(fonts)}): {', '.join(sorted(fonts))}. "
                f"Max 2 familles — la police monospace compte comme 3e. "
                f"Si JetBrains Mono / Fira Code est nécessaire, remplacer display ou body, pas s'ajouter."
            )
        elif len(fonts) < 2:
            self.warnings.append(f"⚠️  Polices insuffisantes ({len(fonts)}): Minimum 2 requises")

        # Vérifie les polices génériques (antipattern)
        generic_fonts = {"helvetica", "arial", "times new roman", "georgia", "verdana"}
        for font in fonts:
            if font.lower() in generic_fonts:
                self.errors.append(f"❌ Police générique détectée: {font}. Utiliser Google Fonts ou custom")

    def _validate_hierarchy(self):
        """§4 — Valide les plages de tailles typographiques.

        Sources :
        - H1 28–80px  : plage display lisible (en-dessous = pas de hiérarchie, au-dessus = AI slop hero géant)
        - H2 22–60px  : plage sous-titre de section
        - H3 18–36px  : plage titre de carte / sous-section
        - P  13–18px  : plage WCAG lisibilité corps de texte (en-dessous = inaccessible, au-dessus = signal IA)
        - Small 11–14px : caption / méta

        Le §4 doit être présent. Cette validation ferme la dernière brèche subjective
        du pipeline ("vérifiable > subjectif").
        """
        hierarchy_section = self.sections.get("hierarchy", "")
        if not hierarchy_section:
            self.warnings.append(
                "⚠️  Section '## 4. Hiérarchie Typographique' absente. "
                "Définir H1/H2/H3/P/Small avec tailles px pour validation automatique."
            )
            return

        # Plages recommandées en px (min, max)
        RANGES = {
            "h1":    (28, 80),
            "h2":    (22, 60),
            "h3":    (18, 36),
            "p":     (13, 18),
            "small": (11, 14),
        }

        # Matche les lignes du type "- **H1**: 48px / 700 / 1.2"
        # ou "- **P (Paragraphe)**: 16px ..." — on capture le label et la première valeur px
        # Le label peut contenir un chiffre (H1, H2, H3) — d'où [A-Za-z]\w*
        line_pattern = re.compile(
            r"^\s*-\s*\*\*\s*([A-Za-z]\w*)(?:\s*\([^)]+\))?\s*\*\*\s*:\s*(\d+)\s*px",
            re.MULTILINE
        )

        found_levels = set()
        for match in line_pattern.finditer(hierarchy_section):
            label = match.group(1).lower()
            val = int(match.group(2))
            if label not in RANGES:
                continue
            found_levels.add(label)
            lo, hi = RANGES[label]
            if val < lo:
                self.errors.append(
                    f"❌ §4 Hiérarchie : {label.upper()} trop petit ({val}px). "
                    f"Plage attendue : {lo}–{hi}px."
                )
            elif val > hi:
                self.errors.append(
                    f"❌ §4 Hiérarchie : {label.upper()} trop grand ({val}px). "
                    f"Plage attendue : {lo}–{hi}px."
                )

        # Vérifier qu'au minimum H1 et P sont déclarés avec des valeurs px
        if "h1" not in found_levels:
            self.warnings.append(
                "⚠️  §4 Hiérarchie : H1 absent ou sans valeur en px. "
                "Format attendu : '- **H1**: 48px / 700 / 1.2'."
            )
        if "p" not in found_levels:
            self.warnings.append(
                "⚠️  §4 Hiérarchie : P (corps de texte) absent ou sans valeur en px. "
                "Format attendu : '- **P**: 16px / 400 / 1.6'."
            )

    def _validate_colors(self):
        """Valide la palette de couleurs"""
        colors_section = self.sections.get("colors", "")

        # Détecte les couleurs hex
        hex_pattern = r"#[0-9A-Fa-f]{6}"
        colors = re.findall(hex_pattern, colors_section)

        if len(colors) < 4:
            self.errors.append(f"❌ Trop peu de couleurs ({len(colors)}). Minimum 4 requises")
        elif len(colors) > 8:
            self.errors.append(f"❌ Trop de couleurs ({len(colors)}). Maximum 8 recommandé")

        # Vérifie les rôles sémantiques — liste élargie avec tous les synonymes usuels
        roles = [
            "primaire", "primary",
            "secondaire", "secondary",
            "accent",
            "fond", "background", "bg",
            "texte", "foreground", "text",
            "succès", "success", "succes",
            "attention", "warning", "avertissement",
            "danger", "destruction", "error", "erreur",
            "muet", "muted", "border", "bordure", "surface",
            "ring", "card",
        ]
        found_roles = sum(1 for role in roles if role.lower() in colors_section.lower())

        if found_roles < 4:
            self.warnings.append(f"⚠️  Rôles sémantiques insuffisants ({found_roles}). Minimum 4 recommandé")

        # Détecte les gradients clichés
        cliche_gradients = [
            (r"bleu.*?violet|blue.*?purple", "bleu→violet"),
            (r"rose.*?violet|pink.*?purple", "rose→violet"),
            (r"rose.*?rouge|pink.*?red", "rose→rouge"),
            (r"cyan.*?bleu|cyan.*?blue", "cyan→bleu"),
        ]

        for pattern, name in cliche_gradients:
            if re.search(pattern, colors_section, re.IGNORECASE):
                self.warnings.append(f"⚠️  Gradient cliché détecté: {name}. Justifier par rôle sémantique")

    def _validate_spacing(self):
        """Valide que tous les espacements sont multiples de 8px"""
        spacing_section = self.sections.get("spacing", "")

        # Détecte les valeurs de spacing
        spacing_pattern = r"(\d+)\s*px"
        spacings = re.findall(spacing_pattern, spacing_section)

        invalid_spacings = []
        for spacing in spacings:
            value = int(spacing)
            if value % 8 != 0 and value != 4:  # 4px acceptable pour micro-espacements
                invalid_spacings.append(value)

        if invalid_spacings:
            self.errors.append(
                f"❌ Espacements non-multiples de 8px: {invalid_spacings}. "
                f"Utiliser: 4, 8, 16, 24, 32, 48, 64"
            )

        # Vérifie la présence de la grille 8px
        if "8px" not in spacing_section and "8 px" not in spacing_section:
            self.warnings.append("⚠️  Grille 8px non mentionnée explicitement")

    def _validate_animations(self):
        """Valide les animations (durée ≤ 400ms) — gère ms et s séparément."""
        animations_section = self.sections.get("animations", "")

        # Durées explicitement en millisecondes (ex: 200ms, 300ms, 50ms)
        ms_raw = re.findall(r"(\d+(?:\.\d+)?)\s*ms\b", animations_section)
        ms_values = [(float(v), f"{v}ms") for v in ms_raw]

        # Durées en secondes (ex: 0.3s, 1s, 2s) — exclut le mot "seconds"
        # Le pattern ne matche PAS "Nms" car après N vient 'm', pas 's' directement
        s_raw = re.findall(r"(\d+(?:\.\d+)?)\s*s(?!econds)\b", animations_section)
        s_values = [(float(v) * 1000, f"{v}s → {float(v)*1000:.0f}ms") for v in s_raw]

        all_durations = ms_values + s_values
        invalid_durations = [(ms_val, label) for ms_val, label in all_durations if ms_val > 400]

        if invalid_durations:
            # Exception : si Three.js est dans le scope (§10), les durées longues
            # sont légitimes pour les scroll scrub, boucles 60fps, etc.
            if getattr(self, "_has_threejs", False):
                long_ui = [(ms, l) for ms, l in invalid_durations if ms < 5000]
                if long_ui:
                    labels = [l for _, l in long_ui]
                    self.warnings.append(
                        f"⚠️  Animations longues (probablement Three.js scroll/loop): {chr(39).join(labels)}. "
                        f"Si UI transitions : max 400ms. Si Three.js : documenter dans §10."
                    )
            else:
                labels = [label for _, label in invalid_durations]
                self.errors.append(
                    f"❌ Animations trop longues: {', '.join(labels)}. "
                    f"Maximum 400ms recommandé"
                )

        # Vérifie prefers-reduced-motion
        if "prefers-reduced-motion" not in animations_section.lower():
            self.warnings.append("⚠️  Pas de mention de prefers-reduced-motion")

    # ------------------------------------------------------------------ #
    # WCAG AA Contrast                                                    #
    # ------------------------------------------------------------------ #

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convertit #RRGGBB en tuple (R, G, B) — valeurs 0-255."""
        h = hex_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _relative_luminance(self, rgb: tuple) -> float:
        """Luminance relative WCAG 2.1 (https://www.w3.org/TR/WCAG21/#dfn-relative-luminance)."""
        def linearize(c: int) -> float:
            s = c / 255.0
            return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
        r, g, b = (linearize(c) for c in rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _contrast_ratio(self, hex1: str, hex2: str) -> float:
        """Ratio de contraste WCAG entre deux couleurs hex."""
        l1 = self._relative_luminance(self._hex_to_rgb(hex1))
        l2 = self._relative_luminance(self._hex_to_rgb(hex2))
        lighter, darker = max(l1, l2), min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    def _validate_wcag_contrast(self):
        """Valide le contraste WCAG AA (texte 4.5:1, éléments UI 3.0:1)."""
        colors_section = self.sections.get("colors", "")
        hex_pattern = r"#[0-9A-Fa-f]{6}"

        # Extraire les paires (rôle sémantique, couleur hex) depuis le tableau
        role_map: Dict[str, str] = {}
        for line in colors_section.splitlines():
            hexes = re.findall(hex_pattern, line)
            if not hexes:
                continue
            line_lower = line.lower()
            if any(k in line_lower for k in ("texte", "text", "foreground", "corps")):
                role_map.setdefault("text", hexes[0])
            elif any(k in line_lower for k in ("fond", "background", "bg", "arrière")):
                role_map.setdefault("bg", hexes[0])
            elif any(k in line_lower for k in ("primaire", "primary")):
                role_map.setdefault("primary", hexes[0])

        if "text" not in role_map or "bg" not in role_map:
            self.warnings.append(
                "⚠️  WCAG: impossible d'identifier Texte/Fond automatiquement. "
                "Nommez les rôles 'Texte' et 'Fond' explicitement dans le tableau de couleurs."
            )
            return

        # Contraste Texte / Fond — WCAG AA texte normal: 4.5:1
        ratio_text = self._contrast_ratio(role_map["text"], role_map["bg"])
        if ratio_text < 4.5:
            self.errors.append(
                f"❌ WCAG AA: contraste Texte/Fond insuffisant {ratio_text:.2f}:1 "
                f"({role_map['text']} sur {role_map['bg']}). Minimum: 4.5:1"
            )

        # Contraste Primaire / Fond — WCAG AA éléments UI: 3.0:1
        if "primary" in role_map:
            ratio_ui = self._contrast_ratio(role_map["primary"], role_map["bg"])
            if ratio_ui < 3.0:
                self.errors.append(
                    f"❌ WCAG AA: contraste Primaire/Fond insuffisant {ratio_ui:.2f}:1 "
                    f"({role_map['primary']} sur {role_map['bg']}). Minimum UI: 3.0:1"
                )

    def _validate_components(self):
        """Valide les composants (max 3 variantes)"""
        components_section = self.sections.get("components", "")

        # Détecte les variantes de boutons
        button_pattern = r"### Variantes.*?(?=###|$)"
        button_section = re.search(button_pattern, components_section, re.DOTALL)

        if button_section:
            variants = re.findall(r"\d\.\s+\*\*([^*]+)\*\*", button_section.group(0))
            if len(variants) > 3:
                self.errors.append(
                    f"❌ Trop de variantes de boutons ({len(variants)}). Maximum 3 recommandé"
                )

    def _detect_antipatterns(self):
        """Détecte les antipatterns (AI slop)"""
        content_lower = self.content.lower()

        # Icônes génériques Lucide
        lucide_icons = ["sparkles", "zap", "cog", "network", "arrow", "check", "star"]
        found_icons = [icon for icon in lucide_icons if icon in content_lower]

        if found_icons:
            self.warnings.append(
                f"⚠️  Icônes Lucide génériques détectées: {', '.join(found_icons)}. "
                f"Considérer custom SVG ou pack cohérent"
            )

        # Buzzwords vagues
        buzzwords = ["premium", "moderne", "élégant", "magnifique", "incroyable"]
        found_buzzwords = [bw for bw in buzzwords if bw in content_lower]

        if found_buzzwords:
            self.warnings.append(
                f"⚠️  Buzzwords vagues: {', '.join(found_buzzwords)}. "
                f"Remplacer par descriptions précises"
            )

        # Sections template génériques
        template_sections = ["hero", "features", "cta", "testimonials", "footer"]
        found_sections = sum(1 for sec in template_sections if sec in content_lower)

        if found_sections >= 4:
            self.warnings.append(
                f"⚠️  Structure template générique détectée ({found_sections} sections). "
                f"Considérer une approche plus unique"
            )

        # Gradients uniformes
        if "gradient" in content_lower:
            gradient_count = len(re.findall(r"gradient", content_lower))
            if gradient_count > 3:
                self.warnings.append(
                    f"⚠️  Trop de gradients ({gradient_count}). "
                    f"Limiter à 2-3 gradients intentionnels"
                )



    def _validate_ux_completeness(self):
        """Vérifie la complétude UX — règles issues de l'audit visuel réel.
        Détecte les lacunes fréquentes non couvertes par les autres validators."""
        components_section = self.sections.get("components", "")
        spacing_section    = self.sections.get("spacing", "")
        animations_section = self.sections.get("animations", "")

        # ── Grille projet N impair ────────────────────────────────────────
        # Si §6 mentionne une grille de cards/projets, vérifier que le comportement
        # sur nombre impair est documenté
        has_grid = any(k in components_section.lower() for k in
                       ["grid", "grille", "card", "carte", "projet", "project"])
        has_odd_rule = any(k in components_section.lower() for k in
                           ["impair", "odd", "last-card", "last card", "full-width",
                            "dernière carte", "n impair"])
        if has_grid and not has_odd_rule:
            self.warnings.append(
                "⚠️  §6 Composants : grille de cards détectée mais comportement N impair non documenté. "
                "Ajouter : comportement last-card sur nombre impair "
                "(ex: last-card full-width, ou left-align, ou grille 2×N)."
            )

        # ── Densité section contact ───────────────────────────────────────
        # Vérifier que la section contact est documentée dans §5 ou §6
        has_contact = any(k in components_section.lower() for k in
                          ["contact", "formulaire", "form", "cta", "email"])
        if not has_contact:
            self.warnings.append(
                "⚠️  §6 Composants : section Contact/CTA non documentée. "
                "Définir la densité minimale (padding vertical max 96px, "
                "contenu minimum : titre + sous-titre + action)."
            )

        # ── Scroll cue hero ───────────────────────────────────────────────
        has_scroll_cue = any(k in animations_section.lower() for k in
                             ["scroll", "chevron", "indicator", "indicateur",
                              "scroll cue", "next section", "section suivante"])
        has_hero = any(k in self.content.lower() for k in
                       ["hero", "section hero", "première section"])
        if has_hero and not has_scroll_cue:
            self.warnings.append(
                "⚠️  §7 Motion : hero détecté mais scroll cue non documenté. "
                "Documenter le signal de transition vers la section suivante "
                "(chevron animé, ombre de transition, ou parallax subtle)."
            )

    def _validate_dark_mode(self):
        """Vérifie que la section Dark Mode est présente et correctement définie."""
        darkmode_section = self.sections.get("darkmode", "")

        if not darkmode_section:
            # Si fond principal < #333 → dark-first project → erreur bloquante
            colors_section = self.sections.get("colors", "")
            fond_hex = None
            for line in colors_section.splitlines():
                if any(k in line.lower() for k in ("fond", "background", "bg", "arrière")):
                    hexes = re.findall(r"#[0-9A-Fa-f]{6}", line)
                    if hexes:
                        fond_hex = hexes[0]
                        break
            if fond_hex:
                lum = self._relative_luminance(self._hex_to_rgb(fond_hex))
                if lum < 0.09:
                    self.errors.append(
                        f"❌ §8 Dark Mode absent mais fond principal sombre ({fond_hex}, lum={lum:.3f}). "
                        f"Projet dark-first : §8 est obligatoire. "
                        f"Documenter surface, texte-secondaire, bordure-dark."
                    )
                    return
            # Fond clair ou non détecté → warning seulement
            self.warnings.append(
                "⚠️  Section '## 8. Dark Mode' absente du DESIGN.md. "
                "Sans contrat dark mode explicite, l'implémentation sera improvisée — "
                "le slop revient par la fenêtre. "
                "Ajouter une section avec les tokens inversés (fond-dark, texte-dark, surface-dark)."
            )
            return

        # Vérifier qu'il y a des hex déclarés dans la section dark
        dark_hexes = re.findall(r"#[0-9A-Fa-f]{6}", darkmode_section)
        if len(dark_hexes) < 3:
            self.warnings.append(
                f"⚠️  Section Dark Mode insuffisante : {len(dark_hexes)} couleur(s) déclarée(s). "
                f"Minimum 3 requises (fond-dark, texte-dark, surface-dark)."
            )

        # Vérifier que les rôles minimaux sont présents
        required_dark_roles = ["fond", "texte", "surface"]
        missing = [r for r in required_dark_roles if r not in darkmode_section.lower()]
        if missing:
            self.warnings.append(
                f"⚠️  Rôles dark mode manquants : {', '.join(missing)}. "
                f"Déclarer explicitement fond-dark, texte-dark et surface-dark."
            )

        # Vérifier que le fond dark est bien sombre (luminosité < 30%)
        for line in darkmode_section.splitlines():
            if any(k in line.lower() for k in ("fond", "background", "bg")):
                hexes = re.findall(r"#[0-9A-Fa-f]{6}", line)
                if hexes:
                    lum = self._relative_luminance(self._hex_to_rgb(hexes[0]))
                    if lum > 0.09:  # luminosité relative > ~30% = pas assez sombre
                        self.warnings.append(
                            f"⚠️  Fond dark mode trop clair ({hexes[0]}, luminosité {lum:.2f}). "
                            f"Recommandé : < #333 pour un dark mode confortable."
                        )
                    break


    def _validate_mobile(self):
        """Valide la section Mobile (§9) si présente.
        Vérifie les unités natives (pt/dp/sp), touch targets,
        safe areas, et patterns d'animation système."""
        mobile_section = self.sections.get("mobile", "")

        if not mobile_section:
            # Pas une erreur — section optionnelle pour les projets web-only
            return

        # ── Unités natives ───────────────────────────────────────────────
        # Détecter les px hardcodés dans un contexte mobile natif
        # (iOS = pt, Android = dp, Flutter = logical pixels, RN = dp)
        platform_section = mobile_section.lower()
        is_native = any(k in platform_section for k in [
            "swiftui", "flutter", "jetpack", "compose", "react native", "react-native",
            "ios", "android", "uikit", "swift", "kotlin"
        ])

        if is_native:
            # Chercher des px hardcodés hors d'un contexte CSS
            px_in_native = re.findall(
                r"(?<!font-size:)(?<!padding:)(?<!margin:)\b(\d+)px\b",
                mobile_section
            )
            if px_in_native:
                self.warnings.append(
                    f"⚠️  Unités px dans contexte mobile natif : {px_in_native[:5]}. "
                    f"Utiliser pt (iOS), dp (Android), ou logical pixels (Flutter/RN)."
                )

        # ── Touch targets ─────────────────────────────────────────────────
        # iOS HIG : 44pt min, Android Material : 48dp min
        touch_target_mentioned = any(k in mobile_section.lower() for k in [
            "touch target", "tap target", "44pt", "44dp", "48dp", "48pt",
            "taille tactile", "zone tactile", "minimum tap"
        ])
        if not touch_target_mentioned:
            self.warnings.append(
                "⚠️  Taille minimale des touch targets non documentée dans §9 Mobile. "
                "iOS HIG : 44pt min, Material Design : 48dp min."
            )

        # ── Safe Areas ────────────────────────────────────────────────────
        safe_area_mentioned = any(k in mobile_section.lower() for k in [
            "safe area", "safeareainsets", "edgeinsets", "notch", "dynamic island",
            "home indicator", "status bar", "navigation bar", "insets"
        ])
        if not safe_area_mentioned:
            self.warnings.append(
                "⚠️  Gestion des Safe Areas non documentée dans §9 Mobile. "
                "Documenter comment le layout respecte notch/Dynamic Island/Home Indicator."
            )

        # ── Animations mobiles ────────────────────────────────────────────
        # Les animations système (spring, easeInOut) sont autorisées même > 400ms
        # car elles respectent le rythme natif de la plateforme
        anim_section = mobile_section
        ms_raw = re.findall(r"(\d+(?:\.\d+)?)\s*ms\b", anim_section)
        s_raw  = re.findall(r"(\d+(?:\.\d+)?)\s*s(?!econds)\b", anim_section)
        all_ms = [float(v) for v in ms_raw] + [float(v)*1000 for v in s_raw]

        # Exclure si spring/system mentionné (animations natives sans durée fixe)
        is_spring = any(k in anim_section.lower() for k in [
            "spring", "uispringtiming", "withspring", "animation.spring",
            "springanimation", "system animation", "animation système"
        ])
        if not is_spring:
            violations = [v for v in all_ms if v > 500]  # seuil + souple sur mobile
            if violations:
                self.warnings.append(
                    f"⚠️  Animations mobiles longues : {violations}ms. "
                    f"Sur mobile, privilégier spring() ou ≤ 400ms pour les transitions."
                )

        # ── Accessibilité mobile ──────────────────────────────────────────
        a11y_mentioned = any(k in mobile_section.lower() for k in [
            "accessibilityLabel", "contentdescription", "talkback", "voiceover",
            "accessibilité", "accessibility", "a11y", "semantics"
        ])
        if not a11y_mentioned:
            self.warnings.append(
                "⚠️  Accessibilité mobile non documentée dans §9. "
                "Mentionner VoiceOver (iOS) / TalkBack (Android) et les labels d'accessibilité."
            )

        # Si la section est bien remplie, confirmer
        if mobile_section and len(mobile_section) > 200:
            pass  # Pas de message inutile


    def _validate_dark_mode_required(self):
        """§8 est obligatoire si le fond principal est sombre (lum < 9%)."""
        darkmode_section = self.sections.get("darkmode", "")
        if darkmode_section:
            return  # Déjà validé par _validate_dark_mode()

        # Chercher le fond dans §2
        colors_section = self.sections.get("colors", "")
        hex_pat = r"#[0-9A-Fa-f]{6}"

        # La première ligne avec "Fond" ou "Background" ou "bg"
        fond_hex = None
        for line in colors_section.splitlines():
            if any(k in line.lower() for k in ("fond", "background", "bg")):
                hexes = re.findall(hex_pat, line)
                if hexes:
                    fond_hex = hexes[0]
                    break

        if fond_hex:
            lum = self._relative_luminance(self._hex_to_rgb(fond_hex))
            if lum < 0.09:  # fond sombre = projet dark-first
                self.errors.append(
                    f"❌ §8 Dark Mode absent mais fond principal sombre "
                    f"({fond_hex}, lum={lum:.3f}). "
                    f"Projet dark-first : §8 est obligatoire. "
                    f"Documenter surface, texte-secondaire, bordure-dark."
                )

    def _validate_section_density(self):
        """Vérifie que les sections clés ont une densité suffisante."""
        components_section = self.sections.get("components", "")

        # Vérifier que la section Contact/CTA est documentée dans §6
        has_contact = any(k in components_section.lower() for k in [
            "contact", "cta", "footer", "coordonnées", "mail", "email",
            "section contact", "section cta"
        ])
        if not has_contact:
            self.warnings.append(
                "⚠️  §6 Composants : section Contact/CTA non documentée. "
                "Définir la densité minimale (padding vertical max 96px, "
                "contenu minimum : titre + sous-titre + action)."
            )



    def _validate_threejs(self):
        """Valide la section Three.js (§10) si présente."""
        threejs_section = self.sections.get("threejs", "")

        if not threejs_section:
            all_content = self.content.lower()
            three_mentioned = any(k in all_content for k in [
                "three.js", "threejs", "webgl", "webglrenderer",
                "from 'three'", 'from "three"'
            ])
            if three_mentioned:
                self.warnings.append(
                    "⚠️  Three.js détecté dans le DESIGN.md mais §10 absent. "
                    "Ajouter '## 10. Three.js' avec : type de scène, budget géométrie, "
                    "pixel ratio cap, dispose strategy, fallback WebGL."
                )
            return

        sec = threejs_section.lower()
        self._has_threejs = True  # flag pour exempter les durées Three.js dans §7

        # Type de scène
        if not any(k in sec for k in ["hero", "background", "viewer", "scroll",
                                       "interactive", "particle", "product", "ambient"]):
            self.warnings.append(
                "⚠️  §10 Three.js : type de scène non documenté. "
                "Préciser : hero background | interactive viewer | scroll-driven | particles."
            )

        # Pixel ratio cap
        if not any(k in sec for k in ["devicepixelratio", "pixel ratio", "pixelratio",
                                       "dpr", "math.min", "cap", "capé"]):
            self.warnings.append(
                "⚠️  §10 Three.js : pixel ratio non documenté. "
                "Ajouter : Math.min(devicePixelRatio, 2) — cap obligatoire "
                "(Retina 3x = 9 pixels/CSS px, sans cap GPU coût × 2.25)."
            )

        # Dispose strategy
        if not any(k in sec for k in ["dispose", "teardown", "cleanup",
                                       "nettoyage", "memory", "vram"]):
            self.warnings.append(
                "⚠️  §10 Three.js : stratégie dispose non documentée. "
                "Three.js ne libère jamais la VRAM automatiquement — "
                "documenter geometry.dispose() + material.dispose() + texture.dispose()."
            )

        # Fallback WebGL
        if not any(k in sec for k in ["fallback", "webgl", "support",
                                       "dégradé", "no-webgl", "image statique"]):
            self.warnings.append(
                "⚠️  §10 Three.js : fallback WebGL non documenté. "
                "~2% des utilisateurs n'ont pas WebGL — définir le comportement "
                "(image statique, canvas 2D, ou message d'erreur)."
            )

        # prefers-reduced-motion
        if not any(k in sec for k in ["prefers-reduced-motion", "reduced-motion",
                                       "reducedmotion", "figé", "statique"]):
            self.warnings.append(
                "⚠️  §10 Three.js : prefers-reduced-motion non documenté. "
                "Scène figée ou rotation lente si reduced-motion activé."
            )

        # Renderer singleton
        if not any(k in sec for k in ["renderer", "webglrenderer",
                                       "instance", "singleton", "unique"]):
            self.warnings.append(
                "⚠️  §10 Three.js : stratégie renderer non documentée. "
                "Un seul WebGLRenderer par page — navigateurs limités à 8-16 contextes GPU."
            )

    def _print_report(self):
        """Affiche le rapport de validation"""
        print("\n" + "=" * 60)
        print("🎨 DESIGN VALIDATION REPORT")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ ERREURS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n⚠️  AVERTISSEMENTS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ VALIDATION RÉUSSIE - Aucune erreur détectée!")

        print("\n" + "=" * 60)
        if self.errors:
            print(f"❌ RÉSULTAT: ÉCHOUÉ ({len(self.errors)} erreurs)")
        elif self.warnings:
            print(f"⚠️  RÉSULTAT: RÉUSSI AVEC AVERTISSEMENTS ({len(self.warnings)} avertissements)")
        else:
            print("✅ RÉSULTAT: RÉUSSI - Prêt pour le codage!")
        print("=" * 60 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_design.py DESIGN.md [--strict]")
        sys.exit(1)

    filepath = sys.argv[1]
    strict = "--strict" in sys.argv

    validator = DesignValidator(filepath, strict)
    success = validator.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()