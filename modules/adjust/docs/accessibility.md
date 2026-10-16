# Accessibility review — 16 October 2026

Reviewed against the accessibility-review skill's WCAG 2.1 AA checklist. This is a limited engineering review, not a conformance certification. No automated axe scan, VoiceOver or NVDA test was run.

## Checks performed

- Semantic landmarks, a single visible main heading, native labelled inputs, required/optional indicators and descriptive hints.
- Skip-to-content link verified with keyboard Tab/Enter in Chromium. Screen transitions put focus on the page heading; disabled steps remain unavailable until their prerequisites exist.
- Native checkbox/label pairs and details/summary source disclosures. Actions and disclosure rows have at least 44 CSS pixels of vertical target area. Focus uses a visible 3-pixel outline; text is not the only selection indicator.
- Submission and service errors have alert semantics. Busy states, evidence counts and selection counts use status semantics. Emergency guidance has an explicit accessible alert name.
- Decorative artwork and redundant icons are hidden from assistive technology. Official source links identify new-tab behaviour.
- Actual 390 × 844 browser test: form labels and entered text visible, no horizontal overflow, no content in localStorage/sessionStorage, reload clears the description. Desktop and mobile screenshots visually inspected.
- Responsive grids collapse to one column. Mobile resource buttons were added so the source library and support routes remain directly accessible when the sidebar journey is hidden.
- Reduced-motion media query removes animation/transitions. No auto-playing media, time limits, keyboard traps or drag-only controls.

## Colour contrast

Computed using WCAG sRGB relative luminance, with the final source CSS colours:

| Element | Foreground | Background | Ratio | Normal-text threshold |
|---|---|---|---|---|
| Body text | `#3f534b` | `#f8f9f5` | 7.79:1 | Pass |
| Secondary text | `#63716a` | `#ffffff` | 5.12:1 | Pass |
| Primary button | `#ffffff` | `#244e3c` | 9.42:1 | Pass |
| Hero green title | `#58723b` | `#eff3e8` | 4.80:1 | Pass |
| Form placeholder | `#63715c` | `#ffffff` | 5.19:1 | Pass |
| Guidance notice | `#526348` | `#f0f3eb` | 5.78:1 | Pass |
| Option pill | `#3e5c31` | `#f0f4e9` | 6.77:1 | Pass |

The placeholder colour was darkened during review. Disabled controls and decorative illustration text are excluded from these normal-text checks. This sample does not constitute an exhaustive automated contrast scan.

## Remaining validation

Test full keyboard-only completion with people using assistive technology, VoiceOver/NVDA announcements, 200% text zoom and 400% browser zoom, Windows high-contrast mode, Safari/Firefox, accessible PDF reading order and real employer usability. Browser-generated PDFs may need additional tagging work before they can be claimed accessible documents. No WCAG compliance claim is made.
