# Mobile Design References

Manual references for mobile UX inspiration. These sources sit behind paywalls or require manual interaction, so they are not auto-ingested by the validator — consult them directly.

For extractable, open mobile patterns ingested into `data/` and queryable through `scripts/search.py`, see:

| CSV | Patterns | Source |
|---|---|---|
| [`data/apple-hig-patterns.csv`](../data/apple-hig-patterns.csv) | 50 iOS / iPadOS / macOS component anatomies | Apple Human Interface Guidelines |
| [`data/material-design-3-patterns.csv`](../data/material-design-3-patterns.csv) | 49 Android / cross-platform component anatomies | Material Design 3 |
| [`data/pttrns-patterns.csv`](../data/pttrns-patterns.csv) | 50 mobile UX pattern categories with anatomy | Pttrns |

Query examples:

```bash
# Component-level lookup (auto-detect domain)
python3 scripts/search.py "tab bar"
python3 scripts/search.py "floating action button"
python3 scripts/search.py "onboarding flow"

# Force a specific source
python3 scripts/search.py "navigation" --domain apple-hig
python3 scripts/search.py "card" --domain material-design-3
python3 scripts/search.py "empty state" --domain pttrns
```

---

## Walled Manual References

| Source | Link | Recommended Use |
| :--- | :--- | :--- |
| **Mobbin** | [mobbin.com](https://mobbin.com) | End-to-end flow analysis and component-level search with advanced filters |
| **Page Flows** | [pageflows.com](https://pageflows.com) | Recorded user journeys for animation and transition reference |
| **Screenlane** | [screenlane.com](https://screenlane.com) | Quick inspiration by screen type and current visual trends |

---

## What to look for there

- **Micro-interactions**: animation details on screen transitions
- **End-to-end journeys**: how users move from onboarding to final conversion
- **Sectoral variations**: pattern differences between FinTech, e-commerce, social
- **Empty and error states**: creative handling of friction moments

---

## Cross-references

- Anchor mobile structural decisions in §9 of `templates/design-md-template.md` (Mobile Native).
- `scripts/validate_design.py` enforces §9 anatomy + rejects unfilled placeholders.
- Phase 2a (Structural Decision Lock) in `SKILL.md` requires you to quote the mobile native primary screen pattern, navigation type, and primary CTA position from §9 — before writing a single line of code.
