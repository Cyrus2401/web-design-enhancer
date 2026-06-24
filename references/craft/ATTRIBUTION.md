# Vendored craft references — provenance & integration

Brand-agnostic craft knowledge vendored from
[**nexu-io/open-design**](https://github.com/nexu-io/open-design) (Apache-2.0),
pinned at commit `009ff65`.

## Why these — and explicitly NOT the design-systems
web-design-enhancer-pro already sources **brand** references **live** via
`getdesign` (Pillar 1), with `scripts/sync_references.py` guarding drift.
Open Design's per-brand `design-systems/` would **duplicate getdesign** and go
stale, so they are **deliberately excluded**.

What is vendored here is the *brand-agnostic* craft layer — typography, color,
motion, UX laws, accessibility, RTL/bidi, form & state coverage — which enriches
the agent's reference set (Pillar 2 / UI-UX intelligence) **without overlapping
getdesign's territory**.

## Files
| File | What it covers |
|---|---|
| `anti-ai-slop.md` | The 7 cardinal AI-slop sins — **source of truth** for `detect_ai_slop.py` |
| `typography-hierarchy.md` / `typography-hierarchy-editorial.md` / `typography.md` | Type scale & hierarchy discipline |
| `color.md` | Color system construction beyond default palettes |
| `animation-discipline.md` | Motion that is intentional, not decorative |
| `laws-of-ux.md` | Hick, Fitts, Von Restorff, Jakob, etc. |
| `state-coverage.md` | Empty / loading / error / success states |
| `form-validation.md` | Real-world form & validation UX |
| `accessibility-baseline.md` | WCAG-grade a11y baseline |
| `rtl-and-bidi.md` | Right-to-left & bidirectional layout |
| `README.md` / `FUTURE_SECTIONS.md` | Upstream index (Open Design's own opt-in mechanism — informational only here) |

## License & attribution
- Apache-2.0 — full text: `../../LICENSES/open-design-APACHE-2.0.txt`; attribution: root `NOTICE`.
- Upstream content is itself adapted from `refero_skill` (MIT).
- Files are vendored **verbatim** (no edits), so the upstream notices are preserved.

## Code linkage (source of truth)
`anti-ai-slop.md` defines the default-AI **Tailwind indigo** palette. That list is
mirrored in `scripts/detect_ai_slop.py` as `CANON_DEFAULT_INDIGO` and enforced by
`tests/test_anti_slop_canon_sync.py` — if Open Design updates the canon and these
files are re-synced, the test forces the constant to be updated too.

## Re-syncing (manual, pinned)
```powershell
$base = "https://raw.githubusercontent.com/nexu-io/open-design/<commit>/craft"
Get-Content references/craft/_manifest.txt | ForEach-Object {
  Invoke-WebRequest -UseBasicParsing -Uri "$base/$_" -OutFile "references/craft/$_"
}
# then run:  py -m pytest tests/test_anti_slop_canon_sync.py -q
```
