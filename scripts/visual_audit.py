#!/usr/bin/env python3
"""
Visual Audit Script - Uses Playwright to check the real rendering of the site.
Checks:
- Loaded fonts (computed styles)
- Real spacings (multiples of 8px)
- Absence of visible "AI slop" elements (stickers, unauthorized emojis)
- Screenshots on 4 breakpoints (mobile/tablet/desktop/wide)

Usage:
    python3 visual_audit.py --url http://localhost:3000 --output ./audit-results
"""

import asyncio
import argparse
import os
import json
from pathlib import Path

# Standard breakpoints — cover mobile, tablet, desktop and wide
BREAKPOINTS = [
    ("mobile",  375,  667),
    ("tablet",  768,  1024),
    ("desktop", 1280, 800),
    ("wide",    1920, 1080),
]

async def run_audit(url, output_dir):
    from playwright.async_api import async_playwright

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {
        "url": url,
        "fonts": [],
        "spacing_errors": [],
        "ai_slop_detected": [],
        "screenshots": {}
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_context(viewport={'width': 1280, 'height': 800}).new_page()

        print(f"[INFO] Navigating to {url}...")
        try:
            await page.goto(url, wait_until="networkidle")
        except Exception as e:
            print(f"[ERROR] Navigation error: {e}")
            await browser.close()
            return

        # 1. Screenshots on 4 breakpoints
        print("[INFO] Capturing screenshots (4 breakpoints)...")
        for name, width, height in BREAKPOINTS:
            await page.set_viewport_size({"width": width, "height": height})
            screenshot_path = str(output_path / f"{name}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            results["screenshots"][name] = screenshot_path
            print(f"   - {name} ({width}x{height}px)")

        # Back to desktop for the DOM audit (stable reference)
        await page.set_viewport_size({"width": 1280, "height": 800})

        # 2. Typography and Spacing audit via JS
        print("[INFO] Analyzing DOM and computed styles...")
        audit_data = await page.evaluate("""
            () => {
                const elements = document.querySelectorAll('h1, h2, h3, p, button, section, div, span, article');
                const fonts = new Set();
                const spacingErrors = [];
                const slopElements = [];

                const isMultipleOf8 = (val) => {
                    const num = parseInt(val);
                    return isNaN(num) || num === 0 || num % 8 === 0 || num === 4;
                };

                elements.forEach(el => {
                    const cs = window.getComputedStyle(el);
                    const text = (el.innerText || "").trim();
                    const tag = el.tagName.toLowerCase();

                    // 1. Loaded fonts
                    fonts.add(cs.fontFamily.split(",")[0].trim().replace(/['"]/g, ""));

                    // 2. Spacing audit
                    ["paddingTop", "paddingBottom", "paddingLeft", "paddingRight", "marginTop", "marginBottom"].forEach(prop => {
                        if (!isMultipleOf8(cs[prop])) {
                            spacingErrors.push(tag + "." + el.className.split(" ")[0] + ": " + prop + "=" + cs[prop]);
                        }
                    });

                    // 3. Made-up system status badge
                    if (/[A-Z][A-Z_]{3,}:\s*[A-Z][A-Z_]+/.test(text) && text.length < 50) {
                        slopElements.push("Status badge: \"" + text + "\" — AI slop");
                    }

                    // 4. ALL_CAPS button
                    if ((tag === "button" || el.closest("button")) && text.length > 3) {
                        const isUpper = cs.textTransform === "uppercase" ||
                                        (text === text.toUpperCase() && /[A-Z]{3}/.test(text));
                        if (isUpper) slopElements.push("ALL_CAPS button: \"" + text.substring(0, 40) + "\"");
                    }

                    // 5. ALL_CAPS labels inside cards
                    if (/^[A-Z][A-Z\'\s]{6,}\s*:/.test(text) && text.length < 60) {
                        if (el.closest("[class*=card],[class*=Card],article")) {
                            slopElements.push("ALL_CAPS label: \"" + text.substring(0, 50) + "\"");
                        }
                    }

                    // 6. Asymmetric grid
                    if (el.matches("[class*=grid],[class*=Grid]")) {
                        const cards = el.querySelectorAll("[class*=card],[class*=Card],article");
                        if (cards.length > 0) {
                            const cols = cs.gridTemplateColumns === "none" ? 1 : cs.gridTemplateColumns.split(" ").length;
                            if (cols >= 3 && cards.length % cols !== 0) {
                                slopElements.push("Asymmetric grid: " + cards.length + " cards / " + cols + " col");
                            }
                        }
                    }

                    // 7. Over-empty section
                    if (tag === "section") {
                        const pTop = parseInt(cs.paddingTop) || 0;
                        const pBot = parseInt(cs.paddingBottom) || 0;
                        if ((pTop + pBot) > 192 && el.children.length <= 2) {
                            slopElements.push("Over-empty section: padding " + (pTop+pBot) + "px, " + el.children.length + " children");
                        }
                    }
                });

                // 8. Too many font families
                const fontList = Array.from(fonts).filter(f => f && f.length > 1);
                if (fontList.length > 3) {
                    slopElements.push("Too many fonts: " + fontList.length + " families (" + fontList.slice(0,4).join(", ") + ")");
                }

                return { fonts: fontList, spacingErrors: spacingErrors.slice(0, 20), slopElements: slopElements };
            }
        """)

        results["fonts"] = audit_data["fonts"]
        results["spacing_errors"] = audit_data["spacingErrors"]
        results["ai_slop_detected"] = audit_data["slopElements"]

        await browser.close()

    # Save the results
    with open(output_path / "audit_report.json", "w") as f:
        json.dump(results, f, indent=2)

    screenshot_count = len(results["screenshots"])
    print(f"\n[OK] Audit complete. Results in {output_dir}")
    print(f"[INFO] Screenshots: {screenshot_count} breakpoints ({', '.join(results['screenshots'].keys())})")
    print(f"[INFO] Fonts detected: {len(results['fonts'])}")
    print(f"[WARN] Spacing errors: {len(results['spacing_errors'])}")
    print(f"[WARN] Slop elements: {len(results['ai_slop_detected'])}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:3000")
    parser.add_argument("--output", default="./audit-results")
    args = parser.parse_args()

    asyncio.run(run_audit(args.url, args.output))
