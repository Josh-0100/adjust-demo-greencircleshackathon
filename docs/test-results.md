# Executed validation — 13 October 2026

These are results observed against the local synthetic demonstration. Commands run on macOS with Python 3.13 in `backend/.venv`, Node 26, npm 11, and Next.js 15.5.27. They do not establish accuracy or suitability for real council decisions.

| Check | Executed result |
| --- | --- |
| Database bootstrap | `./scripts/start.sh` completed Alembic migration and reported 180 labelled fictional resources and 8 seeded cases. |
| Project gate | `./scripts/check.sh` exited 0 with a standard production build. The final integrated `./scripts/check.sh --e2e` also exited 0: backend Pytest 25 passed; TypeScript check passed; Vitest 10 passed; isolated Next.js production build passed for `/`, `/operations`, `/intelligence`, `/impact`, `/admin`, and `/demo`; Playwright passed 6/6. |
| Browser workflows | The final integrated Playwright Chromium run passed 6/6 in 12.8 seconds. It covered resident result → staff resolution → impact, guided demo/reset, configuration/import, custom and learning persistence, API failure/retry, and mobile navigation/theme/keyboard. The prior post-typography direct run also passed 6/6 in 13.0 seconds. |
| Live API | `python3 scripts/health_check.py --url http://127.0.0.1:8765 --wait 20` returned healthy deterministic demo mode under the one-command launcher. |
| Live frontend proxy | `python3 scripts/smoke_test.py --url http://127.0.0.1:3000` exited 0 before and after an immediate launcher restart. It created one case per enabled module with attributed synthetic sources, then tested staff review, feedback, labelled impact, access boundaries, validation, audit, and two repeatable resets. |
| Narrow fixture benchmark | `.venv/bin/python -m app.evaluation.benchmark` passed 12/12 labelled fictional category/source/grounding checks. These constructed fixtures are not a real-world quality measure. |
| Static script checks | `bash -n scripts/start.sh scripts/setup.sh scripts/check.sh` and Python compilation of the health/reset/smoke scripts exited 0. |

The final integrated command from the repository root was:

```sh
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Users/ankit/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing' ./scripts/check.sh --e2e
```

The previous direct Playwright command from `frontend/` was:

```sh
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Users/ankit/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing' npm run test:e2e
```

On a new machine, install Playwright Chromium with `npx playwright install chromium` and run `npm run test:e2e` while both local services are running. The Pytest run emitted one Starlette/AnyIO deprecation warning from an installed dependency; it did not fail tests. Several earlier browser iterations failed before their test or UI defects were fixed; one repeated run exceeded the configured 120-request-per-minute same-client limit. The final clean run passed after the limiter window cleared. The sequence and fixes are recorded in `../PROJECT_LOG.md` and `build-frontend.md`.

The default local AI provider is deterministic and visibly marked simulated. Unit tests exercise a provider outage and reject ungrounded optional-provider output, while the smoke and browser runs exercise the no-paid-API path. The browser suite checks a 390px viewport for horizontal overflow; manual inspection also checked 375px. Neither check is a complete accessibility audit.

Docker is unavailable in this workspace, so image build, Compose runtime, and PostgreSQL behavior are unverified. The supplied demo-role headers are not real authentication. Only fictional data was used. See `responsible-ai.md` and `deployment.md` for remaining pilot work. The event's prebuilt/AI-generated-code policy remains unconfirmed; see `hackathon-rules.md`.

## Bolton Connect + Adjust AI integration — 16 October 2026

Final executed gate: `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' ./scripts/check.sh --e2e` exited0. Host backend38 (including13 new integration cases), Bolton15, Adjust99; host frontend10 and Adjust61; both TypeScript checks and isolated production builds passed. Host Playwright10/10 passed in34.0s, preserving all6 original workflows and adding4 integration journeys. Adjust standalone Playwright8/8 also passed after its frontend integration edits. Existing dependency deprecation/terminal-colour warnings remain.

Actual standalone Bolton full resident-to-adviser browser journey used its own temporary database/server8109: consent, plan, resume, review note/status, staff403, and390px completed-plan/adviser layouts passed. All21 requests stayed on8109; temporary server/database cleaned up. Mobile includes a maximum-length unbroken fictional name after scoped wrapping repair.

First combined browser run9/10 exposed an intermittent embedded invitation race. Delayed iframe mounting plus repeat-link remounting fixed it; the final full gate passed and includes clearing/reopening the same reviewed link. Original live proxy smoke passed all6 modules, staff review/feedback/impact/access/audit and two resets.

Launcher startup/reuse, explicit rejection of requested non-demo reuse of a running demo, Bash/Python syntax, Compose YAML/dependencies and whitespace checks passed. Docker runtime, native Windows, PostgreSQL and production sign-in remain unverified. See [the integration report](integration-report.md) for changed files, exact journeys, deployment instructions, data/auth boundaries and limitations. PPT has not been opened or used.

## Authorised logo and PPT palette — 16 October 2026

After explicit user permission, applied the unchanged supplied logo and exact PPT palette across host, both module interfaces and printable plans. Final full `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' ./scripts/check.sh --e2e` exited0: backend38+15+99, frontend10+61, both TypeScript checks/production builds, host browser10/10 in41.1s. Standalone Adjust8/8 passed with installed Chrome (including one-page PDF), and complete standalone Bolton resident/adviser/mobile/print-logo journey passed with24 requests confined to its own temporary origin. Temporary test data/server cleaned up.

Focused19-state visual audit passed at1440/390/340px including dark mode, drawer and module logo paths, with no horizontal overflow/browser errors and tested text contrast above4.5:1. All3 logo copies match source SHA256 and serveHTTP200; all10 exact slide colours present across the3 stylesheets. Existing warnings remain. Docker/runtime limitation unchanged. See [branding.md](branding.md) for sources, palette and screenshots.

## Reference landing and fluid resident/adviser redesign — 16 October 2026

Final full `PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' ./scripts/check.sh --e2e` exited0: host38/resident15/workplace99 backend tests; host10/workplace64 frontend tests; both TypeScript checks/builds;11 host browser tests passed in38.1s (all6 original workflows,4 retained integration journeys,1 new reference-landing journey covering both roles). The latter preserves entered text, checks first/repeated/postassessment advisor anchors, natural iframe height, private text absent from URLs and unchecked confirmation/review gates. Standalone workplace8/8 and full independent resident/adviser/print journey passed too. Final display-only alias-error cleanup was followed by2 safety tests passing.

Focused visual checks passed21 states plus9 internal document-navigation states, widths340/390/1440; standalone resident responsive checks additionally cover768/1024/1920. No old visible product branding, page errors, horizontal overflow or inner clipping; iframe/body heightgap0. Advisor jumps and case-detail expansion passed. Earlier real cached iframe readiness/host scrolling bugs and one test DOM type error were fixed before the final gate. Source/data identifiers and API/schema/privacy/consent boundaries remain stable. See [redesign record](ui-redesign.md).
