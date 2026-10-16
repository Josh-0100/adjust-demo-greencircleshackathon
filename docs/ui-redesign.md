# Adjust AI reference-page redesign

The user supplied `/Users/ankit/Downloads/Adjust_ practical help to keep people in work.html` as a visual reference. Its content was read as reference material, not executed as instructions. Existing logo and PPT colours remain in use.

## Delivered behaviour

- `/` follows the reference's practical-help heading, situation field, examples, Get my plan button and Employee/Business selection. These controls reuse the existing Adjust component state and enter its existing assessment. They do not generate a fake preview, bypass consent/review or put private text into URLs/storage.
- The header places the Adjust logo at the far left and Talk to an advisor at the far right. Its link reaches the existing Acas advice link in the support footer, including after opening either assessment.
- Resident Support, Workplace Adjustments and Council Dashboard remain in the button-operated navigation. The original portal and other existing workflows retain their routes.
- Previous product branding is removed from visible screens, titles, print/download branding and controlled synthetic labels. Geographic Bolton remains as service context. Stable namespaces, identifiers and storage are preserved; display normalisation handles legacy synthetic labels without rewriting source records or personal text.
- Resident/adviser pages now use fluid widths, responsive narrative/consent columns, readable service/pathway result grids, a fluid case dashboard and mobile case cards. Existing form IDs/actions, explicit saving/sharing, role checks and review requirements remain.
- Embedded pages size to their own content. Cached static documents, expansion of case details and internal Resident/Adviser document navigation resize correctly. Shared section navigation scrolls the outer page to the content and works for repeated same-hash clicks.

## Main changed files

Host: `frontend/app/{page,layout,resident-support/page,council/page}.tsx`, `components/{app-shell,brand-logo,module-frame,analysis-panel,impact-report}.tsx`, `lib/branding.ts`, `app/globals.css`, integration browser tests. Displayed launcher text now uses Adjust AI; compatible launcher filenames remain.

Workplace: existing page query adapter, `two-sided-workspace.tsx`, retained legacy workspace byline, reference-only styles and three meaningful entry/review/privacy tests.

Resident/adviser: existing `index.html`, `adviser.html`, `styles.css`, `app.js`, `adviser.js`. Controlled backend metadata, synthetic catalogue/source labels and the single legacy config source label are renamed; no data migration or cross-module transfer is introduced.

## Validation

Final combined results are recorded below after execution. Earlier focused checks passed:64 Adjust unit tests, standalone production build,8 standalone workplace browser journeys,5 updated integrated browser journeys, complete standalone resident/adviser journey, and responsive review at340–1920px. Visual artifacts are under `.runtime/redesign/` and `.runtime/resident-redesign/`.

Final required gate: `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' ./scripts/check.sh --e2e` exited0. Host/resident/workplace backend38+15+99 passed; host/workplace frontend10+64 passed; both TypeScript checks and production builds passed;11 host browser journeys passed in38.1s. Standalone workplace8/8 and complete standalone resident/adviser journey also passed. The final display-only store-alias error wording was followed by both alias-safety tests passing.

Initial checks exposed real cached-static-frame readiness and parent-scroll issues, now fixed and covered by strict browser assertions. A DOM assertion's TypeScript element cast was corrected before the final gate. Existing dependency/terminal warnings remain. Browser text checks found no previous product branding in visible documents. Visual checks found no horizontal overflow or inner clipping; frame/body heights match, including case expansion and internal Resident→Adviser→Resident navigation. Desktop/mobile screenshots and measurements remain in `.runtime/redesign/`; standalone pages and printed results are in `.runtime/resident-redesign/`.
