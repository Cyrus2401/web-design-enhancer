#!/usr/bin/env python3
"""
AI Slop Detector - Détecte les antipatterns courants du design généré par IA

Détecte:
- Icônes génériques (Lucide, FontAwesome)
- Gradients clichés
- Sections template (Hero, Features, CTA)
- Buzzwords vagues
- Polices génériques
- Couleurs non-justifiées
- Espacements incohérents

Usage:
    python3 detect_ai_slop.py --design DESIGN.md --code ./client/src
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter


class AISloPDetector:
    """Détecteur d'antipatterns AI slop"""

    # Icônes génériques et artefacts "Odeur d'IA" — web et mobile
    GENERIC_ICONS = {
        # Web (Lucide / FontAwesome)
        "sparkles", "zap", "cog", "network", "arrow", "check", "star",
        "heart", "user", "settings", "menu", "search", "bell", "mail",
        "download", "upload", "trash", "edit", "copy", "share", "link",
        "eye", "lock", "unlock", "calendar", "clock", "map", "phone",
        "play", "pause", "volume", "wifi", "battery", "sun", "moon",
        "magic", "stars", "bot", "robot", "ai", "brain",
        # Mobile — SF Symbols génériques (iOS)
        "person.fill", "house.fill", "gear", "bell.fill", "magnifyingglass",
        "ellipsis", "xmark", "chevron.right", "arrow.right", "plus.circle",
        # Mobile — Material Icons génériques (Android)
        "Icons.Default.Home", "Icons.Default.Person", "Icons.Default.Settings",
        "Icons.Default.Notifications", "Icons.Default.Search", "Icons.Default.Menu",
        "Icons.Default.Add", "Icons.Default.Close", "Icons.Default.ArrowBack",
        # Mobile — Expo Icons génériques (React Native)
        "Ionicons.home", "Ionicons.person", "Ionicons.settings",
        "MaterialIcons.home", "MaterialIcons.person",
    }

    # Antipatterns mobiles spécifiques
    MOBILE_SLOP_PATTERNS = [
        # Hardcoded screen dimensions (iPhone 13 = 390, Pixel 6 = 412...)
        (r"width\s*[:=]\s*(?:375|390|393|414|375\.0|390\.0)",
         "Largeur d'écran iPhone hardcodée — utiliser .frame(maxWidth: .infinity) ou LayoutBuilder"),
        (r"width\s*[:=]\s*(?:360|393|412|411)",
         "Largeur d'écran Android hardcodée — utiliser responsive layout"),
        # Touch targets trop petits
        (r"\.frame\s*\(.*?(?:width|height)\s*:\s*([1-3]\d)",
         "Touch target probablement trop petit (< 40pt) — minimum iOS HIG 44pt"),
        # Status bar hardcodée
        (r"(?:padding|margin).*?(?:top)\s*:\s*(?:44|20|47)",
         "Hauteur de status bar hardcodée — utiliser SafeAreaInsets ou useSafeAreaInsets()"),
        # Couleurs hardcodées au lieu de system colors
        (r"Color\(red:\s*\d+,\s*green:\s*\d+",
         "Couleur RGB hardcodée SwiftUI — préférer Color(.systemBackground) ou les semantic colors"),
        # Pas d'adaptive colors (dark mode non géré)
        (r"backgroundColor\s*=\s*UIColor\.white",
         "backgroundColor blanc fixe — utiliser .systemBackground pour le dark mode automatique"),
    ]

    # Patterns pour détecter les logos inventés ou placeholders graphiques
    LOGO_PLACEHOLDERS = [
        (r"logo-placeholder", "Placeholder de logo générique"),
        (r"your-logo", "Texte de logo par défaut"),
        (r"brandname", "Nom de marque générique"),
        (r"company-name", "Nom d'entreprise générique"),
    ]

    # Patterns pour détecter l'utilisation par défaut de shadcn/ui (sans personnalisation)
    SHADCN_DEFAULT_PATTERNS = [
        (r"<Button\s*[^>]*?variant=\"default\"", "Bouton shadcn/ui avec variant par défaut"),
        (r"<Input(?!\s[^>]*className)[^>]*/?>", "Input shadcn/ui sans className de personnalisation"),
    ]

    # Badges statut IA non demandés — ● ATMOSPHÈRE EXCELLENTE, LIVE NOW, etc.
    STATUS_BADGE_PATTERNS = [
        (r"[●•◉]\s*[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ\s]{4,}",
         "Point coloré + texte statut majuscule"),
        (r"\b(?:PREMIUM\s+QUALITY|ULTRA\s+FAST|HIGH\s+PERFORMANCE|LIVE\s+NOW|TOP\s+RATED|ATMOSPHÈRE\s+\w+)\b",
         "Syntagme statut IA (jamais un label de données légitime)"),
        (r"w-2\s+h-2\s+rounded-full\s+bg-(?:green|emerald|lime|teal)-\d{3}",
         "Point vert décoratif Tailwind (indicateur statut IA)"),
        (r"animate-pulse[^\"]*rounded-full|rounded-full[^\"]*animate-pulse",
         "Point animé (pulse) décoratif — signal IA fréquent"),
    ]

    # Gradients clichés
    CLICHE_GRADIENTS = [
        (r"(?:from|to).*?blue.*?(?:from|to).*?purple|purple.*?blue", "bleu→violet"),
        (r"(?:from|to).*?pink.*?(?:from|to).*?purple|purple.*?pink", "rose→violet"),
        (r"(?:from|to).*?cyan.*?(?:from|to).*?blue|blue.*?cyan", "cyan→bleu"),
        (r"(?:from|to).*?red.*?(?:from|to).*?orange|orange.*?red", "rouge→orange"),
    ]

    # Buzzwords vagues
    BUZZWORDS = {
        "premium": "Remplacer par description précise (ex: 'Contraste élevé, espacements généreux')",
        "moderne": "Remplacer par description précise (ex: 'Minimaliste', 'Géométrique')",
        "élégant": "Remplacer par description précise (ex: 'Espacements généreux', 'Typographie hiérarchisée')",
        "magnifique": "Remplacer par description précise",
        "incroyable": "Remplacer par description précise",
        "unique": "Remplacer par description précise",
        "innovant": "Remplacer par description précise",
        "futuriste": "Utiliser si justifié par choix visuels concrets",
    }

    # Sections template génériques
    TEMPLATE_SECTIONS = {
        "hero": "Section héroïque",
        "features": "Grille de fonctionnalités",
        "testimonials": "Section témoignages",
        "cta": "Appel à l'action",
        "pricing": "Tarification",
        "faq": "FAQ",
        "footer": "Pied de page",
    }

    # Polices génériques
    GENERIC_FONTS = {
        "helvetica", "arial", "times new roman", "georgia", "verdana",
        "courier", "comic sans", "impact", "trebuchet", "palatino",
    }

    def __init__(self, design_file: str = None, code_dir: str = None):
        self.design_file = Path(design_file) if design_file else None
        self.code_dir = Path(code_dir) if code_dir else None
        self.issues: List[Dict] = []
        self.score = 100  # Score de qualité (0-100)

        # Whitelist .slop-ignore — chargée depuis la racine du projet
        self._whitelist = self._load_slop_ignore()

    # ── .slop-ignore ──────────────────────────────────────────────────────────

    def _load_slop_ignore(self) -> Dict[str, List[str]]:
        """Charge le fichier .slop-ignore depuis la racine du projet."""
        whitelist: Dict[str, List[str]] = {
            "icons": [], "buzzwords": [], "gradients": [], "badges": [], "files": []
        }
        # Chercher dans le répertoire courant et les parents immédiats
        candidates = [
            Path(".slop-ignore"),
            Path("../.slop-ignore"),
            Path(__file__).parent.parent / ".slop-ignore",
        ]
        ignore_path = next((p for p in candidates if p.exists()), None)
        if not ignore_path:
            return whitelist

        current_section = None
        for raw_line in ignore_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            # Section header : [icons]
            section_match = re.match(r"^\[(\w+)\]$", line)
            if section_match:
                current_section = section_match.group(1).lower()
                continue
            # Entrée : "search  # justification"
            if current_section and current_section in whitelist:
                token = line.split("#")[0].strip()  # retirer le commentaire inline
                justification = line.split("#")[1].strip() if "#" in line else ""
                # Règle : sans justification, l'entrée est ignorée (sécurité)
                if token and justification:
                    whitelist[current_section].append(token.lower())

        if any(whitelist.values()):
            loaded = sum(len(v) for v in whitelist.values())
            print(f"  📋 .slop-ignore chargé — {loaded} exemption(s)")

        return whitelist

    def _add_issue(self, issue_type: str, message: str, suggestion: str = "", severity: int = 1):
        """Helper unifié pour ajouter un problème et déduire le score."""
        self.issues.append({
            "type": issue_type.lower(),
            "severity": "warning" if severity == 1 else "error",
            "message": message,
            "suggestion": suggestion,
        })
        self.score -= 5 * severity

    def _is_whitelisted(self, section: str, token: str) -> bool:
        """Retourne True si le token est exempté dans la section donnée."""
        return token.lower() in self._whitelist.get(section, [])

    def _file_is_ignored(self, path) -> bool:
        """Retourne True si le fichier est dans la liste d'ignorés."""
        path_str = str(path).replace("\\", "/")
        for pattern in self._whitelist.get("files", []):
            if pattern.rstrip("/") in path_str:
                return True
        return False


    def _detect_mobile_slop(self, content: str, file_path: Path = None):
        """Détecte les antipatterns mobiles natifs dans le code."""
        ctx = str(file_path.name) if file_path else "code"

        # Détecter si c'est du code mobile natif
        is_swift    = file_path and file_path.suffix in {".swift"}
        is_kotlin   = file_path and file_path.suffix in {".kt", ".kts"}
        is_dart     = file_path and file_path.suffix in {".dart"}
        is_rn       = file_path and file_path.suffix in {".tsx", ".jsx"} and (
                        "react-native" in content.lower() or
                        "StyleSheet.create" in content or
                        "from 'react-native'" in content
                    )

        if not (is_swift or is_kotlin or is_dart or is_rn):
            return  # Pas du code mobile natif — skip

        import re as _re

        for pattern, description in self.MOBILE_SLOP_PATTERNS:
            if _re.search(pattern, content):
                self._add_issue(
                    "MOBILE_SLOP",
                    f"{description} [{ctx}]",
                    "Utiliser les composants et APIs natifs de la plateforme",
                    severity=2
                )

        # Vérification dark mode adaptatif
        if is_swift and "Color.white" in content and "colorScheme" not in content:
            self._add_issue(
                "MOBILE_SLOP",
                f"Couleur blanche fixe sans adaptation dark mode [{ctx}]",
                "Utiliser Color(.systemBackground) ou @Environment(.colorScheme)",
                severity=1
            )

        if is_kotlin and "Color.White" in content and "isSystemInDarkTheme" not in content:
            self._add_issue(
                "MOBILE_SLOP",
                f"Color.White fixe sans dark mode adaptatif [{ctx}]",
                "Utiliser MaterialTheme.colorScheme.background",
                severity=1
            )

        # Vérification accessibilité minimale
        if is_swift and "Image(" in content:
            has_label = "accessibilityLabel" in content or "Label(" in content
            if not has_label:
                self._add_issue(
                    "MOBILE_SLOP",
                    f"Image SwiftUI sans accessibilityLabel [{ctx}]",
                    "Ajouter .accessibilityLabel(String) sur chaque Image",
                    severity=1
                )

        if is_kotlin and "Image(" in content and "contentDescription" not in content:
            self._add_issue(
                "MOBILE_SLOP",
                f"Image Compose sans contentDescription [{ctx}]",
                "Ajouter contentDescription = String ou null si decoratif",
                severity=1
            )

    def run(self) -> bool:
        """Exécute la détection complète"""
        if self.design_file:
            self._check_design_file()

        if self.code_dir:
            self._check_code_directory()

        self._print_report()
        return self.score >= 80  # Passe si score ≥ 80

    def _check_design_file(self):
        """Vérifie le fichier DESIGN.md"""
        if not self.design_file.exists():
            print(f"❌ Fichier non trouvé: {self.design_file}")
            return

        content = self.design_file.read_text(encoding="utf-8")

        # Détecte l'utilisation par défaut de shadcn/ui
        self._detect_shadcn_defaults(content)

        # Détecte les placeholders de logo
        self._detect_logo_placeholders(content)

        # Détecte les buzzwords
        self._detect_buzzwords(content)

        # Détecte les icônes génériques
        self._detect_generic_icons(content)

        # Détecte les gradients clichés
        self._detect_cliche_gradients(content)

        # Détecte les polices génériques
        self._detect_generic_fonts(content)

        # Détecte les badges statut IA
        self._detect_status_badges(content)

    def _check_code_directory(self):
        """Vérifie les fichiers de code"""
        if not self.code_dir.exists():
            print(f"❌ Répertoire non trouvé: {self.code_dir}")
            return

        # Vérifie les fichiers web (TSX/JSX) et mobile natif (Swift/Kotlin/Dart)
        mobile_web_exts = ["*.tsx", "*.jsx", "*.swift", "*.kt", "*.kts", "*.dart"]
        for ext in mobile_web_exts:
            for file_path in self.code_dir.rglob(ext):
                if not self._file_is_ignored(file_path):
                    self._check_code_file(file_path)

        # Détecte l'utilisation par défaut de shadcn/ui dans le code
        for file_path in self.code_dir.rglob("*.tsx"):
            self._detect_shadcn_defaults(file_path.read_text(encoding="utf-8", errors="ignore"), file_path)
        for file_path in self.code_dir.rglob("*.jsx"):
            self._detect_shadcn_defaults(file_path.read_text(encoding="utf-8", errors="ignore"), file_path)

        # Détecte les badges statut IA dans le code
        for file_path in self.code_dir.rglob("*.tsx"):
            self._detect_status_badges(file_path.read_text(encoding="utf-8", errors="ignore"), file_path)
        for file_path in self.code_dir.rglob("*.jsx"):
            self._detect_status_badges(file_path.read_text(encoding="utf-8", errors="ignore"), file_path)

    def _check_code_file(self, file_path: Path):
        """Vérifie un fichier de code"""
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        # Détecte les imports Lucide
        lucide_imports = re.findall(r"from\s+['\"]lucide-react['\"].*?import\s+{([^}]+)}", content)
        if lucide_imports:
            icons = [i.strip() for i in lucide_imports[0].split(",")]
            generic = [i for i in icons if i.lower() in self.GENERIC_ICONS]

            if generic:
                self.issues.append({
                    "type": "generic_icons",
                    "file": str(file_path),
                    "severity": "warning",
                    "message": f"Icônes Lucide génériques: {', '.join(generic)}",
                    "suggestion": "Utiliser custom SVG ou pack d'icônes cohérent"
                })
                self.score -= 5 * len(generic)

        # Détecte les sections template
        template_count = sum(1 for section in self.TEMPLATE_SECTIONS if section in content.lower())
        if template_count >= 4:
            self.issues.append({
                "type": "template_structure",
                "file": str(file_path),
                "severity": "warning",
                "message": f"Structure template générique ({template_count} sections)",
                "suggestion": "Considérer une approche plus unique"
            })
            self.score -= 10

        # Détecte les antipatterns mobiles natifs
        self._detect_mobile_slop(content, file_path)


    def _detect_status_badges(self, content: str, file_path: Path = None):
        """Détecte les badges statut IA non demandés (● ATMOSPHÈRE EXCELLENTE, LIVE NOW, etc.)"""
        for pattern, message in self.STATUS_BADGE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                issue = {
                    "type": "status_badge",
                    "severity": "warning",
                    "message": f"Badge statut IA: {message}",
                    "suggestion": (
                        "Supprimer ce badge — non demandé, signal IA immédiat. "
                        "Si un statut est fonctionnellement nécessaire, le justifier dans DESIGN.md."
                    )
                }
                if file_path:
                    issue["file"] = str(file_path)
                self.issues.append(issue)
                self.score -= 8

    def _detect_buzzwords(self, content: str):
        """Détecte les buzzwords vagues"""
        for buzzword, suggestion in self.BUZZWORDS.items():
            if self._is_whitelisted("buzzwords", buzzword):
                continue
            if re.search(rf"\b{buzzword}\b", content, re.IGNORECASE):
                self.issues.append({
                    "type": "buzzword",
                    "severity": "warning",
                    "message": f"Buzzword vague: '{buzzword}'",
                    "suggestion": suggestion
                })
                self.score -= 3

    def _detect_generic_icons(self, content: str):
        """Détecte les icônes génériques"""
        for icon in self.GENERIC_ICONS:
            if self._is_whitelisted("icons", icon):
                continue
            if re.search(rf"\b{icon}\b", content, re.IGNORECASE):
                self.issues.append({
                    "type": "generic_icon",
                    "severity": "info",
                    "message": f"Icône générique: {icon}",
                    "suggestion": "Considérer custom SVG si utilisée de manière non-standard"
                })
                self.score -= 1

    def _detect_cliche_gradients(self, content: str):
        """Détecte les gradients clichés"""
        for pattern, name in self.CLICHE_GRADIENTS:
            if re.search(pattern, content, re.IGNORECASE):
                self.issues.append({
                    "type": "cliche_gradient",
                    "severity": "warning",
                    "message": f"Gradient cliché: {name}",
                    "suggestion": "Justifier par rôle sémantique ou considérer alternative"
                })
                self.score -= 5

    def _detect_generic_fonts(self, content: str):
        """Détecte les polices génériques"""
        for font in self.GENERIC_FONTS:
            if re.search(rf"\b{font}\b", content, re.IGNORECASE):
                self.issues.append({
                    "type": "generic_font",
                    "severity": "error",
                    "message": f"Police générique: {font}",
                    "suggestion": "Utiliser Google Fonts ou custom font"
                })
                self.score -= 10

    def _detect_logo_placeholders(self, content: str, file_path: Path = None):
        """Détecte les placeholders de logo ou noms génériques"""
        for pattern, message in self.LOGO_PLACEHOLDERS:
            if re.search(pattern, content, re.IGNORECASE):
                issue = {
                    "type": "logo_placeholder",
                    "severity": "error",
                    "message": f"Logo/Nom générique détecté: {message}",
                    "suggestion": "Utiliser un logo textuel stylisé (font-bold tracking-tight uppercase) si aucun logo n'est fourni."
                }
                if file_path:
                    issue["file"] = str(file_path)
                self.issues.append(issue)
                self.score -= 10

    def _detect_shadcn_defaults(self, content: str, file_path: Path = None):
        """Détecte l'utilisation par défaut de shadcn/ui"""
        for pattern, message in self.SHADCN_DEFAULT_PATTERNS:
            if re.search(pattern, content):
                issue = {
                    "type": "shadcn_default",
                    "severity": "warning",
                    "message": f"Shadcn/ui par défaut: {message}",
                    "suggestion": "Personnaliser les composants shadcn/ui via Tailwind CSS et les tokens de design."
                }
                if file_path:
                    issue["file"] = str(file_path)
                self.issues.append(issue)
                self.score -= 5

    def _print_report(self):
        """Affiche le rapport de détection"""
        print("\n" + "=" * 70)
        print("🚨 AI SLOP DETECTION REPORT")
        print("=" * 70)

        if not self.issues:
            print("\n✅ AUCUN ANTIPATTERN DÉTECTÉ!")
        else:
            print(f"\n⚠️  {len(self.issues)} problèmes détectés:\n")

            # Groupe par type
            by_type = {}
            for issue in self.issues:
                issue_type = issue["type"]
                if issue_type not in by_type:
                    by_type[issue_type] = []
                by_type[issue_type].append(issue)

            for issue_type in sorted(by_type.keys()):
                print(f"\n🔴 {issue_type.upper()}:")
                for issue in by_type[issue_type]:
                    severity = issue.get("severity", "info")
                    emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(severity, "•")

                    print(f"  {emoji} {issue['message']}")
                    if "file" in issue:
                        print(f"     Fichier: {issue['file']}")
                    print(f"     💡 {issue['suggestion']}")

        # Score final
        print("\n" + "-" * 70)
        print(f"📊 SCORE DE QUALITÉ: {self.score}/100")

        if self.score >= 80:
            print("✅ RÉSULTAT: BON - Prêt pour la livraison")
        elif self.score >= 60:
            print("⚠️  RÉSULTAT: ACCEPTABLE - Corriger les avertissements")
        else:
            print("❌ RÉSULTAT: FAIBLE - Revoir la conception")

        print("=" * 70 + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Détecteur d'antipatterns AI slop")
    parser.add_argument("--design", help="Fichier DESIGN.md à vérifier")
    parser.add_argument("--code", help="Répertoire de code à auditer")

    args = parser.parse_args()

    if not args.design and not args.code:
        print("Usage: python3 detect_ai_slop.py --design DESIGN.md --code ./client/src")
        sys.exit(1)

    detector = AISloPDetector(design_file=args.design, code_dir=args.code)
    success = detector.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
