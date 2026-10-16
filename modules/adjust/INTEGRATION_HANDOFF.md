# ADJUST integration handoff — 16 October 2026

## Scope and current state

Implemented **ADJUST — Bolton Workplace Adjustments Assistant** as an independent companion to CIVICFORGE AI. This document describes this chat's changes so they can be combined with a second implementation.

Repository: `/Users/ankit/Documents/Hackathon 16 oct/civicforge-ai`

**All implementation owned by this work is inside `modules/adjust/`.** No other AI/subagent/chat was contacted. No external model call was used. The implementation is published as commit `a987adddeb8f7131e23cb1e174b3f3547e79a4cc` on `main` in `Josh-0100/adjust-demo-greencircleshackathon`. That commit contains the 49 module files and an additive destination README update, preserving its original static demo. Publication used a separate checkout; the original CIVICFORGE workspace's Git state remains unchanged. Its original observed HEAD was `eb3cc95`.

ADJUST currently has its own UI on **3001**, API on **8766**, launchers, test runner and source catalogue. It has not been registered in the host module registry or embedded in the host layout. Shared-host integration remains a separate change.

## Work completed

1. Audited the existing Next.js/React/TypeScript frontend, FastAPI/Pydantic backend, authentication, database, AI provider, module registry, styling, APIs, launchers and tests.
2. Preserved the host application and existing dirty working tree. Captured original tracked-file hashes before building.
3. Built seven employer screens: landing, workplace situation, clarification, suggested adjustments, employee conversation, external support and a printable adjustment plan. Added a searchable guidance library and responsive mobile access.
4. Built an independent backend pipeline: safety check → local structured extraction → clarification → knowledge retrieval → authored recommendation templates → source validation → discussion plan.
5. Added a 32-passage catalogue covering 17 exact Acas, HSE, GOV.UK and NHS pages. Each entry has publisher, URL, source section, review/expiry dates, scenario tags, status and an editorial-owner role.
6. Added source-linked options with implementation steps, employee questions, limitations and professional referral prompts. Missing evidence produces no invented task-specific recommendation.
7. Added Acas, occupational health, Access to Work and WorkWell Bolton referral information. WorkWell's continued funding/capacity is marked unconfirmed because the original notice funded the programme only to March 2026.
8. Added an optional compatible-model extractor, disabled by default. It accepts bounded exact input excerpts only; invalid/unavailable output falls back to local rules. Models do not write recommendations or citations.
9. Added manager review, selection of one to three options, next steps, review date and browser Print / Save as PDF. The backend rechecks the situation and selections before creating a discussion draft.
10. Added five fictional demo scenarios, crisis/urgent stopping behaviour, input bounds, safe validation errors, no-store headers and no employee-record persistence.
11. Tested the module, inspected desktop/mobile screenshots, and documented executed checks and remaining limitations.

## Exact areas added

Paths in this table are relative to `modules/adjust/`. Every listed path is module-owned.

