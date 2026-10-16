# Frontend build continuation log

Owner: frontend agent. Last update: 13 October 2026.

## Current milestone (frontend implemented)

- Created Next.js / TypeScript application, API contract types, same-origin backend proxy, request error handling, workspace context, accessible reusable components and responsive app shell.
- Dependencies installed successfully, lockfile committed to source tree. Initial sandbox install had network timeout; approved dependency install succeeded using `/private/tmp/civicforge-npm-cache`.
- Six substantive routes complete: `/`, `/operations`, `/intelligence`, `/impact`, `/admin`, `/demo`.
- Resident enquiry → citations / simulated provenance → human staff note / resolve → live impact pipeline implemented; custom home resilience input/result plugin and persistent learning progress integrated with dedicated APIs.
- Admin saves complete configuration, activates modules, imports reviewed evidence, and reads safe audit summaries.
- Final Next.js production validation build passed on Next.js 15.5.27. TypeScript check passed. Vitest: **10 tests passed** in the final clean run.
- Final Playwright suite: **6/6 passed in 13.0 seconds**, after the reading-size improvements. Includes real resident/staff/impact, guided demo/reset, persisted configuration/import, custom assessment and persisted learning, backend failure/retry, and mobile/theme/keyboard workflows. Earlier repeated runs hit the default 120 requests/minute limiter; the final run used normal limits after its window cleared.

## Last changes and continuation

- Demo module now follows the first enabled configured module, ensuring the scenario matches default service navigator sources.
- Retrieval confidence wording changed to **evidence match signal** (uncalibrated) following live backend review.
- All API fetching preserves failure messages, has bounded timeouts and avoids stale filter responses.
- Optional `PLAYWRIGHT_CHROMIUM_EXECUTABLE` lets the test runner reuse the locally installed browser; `PLAYWRIGHT_BASE_URL` configures server URL. `PLAYWRIGHT_START_SERVER=1` starts Next.js automatically when binding is permitted.
- Live backend and local launcher use `http://127.0.0.1:8765` because port 8000 is occupied on this machine. Docker backend remains port 8000 internally, mapped to host 8765.

## Commands

From `frontend/`: `npm install`, `npm run dev`, `npm run typecheck`, `npm test`, `npm run build`, `npm run test:e2e`.

Next.js proxies `/api/*` to `BACKEND_URL` (local default `http://127.0.0.1:8765`; Docker internal backend port 8000). Headers identify synthetic demo roles only. They are not production authentication.

## Implementation decisions

- Semantic, shadcn-style `Button` built with actual Radix Slot and class-variance-authority; no disconnected UI templates.
- Self-hosted system font stack to keep startup independent of font downloads.
- Safe text rendering and http(s)-only links for source citations.
- All impact values read from backend, with measurement kind visible.

## Integration defects discovered and corrected

- Operations omitted empty optional query filters after FastAPI correctly rejected `status=` as invalid.
- Learning checkboxes now update immediately, persist their state via the dedicated API and revert on save failure. E2E performs a fresh GET to verify persisted progress.
- Staff test accounts for cases already escalated to `in_review` by safety rules.
- API error test scopes to the application alert (Next.js route announcer also has an alert role), preserves input and retries successfully.
- A failed module fetch is presented as unavailable services, never as zero configured modules.

## Final frontend verification (13 October 2026)

- `npm run typecheck`: passed.
- `npm test`: 2 files, 10 tests passed.
- `NEXT_BUILD_DIR=.next-validation npm run build`: passed; all six routes statically generated, standalone output enabled. Optional build directory isolates validation from the active development server; default `npm run build` still writes `.next/`.
- Post-typography Playwright command (existing local frontend3000 / backend8765):

```sh
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Users/ankit/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing' npm run test:e2e
```

- Exact result: **6 passed (13.0s)**. Override reused the installed local Chromium; portable setup uses `npx playwright install chromium` and `npm run test:e2e`.
- Primary guidance, input text, recommendations, evidence excerpts and demo copy are 13–14px; secondary reading text is 12px, including mobile. Mobile impact cards use a single column. Decorative tiny labels remain intentionally compact.
- Root owns final gate, launcher verification, Git commits and the parent `PROJECT_LOG.md`. No remaining frontend blocker.
