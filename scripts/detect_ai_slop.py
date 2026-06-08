#!/usr/bin/env python3
"""
AI Slop Detector - Detects common antipatterns of AI-generated design

Detects:
- Generic icons (Lucide, FontAwesome)
- Cliche gradients
- Template sections (Hero, Features, CTA)
- Vague buzzwords
- Generic fonts
- Unjustified colors
- Inconsistent spacings

Usage:
    python3 detect_ai_slop.py --design DESIGN.md --code ./client/src
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter


class AISloPDetector:
    """AI slop antipattern detector"""

    # Generic icons and "AI smell" artifacts - web and mobile
    GENERIC_ICONS = {
        # Web (Lucide / FontAwesome)
        "sparkles", "zap", "cog", "network", "arrow", "check", "star",
        "heart", "user", "settings", "menu", "search", "bell", "mail",
        "download", "upload", "trash", "edit", "copy", "share", "link",
        "eye", "lock", "unlock", "calendar", "clock", "map", "phone",
        "play", "pause", "volume", "wifi", "battery", "sun", "moon",
        "magic", "stars", "bot", "robot", "ai", "brain",
        # Mobile - generic SF Symbols (iOS)
        "person.fill", "house.fill", "gear", "bell.fill", "magnifyingglass",
        "ellipsis", "xmark", "chevron.right", "arrow.right", "plus.circle",
        # Mobile - generic Material Icons (Android)
        "Icons.Default.Home", "Icons.Default.Person", "Icons.Default.Settings",
        "Icons.Default.Notifications", "Icons.Default.Search", "Icons.Default.Menu",
        "Icons.Default.Add", "Icons.Default.Close", "Icons.Default.ArrowBack",
        # Mobile - generic Expo Icons (React Native)
        "Ionicons.home", "Ionicons.person", "Ionicons.settings",
        "MaterialIcons.home", "MaterialIcons.person",
    }

    # Mobile-specific antipatterns
    MOBILE_SLOP_PATTERNS = [
        # Hardcoded screen dimensions (iPhone 13 = 390, Pixel 6 = 412...)
        (r"width\s*[:=]\s*(?:375|390|393|414|375\.0|390\.0)",
         "Hardcoded iPhone screen width - use .frame(maxWidth: .infinity) or LayoutBuilder"),
        (r"width\s*[:=]\s*(?:360|393|412|411)",
         "Hardcoded Android screen width - use responsive layout"),
        # Touch targets too small
        (r"\.frame\s*\(.*?(?:width|height)\s*:\s*([1-3]\d)",
         "Touch target probably too small (< 40pt) - iOS HIG minimum is 44pt"),
        # Hardcoded status bar
        (r"(?:padding|margin).*?(?:top)\s*:\s*(?:44|20|47)",
         "Hardcoded status bar height - use SafeAreaInsets or useSafeAreaInsets()"),
        # Hardcoded colors instead of system colors
        (r"Color\(red:\s*\d+,\s*green:\s*\d+",
         "Hardcoded SwiftUI RGB color - prefer Color(.systemBackground) or semantic colors"),
        # No adaptive colors (dark mode not handled)
        (r"backgroundColor\s*=\s*UIColor\.white",
         "Fixed white backgroundColor - use .systemBackground for automatic dark mode"),
    ]

    # Patterns to detect invented logos or graphic placeholders
    LOGO_PLACEHOLDERS = [
        (r"logo-placeholder", "Generic logo placeholder"),
        (r"your-logo", "Default logo text"),
        (r"brandname", "Generic brand name"),
        (r"company-name", "Generic company name"),
    ]

    # Patterns to detect default shadcn/ui usage (no customization)
    SHADCN_DEFAULT_PATTERNS = [
        (r"<Button\s*[^>]*?variant=\"default\"", "shadcn/ui Button with default variant"),
        (r"<Input(?!\s[^>]*className)[^>]*/?>", "shadcn/ui Input without customization className"),
    ]

    # AI status badges that were never requested - ATMOSPHERE EXCELLENT, LIVE NOW, etc.
    STATUS_BADGE_PATTERNS = [
        # One-off status badges
        (r"[●•◉]\s*[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ\s]{4,}",
         "Colored dot + uppercase status text"),
        (r"\b(?:PREMIUM\s+QUALITY|ULTRA\s+FAST|HIGH\s+PERFORMANCE|LIVE\s+NOW|TOP\s+RATED|ATMOSPHÈRE\s+\w+)\b",
         "AI status phrase (never a legitimate data label)"),
        (r"w-2\s+h-2\s+rounded-full\s+bg-(?:green|emerald|lime|teal)-\d{3}",
         "Decorative green dot Tailwind (AI status indicator)"),
        (r"animate-pulse[^\"]*rounded-full|rounded-full[^\"]*animate-pulse",
         "Animated (pulse) decorative dot - frequent AI signal"),
        # Invented system status badges (JSX/TSX pattern)
        # Restricted to JSX context (between > and <) to avoid false positives
        # on TypeScript enums (PaymentStatus.PAID: SUCCESS), SQL/CSS code comments
        # (SELECT NAME:, MEDIA QUERIES:), or JS constants.
        (r">[\s]*[A-Z][A-Z_]{3,}\s*:\s*[A-Z][A-Z_]+[\s]*<",
         "Invented system status badge e.g. '<span>SYNC_NODE: STABLE</span>' - never real data"),
        (r"\b(?:sync_node|sys_info|sys_status|sync_status)\b",
         "Generic system status indicator - strong AI signal"),
        # ALL_CAPS on buttons and labels (only in JSX/component context)
        # Avoids false positives on legitimate CSS (utility badges, .uppercase Tailwind alone)
        (r"text-transform\s*:\s*uppercase[^}]{0,200}(?:button|\.btn|\.cta|nav-link|menu-item)",
         "text-transform: uppercase on button/CTA - AI slop pattern (ENVOYER UN MAIL, GET STARTED)"),
        (r"(?:className|class)\s*=\s*\"[^\"]*\b(?:uppercase|tracking-widest)\b[^\"]*\b(?:btn|button|cta|nav-link)\b",
         "Uppercase class on button/CTA - ALL CAPS on CTAs = frequent AI pattern"),
        # Decorative GitHub stars/likes badges
        (r"<(?:Star|StarIcon|StarFilled)\s*/>",
         "JSX star icon with no functional context - decorative GitHub stars badge"),
        (r"(?:starCount|star_count|stargazers_count).*?\d+",
         "Hardcoded GitHub star counter - static data not tied to any API"),
        # Unjustified ALL_CAPS labels inside cards
        # Restricted to visible JSX context (between > and <) to avoid false positives
        # on SQL ("SELECT NAME:"), CSS comments ("MEDIA QUERIES:"), JSDoc, env files.
        (r">\s*[A-Z][A-Z ]{6,}\s*:\s*<",
         "ALL_CAPS label inside a card e.g. '>COMMANDE INSTALLATION:<' - not documented in DESIGN.md"),
        # Invented system identifiers - only if NOT preceded by process.env.,
        # import.meta.env., a slash (path), or a dot (property access).
        # Preserves legitimate usage: process.env.API_KEY, NODE_ENV, API_URL as a constant.
        # Targets: SYS_*, NODE_* (except NODE_ENV), API_* used as JSX text badges.
        (r"(?<![.\w/])\b(?:SYS_INFO|SYS_STATUS|SYS_NODE|SYS_PING|NODE_STATUS|API_HEALTH|API_LIVE)\b",
         "Invented system identifier - strong AI slop signal"),
        # ALL_CAPS button text (ENVOYER UN MAIL, GET STARTED, etc.)
        # Excludes common abbreviations (ID, URL, API, FAQ, CTA, OK, NEW, PRO)
        # and short accessibility patterns (ARIA labels in uppercase).
        (r">\s*(?!(?:ID|URL|API|FAQ|CTA|OK|NEW|PRO|VIP|GDPR|RGPD|ALL|TOP|HOT|END|YES|NO|ON|OFF)\s*<)"
         r"[A-Z][A-Z\s]{5,30}<",
         "ALL_CAPS button text in HTML - ALL CAPS on CTAs = AI pattern"),
        # Star icon JSX patterns
        (r"<(?:Star|StarIcon|StarFilled|FaStar|BsStar)\s*[^>]*/?>",
         "JSX star icon - decorative GitHub stars badge"),
        # Radial gradient not documented in §1
        (r"radial-gradient\s*\([^)]{20,}\)",
         "Radial gradient in CSS - document in §1 if intentional"),
        # Featured card variants not documented
        (r"(?:border|ring)-(?:blue|accent|primary)-\d{3}[^;]*(?:card|Card|projet|project)",
         "Card with colored 'featured' border - variant not documented in §6"),
    ]

    # Cliche gradients
    CLICHE_GRADIENTS = [
        (r"(?:from|to).*?blue.*?(?:from|to).*?purple|purple.*?blue", "blue->purple"),
        (r"(?:from|to).*?pink.*?(?:from|to).*?purple|purple.*?pink", "pink->purple"),
        (r"(?:from|to).*?cyan.*?(?:from|to).*?blue|blue.*?cyan", "cyan->blue"),
        (r"(?:from|to).*?red.*?(?:from|to).*?orange|orange.*?red", "red->orange"),
    ]


    # Three.js antipatterns - detected in .js/.ts/.jsx/.tsx
    THREEJS_SLOP_PATTERNS = [
        # Geometry inside animate() = critical VRAM leak
        (r"new\s+THREE\.\w+Geometry\s*\([^)]*\)[^}]{0,200}requestAnimationFrame",
         "Geometry created inside animate() - new GPU buffer each frame, VRAM exhausted in seconds"),
        (r"requestAnimationFrame[^}]{0,200}new\s+THREE\.\w+Geometry",
         "Geometry created inside the render loop - critical VRAM leak"),
        # Renderer recreated = exhausts GPU contexts (limit 8-16)
        (r"function\s+\w+\s*\([^)]*\)[^}]{0,300}new\s+THREE\.WebGLRenderer",
         "WebGLRenderer created inside a repeatedly-called function - GPU context leak"),
        (r"useEffect[^}]{0,400}new\s+THREE\.WebGLRenderer",
         "WebGLRenderer in useEffect without cleanup - recreated on every React render"),
        # Pixel ratio with no cap = GPU cost x2.25 on Retina 3x
        (r"setPixelRatio\s*\(\s*window\.devicePixelRatio\s*\)",
         "setPixelRatio without cap - Retina 3x = 9 px/CSS px. Use Math.min(devicePixelRatio, 2)"),
        # Raycaster created inside the event handler = allocation per mousemove
        (r"addEventListener.{0,20}(?:mousemove|pointermove).{0,200}new THREE.Raycaster",
         "new THREE.Raycaster() inside mousemove - 200+ allocations/sec. Create once, reuse"),
        # Material duplicated in a loop
        (r"for\s*\([^)]+\)[^}]{0,200}new\s+THREE\.Mesh(?:Standard|Phong|Lambert)Material",
         "Material recreated in a loop - share a single instance across identical meshes"),
        # CapsuleGeometry on r128 = guaranteed crash
        (r"new\s+THREE\.CapsuleGeometry",
         "THREE.CapsuleGeometry does not exist in r128 (added in r142) - build with CylinderGeometry + SphereGeometry"),
        # No dispose on teardown
        (r"scene\.remove\s*\([^)]+\)(?![^}]{0,200}\.dispose\s*\(\))",
         "scene.remove() without dispose() - geometry/material/textures stay in VRAM indefinitely"),
        # Segment count too high on background elements
        (r"new\s+THREE\.SphereGeometry\s*\([^,]+,\s*(?:128|256|512)\s*,",
         "SphereGeometry with 128+ segments - excessive budget. Hero: 32-64, Background: 8-16"),
        # Shadows on everything = double GPU pass
        (r"for\s*\([^)]+\)[^}]{0,200}\.castShadow\s*=\s*true",
         "castShadow enabled in a loop on every object - shadow map pass per mesh, very expensive"),
        # Unversioned CDN = silent breakage
        (r"unpkg\.com/three@latest|cdnjs\.cloudflare\.com.*three.*latest",
         "Unversioned Three.js CDN - silently breaks when unpkg/cdnjs updates. Pin to r128"),
        # No initial lookAt = potentially empty scene
        (r"new\s+THREE\.PerspectiveCamera[^}]{0,500}renderer\.render",
         # Light heuristic - check for presence of lookAt
         "PerspectiveCamera with no apparent camera.lookAt() - scene may be invisible"),
    ]

    # Vague buzzwords
    BUZZWORDS = {
        "premium": "Replace with a precise description (e.g. 'High contrast, generous spacings')",
        "moderne": "Replace with a precise description (e.g. 'Minimalist', 'Geometric')",
        "elegant": "Replace with a precise description (e.g. 'Generous spacings', 'Hierarchical typography')",
        "magnifique": "Replace with a precise description",
        "incroyable": "Replace with a precise description",
        "unique": "Replace with a precise description",
        "innovant": "Replace with a precise description",
        "futuriste": "Use only if justified by concrete visual choices",
    }

    # Generic template sections
    TEMPLATE_SECTIONS = {
        "hero": "Hero section",
        "features": "Feature grid",
        "testimonials": "Testimonials section",
        "cta": "Call to action",
        "pricing": "Pricing",
        "faq": "FAQ",
        "footer": "Footer",
    }

    # Generic fonts
    GENERIC_FONTS = {
        "helvetica", "arial", "times new roman", "georgia", "verdana",
        "courier", "comic sans", "impact", "trebuchet", "palatino",
    }

    def __init__(self, design_file: str = None, code_dir: str = None):
        self.design_file = Path(design_file) if design_file else None
        self.code_dir = Path(code_dir) if code_dir else None
        self.issues: List[Dict] = []
        self.score = 100  # Quality score (0-100)

        # .slop-ignore whitelist - loaded from the project root
        self._whitelist = self._load_slop_ignore()

    # -- .slop-ignore -----------------------------------------------------------

    def _load_slop_ignore(self) -> Dict[str, List[str]]:
        """Load the .slop-ignore file from the project root."""
        whitelist: Dict[str, List[str]] = {
            "icons": [], "buzzwords": [], "gradients": [], "badges": [], "files": []
        }
        # Look in the current directory and immediate parents
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
            # Section header: [icons]
            section_match = re.match(r"^\[(\w+)\]$", line)
            if section_match:
                current_section = section_match.group(1).lower()
                continue
            # Entry: "search  # justification"
            if current_section and current_section in whitelist:
                token = line.split("#")[0].strip()  # strip inline comment
                justification = line.split("#")[1].strip() if "#" in line else ""
                # Rule: entries without justification are ignored (safety)
                if token and justification:
                    whitelist[current_section].append(token.lower())

        if any(whitelist.values()):
            loaded = sum(len(v) for v in whitelist.values())
            print(f"  [INFO] .slop-ignore loaded - {loaded} exemption(s)")

        return whitelist

    def _add_issue(self, issue_type: str, message: str, suggestion: str = "", severity: int = 1):
        """Unified helper to record an issue and deduct from the score."""
        self.issues.append({
            "type": issue_type.lower(),
            "severity": "warning" if severity == 1 else "error",
            "message": message,
            "suggestion": suggestion,
        })
        self.score -= 5 * severity

    def _is_whitelisted(self, section: str, token: str) -> bool:
        """Return True if the token is exempt in the given section."""
        return token.lower() in self._whitelist.get(section, [])

    def _file_is_ignored(self, path) -> bool:
        """Return True if the file is in the ignore list."""
        path_str = str(path).replace("\\", "/")
        for pattern in self._whitelist.get("files", []):
            if pattern.rstrip("/") in path_str:
                return True
        return False


    def _detect_mobile_slop(self, content: str, file_path: Path = None):
        """Detect native mobile antipatterns in code."""
        ctx = str(file_path.name) if file_path else "code"

        # Detect whether this is native mobile code
        is_swift    = file_path and file_path.suffix in {".swift"}
        is_kotlin   = file_path and file_path.suffix in {".kt", ".kts"}
        is_dart     = file_path and file_path.suffix in {".dart"}
        is_rn       = file_path and file_path.suffix in {".tsx", ".jsx"} and (
                        "react-native" in content.lower() or
                        "StyleSheet.create" in content or
                        "from 'react-native'" in content
                    )

        if not (is_swift or is_kotlin or is_dart or is_rn):
            return  # Not native mobile code - skip

        import re as _re

        for pattern, description in self.MOBILE_SLOP_PATTERNS:
            if _re.search(pattern, content):
                self._add_issue(
                    "MOBILE_SLOP",
                    f"{description} [{ctx}]",
                    "Use the platform's native components and APIs",
                    severity=2
                )

        # Adaptive dark mode check
        if is_swift and "Color.white" in content and "colorScheme" not in content:
            self._add_issue(
                "MOBILE_SLOP",
                f"Fixed white color with no dark mode adaptation [{ctx}]",
                "Use Color(.systemBackground) or @Environment(.colorScheme)",
                severity=1
            )

        if is_kotlin and "Color.White" in content and "isSystemInDarkTheme" not in content:
            self._add_issue(
                "MOBILE_SLOP",
                f"Fixed Color.White with no adaptive dark mode [{ctx}]",
                "Use MaterialTheme.colorScheme.background",
                severity=1
            )

        # Minimal accessibility check
        if is_swift and "Image(" in content:
            has_label = "accessibilityLabel" in content or "Label(" in content
            if not has_label:
                self._add_issue(
                    "MOBILE_SLOP",
                    f"SwiftUI Image without accessibilityLabel [{ctx}]",
                    "Add .accessibilityLabel(String) to every Image",
                    severity=1
                )

        if is_kotlin and "Image(" in content and "contentDescription" not in content:
            self._add_issue(
                "MOBILE_SLOP",
                f"Compose Image without contentDescription [{ctx}]",
                "Add contentDescription = String or null if decorative",
                severity=1
            )


    def _detect_threejs_slop(self, content: str, file_path: Path = None):
        """Detect Three.js antipatterns in JS/TS/JSX/TSX code."""
        import re as _re
        ctx = file_path.name if file_path else "code"

        # Check if Three.js is used in this file
        is_three = any(k in content for k in [
            "THREE.", "from 'three'", 'from "three"',
            "WebGLRenderer", "PerspectiveCamera", "BufferGeometry"
        ])
        if not is_three:
            return

        for pattern, description in self.THREEJS_SLOP_PATTERNS:
            # Exclude the noisy lookAt pattern
            if "PerspectiveCamera with no apparent camera.lookAt" in description:
                has_camera = "PerspectiveCamera" in content
                has_lookat = "lookAt" in content
                if has_camera and not has_lookat:
                    self._add_issue(
                        "THREEJS_SLOP",
                        f"{description} [{ctx}]",
                        "Add camera.lookAt(scene.position) or camera.lookAt(target) before the first render",
                        severity=1
                    )
                continue

            if _re.search(pattern, content, _re.DOTALL):
                self._add_issue(
                    "THREEJS_SLOP",
                    f"{description} [{ctx}]",
                    "See references/threejs-best-practices.md",
                    severity=2
                )

    def run(self) -> bool:
        """Run the full detection"""
        if self.design_file:
            self._check_design_file()

        if self.code_dir:
            self._check_code_directory()

        self._print_report()
        return self.score >= 80  # Passes if score >= 80

    def _check_design_file(self):
        """Check the DESIGN.md file"""
        if not self.design_file.exists():
            print(f"[ERROR] File not found: {self.design_file}")
            return

        content = self.design_file.read_text(encoding="utf-8")

        # Detect default shadcn/ui usage
        self._detect_shadcn_defaults(content)

        # Detect logo placeholders
        self._detect_logo_placeholders(content)

        # Detect buzzwords
        self._detect_buzzwords(content)

        # Detect generic icons
        self._detect_generic_icons(content)

        # Detect cliche gradients
        self._detect_cliche_gradients(content)

        # Detect generic fonts
        self._detect_generic_fonts(content)

        # Detect AI status badges
        self._detect_status_badges(content)

    def _check_code_directory(self):
        """Check code files"""
        if not self.code_dir.exists():
            print(f"[ERROR] Directory not found: {self.code_dir}")
            return

        # Check web (TSX/JSX) and native mobile (Swift/Kotlin/Dart) files
        mobile_web_exts = ["*.tsx", "*.jsx", "*.js", "*.ts", "*.swift", "*.kt", "*.kts", "*.dart"]
        for ext in mobile_web_exts:
            for file_path in self.code_dir.rglob(ext):
                if not self._file_is_ignored(file_path):
                    self._check_code_file(file_path)

        # Detect default shadcn/ui usage in the code
        for file_path in self.code_dir.rglob("*.tsx"):
            self._detect_shadcn_defaults(file_path.read_text(encoding="utf-8", errors="ignore"), file_path)
        for file_path in self.code_dir.rglob("*.jsx"):
            self._detect_shadcn_defaults(file_path.read_text(encoding="utf-8", errors="ignore"), file_path)

        # Detect AI status badges in the code
        for file_path in self.code_dir.rglob("*.tsx"):
            self._detect_status_badges(file_path.read_text(encoding="utf-8", errors="ignore"), file_path)
        for file_path in self.code_dir.rglob("*.jsx"):
            self._detect_status_badges(file_path.read_text(encoding="utf-8", errors="ignore"), file_path)

    def _check_code_file(self, file_path: Path):
        """Check a single code file"""
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        # Detect Lucide imports
        lucide_imports = re.findall(r"from\s+['\"]lucide-react['\"].*?import\s+{([^}]+)}", content)
        if lucide_imports:
            icons = [i.strip() for i in lucide_imports[0].split(",")]
            generic = [i for i in icons if i.lower() in self.GENERIC_ICONS]

            if generic:
                self.issues.append({
                    "type": "generic_icons",
                    "file": str(file_path),
                    "severity": "warning",
                    "message": f"Generic Lucide icons: {', '.join(generic)}",
                    "suggestion": "Use custom SVG or a coherent icon pack"
                })
                self.score -= 5 * len(generic)

        # Detect template sections
        template_count = sum(1 for section in self.TEMPLATE_SECTIONS if section in content.lower())
        if template_count >= 4:
            self.issues.append({
                "type": "template_structure",
                "file": str(file_path),
                "severity": "warning",
                "message": f"Generic template structure ({template_count} sections)",
                "suggestion": "Consider a more distinctive approach"
            })
            self.score -= 10

        # Detect native mobile antipatterns
        self._detect_mobile_slop(content, file_path)

        # Detect Three.js antipatterns
        self._detect_threejs_slop(content, file_path)


    def _detect_status_badges(self, content: str, file_path: Path = None):
        """Detect AI status badges that were never requested (ATMOSPHERE EXCELLENT, LIVE NOW, etc.)"""
        for pattern, message in self.STATUS_BADGE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                issue = {
                    "type": "status_badge",
                    "severity": "warning",
                    "message": f"AI status badge: {message}",
                    "suggestion": (
                        "Remove this badge - never requested, immediate AI signal. "
                        "If a status is functionally required, justify it in DESIGN.md."
                    )
                }
                if file_path:
                    issue["file"] = str(file_path)
                self.issues.append(issue)
                self.score -= 8

    def _detect_buzzwords(self, content: str):
        """Detect vague buzzwords"""
        for buzzword, suggestion in self.BUZZWORDS.items():
            if self._is_whitelisted("buzzwords", buzzword):
                continue
            if re.search(rf"\b{buzzword}\b", content, re.IGNORECASE):
                self.issues.append({
                    "type": "buzzword",
                    "severity": "warning",
                    "message": f"Vague buzzword: '{buzzword}'",
                    "suggestion": suggestion
                })
                self.score -= 3

    def _detect_generic_icons(self, content: str):
        """Detect generic icons"""
        for icon in self.GENERIC_ICONS:
            if self._is_whitelisted("icons", icon):
                continue
            if re.search(rf"\b{icon}\b", content, re.IGNORECASE):
                self.issues.append({
                    "type": "generic_icon",
                    "severity": "info",
                    "message": f"Generic icon: {icon}",
                    "suggestion": "Consider custom SVG if used in a non-standard way"
                })
                self.score -= 1

    def _detect_undocumented_gradients(self, content: str):
        """Detect gradients present in the code but not documented in §1 of DESIGN.md."""
        # Look for background-image with gradient or radial-gradient
        grad_patterns = [
            r"radial-gradient\s*\(",
            r"linear-gradient\s*\(",
            r"conic-gradient\s*\(",
            r"bg-gradient-",  # Tailwind
        ]
        design_mentions = []
        if self.design_file:
            try:
                design_content = self.design_file.read_text(encoding="utf-8", errors="ignore").lower()
                design_mentions = re.findall(r"gradient|dégradé|degrade|mesh|radial", design_content)
            except Exception:
                pass

        for pat in grad_patterns:
            if re.search(pat, content, re.IGNORECASE):
                if not design_mentions:
                    self._add_issue(
                        "UNDOCUMENTED_GRADIENT",
                        f"Gradient detected in code but not documented in §1 of DESIGN.md.",
                        "Document the gradient in §1 'Allowed effects' with a visual justification.",
                        severity=1
                    )
                break  # Single warning even if multiple gradients

    def _detect_cliche_gradients(self, content: str):
        """Detect cliche gradients"""
        for pattern, name in self.CLICHE_GRADIENTS:
            if re.search(pattern, content, re.IGNORECASE):
                self.issues.append({
                    "type": "cliche_gradient",
                    "severity": "warning",
                    "message": f"Cliche gradient: {name}",
                    "suggestion": "Justify by semantic role or consider an alternative"
                })
                self.score -= 5

    def _detect_generic_fonts(self, content: str):
        """Detect generic fonts"""
        for font in self.GENERIC_FONTS:
            if re.search(rf"\b{font}\b", content, re.IGNORECASE):
                self.issues.append({
                    "type": "generic_font",
                    "severity": "error",
                    "message": f"Generic font: {font}",
                    "suggestion": "Use Google Fonts or a custom font"
                })
                self.score -= 10

    def _detect_logo_placeholders(self, content: str, file_path: Path = None):
        """Detect logo placeholders or generic names"""
        for pattern, message in self.LOGO_PLACEHOLDERS:
            if re.search(pattern, content, re.IGNORECASE):
                issue = {
                    "type": "logo_placeholder",
                    "severity": "error",
                    "message": f"Generic logo/name detected: {message}",
                    "suggestion": "Use a stylized text logo (font-bold tracking-tight uppercase) if no logo is provided."
                }
                if file_path:
                    issue["file"] = str(file_path)
                self.issues.append(issue)
                self.score -= 10

    def _detect_shadcn_defaults(self, content: str, file_path: Path = None):
        """Detect default shadcn/ui usage"""
        for pattern, message in self.SHADCN_DEFAULT_PATTERNS:
            if re.search(pattern, content):
                issue = {
                    "type": "shadcn_default",
                    "severity": "warning",
                    "message": f"Default shadcn/ui: {message}",
                    "suggestion": "Customize shadcn/ui components via Tailwind CSS and design tokens."
                }
                if file_path:
                    issue["file"] = str(file_path)
                self.issues.append(issue)
                self.score -= 5

    def _print_report(self):
        """Print the detection report"""
        print("\n" + "=" * 70)
        print("AI SLOP DETECTION REPORT")
        print("=" * 70)

        if not self.issues:
            print("\n[OK] NO ANTIPATTERN DETECTED!")
        else:
            print(f"\n[WARN] {len(self.issues)} issues detected:\n")

            # Group by type
            by_type = {}
            for issue in self.issues:
                issue_type = issue["type"]
                if issue_type not in by_type:
                    by_type[issue_type] = []
                by_type[issue_type].append(issue)

            for issue_type in sorted(by_type.keys()):
                print(f"\n[{issue_type.upper()}]")
                for issue in by_type[issue_type]:
                    severity = issue.get("severity", "info")
                    tag = {"error": "[ERROR]", "warning": "[WARN]", "info": "[INFO]"}.get(severity, "-")

                    print(f"  {tag} {issue['message']}")
                    if "file" in issue:
                        print(f"     File: {issue['file']}")
                    print(f"     -> {issue['suggestion']}")

        # Final score
        print("\n" + "-" * 70)
        print(f"QUALITY SCORE: {self.score}/100")

        if self.score >= 80:
            print("[OK] RESULT: GOOD - Ready for delivery")
        elif self.score >= 60:
            print("[WARN] RESULT: ACCEPTABLE - Fix the warnings")
        else:
            print("[ERROR] RESULT: POOR - Revisit the design")

        print("=" * 70 + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI slop antipattern detector")
    parser.add_argument("--design", help="DESIGN.md file to check")
    parser.add_argument("--code", help="Code directory to audit")

    args = parser.parse_args()

    if not args.design and not args.code:
        print("Usage: python3 detect_ai_slop.py --design DESIGN.md --code ./client/src")
        sys.exit(1)

    detector = AISloPDetector(design_file=args.design, code_dir=args.code)
    success = detector.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