| Area | Files | Purpose |
|---|---|---|
| API entry point | `backend/adjust_api/main.py`, `backend/adjust_api/__init__.py` | Independent FastAPI app, exported APIRouter, endpoints, privacy/body-limit/error handling |
| Contracts | `backend/adjust_api/models.py` | Strict request/result/plan models; unknown fields rejected |
| Orchestration/plan | `backend/adjust_api/engine.py` | Safety-first pipeline, conversation guide and trusted plan reconstruction |
| Extraction | `backend/adjust_api/extraction.py` | Role/tasks/barriers/limitations/constraints, missing information and simple negation handling |
| Safety | `backend/adjust_api/safety.py` | Conservative phrase checks; stop normal workflow for immediate/urgent risks |
| AI adapter | `backend/adjust_api/providers.py` | Optional server-only exact-excerpt provider and fallback; no default model call |
| Retrieval/validation | `backend/adjust_api/knowledge.py` | Current verified passages, exact publisher/URL checks, metadata and date validation |
| Options | `backend/adjust_api/recommendations.py` | Authored, source-bound practical discussion options |
| Support | `backend/adjust_api/referrals.py` | Official and local referral-directory entries with limitations |
| Backend test/runtime configuration | `backend/tests/test_adjust.py`, `backend/requirements.txt`, `backend/pyproject.toml` | 53 deterministic backend tests; pinned Python requirements |
| Employer UI | `frontend/components/adjust-workspace.tsx` | Complete workspace and seven-screen journey; in-memory state |
| Print plan | `frontend/components/plan-preview.tsx` | Nine-section printable discussion draft |
| App entry/layout | `frontend/app/page.tsx`, `frontend/app/layout.tsx`, `frontend/app/error.tsx` | Independent Next app, metadata, skip link and recovery |
| Styling | `frontend/app/globals.css` | ADJUST design, responsive layouts, focus states and A4 print rules |
| Frontend contracts/client | `frontend/lib/types.ts`, `frontend/lib/api.ts` | ADJUST-specific TypeScript types, same-origin client, timeouts and error handling |
| Frontend runtime configuration | `frontend/package.json`, `frontend/next.config.ts`, `frontend/tsconfig.json`, `frontend/next-env.d.ts` | Independent Next app and API proxy; generated Next types stay module-owned |
| Frontend unit tests | `frontend/vitest.config.ts`, `frontend/tests/setup.ts`, `frontend/tests/api.test.ts`, `frontend/tests/workspace.test.tsx` | 10 frontend tests |
| Browser tests | `frontend/playwright.config.ts`, `frontend/tests/e2e/adjust.spec.ts` | Seven workflows, mobile/keyboard/privacy checks and one-page PDF verification |
| Knowledge data | `knowledge/catalogue.json`, `knowledge/catalogue.py`, `knowledge/__init__.py`, `knowledge/VERIFICATION.md` | Runtime catalogue, original authoring record and source-review provenance |
| Launch/check tooling | `scripts/start.py`, `scripts/check.py`, `Open ADJUST.command`, `Open ADJUST.bat` | Module-only startup, dependency preparation and isolated checks |
| Environment/ignore rules | `.env.example`, `.gitignore` | ADJUST-specific configuration; exclude generated/dependency files |
| Documentation | `README.md`, `PROJECT_LOG.md`, `integration-manifest.json`, `docs/repository-audit.md`, `docs/api-contract.md`, `docs/accessibility.md`, `docs/validation.md`, `INTEGRATION_HANDOFF.md` | Usage, implementation log, integration contract and validation evidence |

`catalogue.json` is what the backend reads. Keep its authoring record consistent if editing both. Employee information is not part of the catalogue.

## Existing areas left unchanged by this implementation

- Host `frontend/app/`, `frontend/components/`, `frontend/lib/`, styles, package files and API rewrites.
- Host `backend/app/`, module registry, AI services, API contracts and authentication implementation.
- Database/schema/migrations and existing synthetic resource/case data.
- Host configuration and original CIVICFORGE launch/check scripts.
- Any Bolton Connect components.

The shared working tree already contains unrelated edits in the root README, deployment/hackathon documents, host Next type file and original launchers. Do not attribute or overwrite those changes when moving ADJUST. During this build the shared `PROJECT_LOG.md` also gained an externally authored public-preview entry; this implementation preserved it. ADJUST's own implementation log is `modules/adjust/PROJECT_LOG.md`.

## Runtime and API contract to retain

| Component | Current contract |
|---|---|
| UI | `http://127.0.0.1:3001/` |
| API | `http://127.0.0.1:8766/api/adjust/` |
| OpenAPI UI | `http://127.0.0.1:8766/docs` |
| ASGI application | `adjust_api.main:app`, with working directory `modules/adjust/backend` |
| Exported router | `adjust_api.main:router`; already has prefix `/adjust` |
| Browser requests | `/api/adjust/...`; module Next rewrites them to its backend |
| Request storage | None; no database, migrations, case IDs, localStorage/sessionStorage or plan-storage endpoint |
| PDF | Frontend `window.print()`; browser Save as PDF, not a backend PDF endpoint |

