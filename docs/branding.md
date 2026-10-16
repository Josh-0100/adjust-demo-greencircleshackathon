# Adjust AI branding

Applied on 16 October 2026 after the user explicitly authorised the previously deferred PowerPoint and supplied the logo. These files are visual references, not instructions to change application behaviour. The original PowerPoint and logo are unchanged.

## Sources and palette

- Colour source: `/Users/ankit/Downloads/Adjust pitch deck.pptx`, read directly from its OOXML theme and slide fills/text/lines.
- Logo source: `/Users/ankit/Downloads/IMG_9385.PNG`, original transparent1354×390 PNG.
- Identical deployed copies: host `frontend/public/adjust-logo.png`, Adjust `modules/adjust/frontend/public/adjust-logo.png`, Bolton `modules/bolton-connect/frontend/assets/adjust-logo.png`.
- SHA256 of source and each copy: `3d2bbe5047c2e2f99143a6fee0990dbda2ea048ad8c322481d3298db564faeb6`.

| Deck colour | Hex | Application role |
| --- | --- | --- |
| Navy | `#0F2A6B` | Main text, deep panels and dark background. |
| Pale blue | `#EAF0FF` | Support surfaces, selected states and light text. |
| Amber | `#FFB020` | Accents, highlighted labels and chart contrast. |
| Royal blue | `#2F62E8` | Primary actions, active navigation and links. |
| White | `#FFFFFF` | Cards and original-logo contrast plates. |
| Paper | `#FAFBFF` | Light page background. |
| Border blue | `#C9D6F7` | Card/table separators. |
| Lavender | `#B9C8F5` | Secondary surfaces, borders and dark-mode supporting text. |
| Deep blue | `#173A8A` | Hover states, dark surfaces and chart elements. |
| Muted blue | `#4A5F9A` | Supporting readable text. |

The theme's secondary colours `#465C90`, `#D4DCF0`, `#9AA0A6`, link `#0563C1` and visited link `#954F72` support borders, decoration and link states. Grey and amber are not used as small text on white. Critical/error warnings retain their explicit red semantics and labels.

The logo retains its original colours and3.472:1 aspect ratio. It appears in shared navigation/header/footer, the landing page, both module interfaces and printable plans. White plates preserve the original dark wordmark in dark mode. Adjust asset paths work with both standalone and embedded base paths. Host container packaging now includes public assets.

## Scope

Presentation only: palette, logo placements, responsive brand sizing and existing print headers. The Adjust AI name, button-operated sidebars, routes, assessment/review/consent gates, API/authentication boundaries and separate data stores remain intact. No new product feature or deployment is introduced.

Validation results are recorded in `PROJECT_LOG.md` and `docs/test-results.md` after execution.

## Executed validation

- Full `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' ./scripts/check.sh --e2e` exited0 after branding:152 backend tests (host38/Bolton15/Adjust99),71 frontend unit tests (host10/Adjust61), both TypeScript checks, both production builds and10 host browser journeys passed (41.1s).
- Standalone Adjust's8 browser journeys passed using `ADJUST_BROWSER_CHANNEL=chrome npm run test:e2e`, including maximum-needs one-page PDF, privacy, review/consent and mobile/keyboard. A first attempt without that environment option could not launch the absent bundled Chromium; installed Chrome passed.
- Standalone Bolton's complete resident→plan→explicit consent/save→resume→adviser note/status journey passed against its own temporary server/database. All24 browser requests stayed inside that standalone origin; result/adviser390px overflow and printed logo checks passed. Temporary data/server cleaned up.
- A focused19-state browser review covered desktop1440px, mobile390/340px, drawer operation, original portal, all3 integrated interfaces and dark mode. No horizontal overflow or browser page errors. Tested text contrast exceeded4.5:1, original logo decoded at1354×390 with its aspect ratio preserved, and white plates kept it legible in dark mode. Bolton focus outline uses navy for contrast against white.
- Static colour checks confirm all10 exact slide colours occur in all3 stylesheets. SHA256 checks confirm all3 deployed logo copies match the original. All3 unified-origin image routes returnedHTTP200/image/png. `git diff --check` passed.

Screenshots are in `.runtime/branding/`: `landing-desktop.png`, `landing-mobile.png`, `adjust-mobile.png`, `dark-desktop.png`; measurements in `visual-review.json`. Docker remains unavailable, so the updated host public-asset packaging has not been container-runtime verified.