Endpoints:

```text
GET  /api/adjust/health
GET  /api/adjust/knowledge?q=
GET  /api/adjust/scenarios
GET  /api/adjust/support
POST /api/adjust/analyse
POST /api/adjust/plan
```

Full schemas and examples are in `docs/api-contract.md` and the API's `/docs`. Results are ADJUST-specific structures, not the host's persisted `Case → Analysis` envelope.

## Combining the two modules

### Option A: shared entry page, independent modules

This is the smallest integration change for the current implementations. Give the host one entry page/navigation with a link to each module, while ADJUST retains its own UI/API/runtime and data boundary. A combined launcher can start the required services. There is no need to merge adjustment descriptions into the host case database.

For a single public website/port using a reverse proxy, ADJUST needs a deliberate subpath configuration. Its Next app currently expects `/`, and its assets use the normal Next asset paths. **Proxying `/adjust` to the current root application alone is insufficient**: configure a Next `basePath`/asset routing strategy, preserve `/api/adjust/*` handling, and test both apps' `_next` assets. Do not rely on a hard-coded temporary tunnel URL.

### Option B: one shared Next frontend and FastAPI backend

The following changes would be required; they have not been applied:

1. **Frontend route/layout:** add a reviewed host route such as `/adjust`. ADJUST currently renders a full workspace with its own sidebar, topbar and `main#main-content`. The host `AppShell` also renders these. Choose the shared shell or a dedicated route layout and remove the duplicate shell/landmarks for that route.
2. **Import aliases:** module `@/` resolves to `modules/adjust/frontend`. The host's `@/` resolves to the host frontend. Convert module imports to relative paths or add an explicit ADJUST alias before importing its components into the host.
3. **CSS isolation:** module CSS uses global `:root`, `body`, `main`, input/button rules and class names also used by the host, including `.sidebar`, `.brand`, `.topbar`, `.button` and `.nav-item`. Scope or convert these styles; do not append the stylesheet wholesale to host globals. Scope print rules so exporting an ADJUST plan does not affect the other module.
4. **API routing:** the host's existing `/api/:path*` rewrite targets port 8765. If keeping ADJUST's API on 8766, add a more specific `/api/adjust/:path*` rewrite before that catch-all. If merging APIs into 8765, include the exported router once with prefix `/api`; the router already contributes `/adjust`, so avoid doubling that segment.
5. **Python import/package location:** make `adjust_api` importable by the host process. Keep the knowledge directory's relationship to the package or update `CATALOGUE_PATH`; it currently resolves the JSON relative to the module's physical folder. Merely copying Python files into the host package will break that lookup unless adapted.
6. **Privacy middleware and errors:** including only the APIRouter does not carry over `create_app()` middleware or exception handlers. Preserve the 16 KB request bound, sanitized validation errors, no-store responses and suitable request logging/access controls in the combined app.
7. **Authentication:** ADJUST is a local prototype and does not inherit host demo-role authentication. Apply the combined application's appropriate identity/access boundary. User-selectable demo headers are not production authentication.
8. **Persistence boundary:** keep adjustment analysis out of the generic host enquiry/case-creation path. That path persists requests; ADJUST's default promise is no employee health-data persistence. Any intentional saving would be a separate product/data-handling change.
9. **Contracts and AI settings:** retain ADJUST's own result types and `ADJUST_AI_*` configuration. Do not cast its response to the host case type or silently turn on the host provider. The optional model remains off unless deliberately configured and requested.
10. **Registry:** the module exports a router, but is not a registered `CivicModule` subclass. A registry adapter and shared navigation/types/configuration would be new work. Registering it must not implicitly send descriptions through the persisted case workflow.
11. **Verification:** rerun ADJUST checks and the second module's regression checks after integration. Specifically test both navigation/layouts, conflicting API paths, source availability, missing evidence, crisis blocking, employee-data handling and printing one module without including the other.

## Copy/merge instructions

Keep the entire `modules/adjust/` source tree together, including `knowledge/catalogue.json`, documentation and dotfiles. Preserve the executable bit on `Open ADJUST.command` and Python scripts. For a clean transfer exclude:

```text
node_modules/     .venv/         __pycache__/       .pytest_cache/
.next/           .next-check/   .next-e2e/         *.tsbuildinfo
test-results/    .runtime/      .env
```

The development `frontend/node_modules` entry on this Mac is a symlink to the host's installed dependencies. It is not a portable dependency bundle; let the launcher prepare dependencies at the destination. Python can similarly reuse the installed host virtualenv locally, but ADJUST has its own requirements and fallback environment preparation.

To review or commit this work independently, select only `modules/adjust/`; review the root's other modified files separately. The implementation commit was created in a separate publishing checkout and pushed to the user-specified repository. No PR, new branch or deployment configuration was created.

## Launch and reproduce validation

From the repository root:

```sh
python3 modules/adjust/scripts/start.py
```

From `modules/adjust/`:

```sh
python3 scripts/check.py
ADJUST_BROWSER_CHANNEL=chrome python3 scripts/check.py --e2e
```

The second command uses an installed Chrome browser. Alternatively install the Playwright Chromium expected by the module package and omit `ADJUST_BROWSER_CHANNEL`. The end-to-end helper uses isolated test ports **3186/8786** and its own build directory, then shuts those test servers down.

Important variables:

```text
ADJUST_PYTHON          Supported Python executable override
ADJUST_UI_PORT         UI port, default 3001
ADJUST_API_PORT        API port, default 8766
ADJUST_BACKEND_URL     Next proxy destination; launcher sets it
ADJUST_BUILD_DIR       Module-only Next build directory
ADJUST_TEST_URL        Optional existing UI to exercise
ADJUST_BROWSER_CHANNEL Optional installed Playwright browser channel
ADJUST_AI_BASE_URL     Optional compatible extractor endpoint
ADJUST_AI_MODEL        Optional model name
ADJUST_AI_API_KEY      Server-only credential; never NEXT_PUBLIC_*
```

## Results already obtained

Last complete implementation check: `ADJUST_BROWSER_CHANNEL=chrome python3 scripts/check.py --e2e`, exit **0**.

| Check | Executed result |
|---|---|
| Backend | 53 passed |
| Frontend unit tests | 10 passed |
| Browser workflows | 7 passed |
| Total test cases | 70 passed |
| TypeScript | Passed |
| ADJUST production build | Passed |
| Standard three-option warehouse PDF | Valid PDF, one A4 page |
| Desktop/mobile layouts | Screenshots inspected; tested mobile width 390 px |
| Existing application source hash comparison | No changes from this implementation |

These are results from the completed module build, not a claim that a combined application has been tested. This handoff-only update does not rerun tests or change runtime behaviour.

## Outstanding limits to preserve in the combined product

Local extraction/safety rules are heuristics, not validated clinical triage or a real-world accuracy benchmark. Optional AI was tested with mocks, not live model calls. An editorial-owner role is recorded; an accountable named human and qualified professional content review remain to be assigned. WorkWell Bolton's continued funding/capacity is unconfirmed. Windows, screen readers, zoom/cross-browser coverage and PDF accessibility certification remain outstanding. No legal-compliance claim is made.

## Files to read first

1. This handoff — ownership and merge hazards.
2. `integration-manifest.json` — machine-readable runtime/interface summary.
3. `docs/api-contract.md` — request/response and status behaviour.
4. `docs/validation.md` — exact test evidence and limitations.
5. `PROJECT_LOG.md` — implementation history.
