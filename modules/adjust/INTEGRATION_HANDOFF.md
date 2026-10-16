# Current two-sided implementation addendum — 16 October 2026

This worktree now has the employee-first and employer-first flow, canonical statement review/edit/removal, invitation/return links, shared sourced five-part plan, carers and employer-private cost comparison. The historical employer-only inventory below describes the previously published release. **The new work has not been pushed or deployed.** The local app is running on 3001/API8766.

New primary files are `backend/adjust_api/cases.py`, `frontend/components/two-sided-workspace.tsx`, `combined-plan.tsx`, `cost-comparison.tsx`, `frontend/lib/case-api.ts`, `knowledge/two-sided-guidance.md` and their tests. Page entry, metadata, module-only CSS and main router mounting changed additively. Legacy employer components/APIs remain for compatibility.

No shared case database or storage may be added when integrating this design. Handoff fragments contain only reviewed canonical IDs, category, business size and review date. The second person must send a return link; there is no saved case or automatic synchronisation. Keep fragments out of logging, preserve no-referrer/no-store headers and the strict codec, and explain that copied links/PDFs cannot be recalled. Both-party review is a demo control, not verified identity or agreement. The private cost component must stay outside shared state/APIs/links and inside `.no-print`.

Three scoped subagents assisted the current implementation/research/testing in this chat; the older no-subagent statement below applies only to its historical batch. Current executed validation: backend99, frontend60, browser8 passed; TypeScript and production build passed. See `docs/validation.md` and `PROJECT_LOG.md` for commands, failure fixes and limits. No external model call or unrelated application change.

---

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

---

# BOLTON CONNECT integration handoff — 16 October 2026

> Added by the **Bolton Connect** implementation — the "second implementation"
> referenced in the ADJUST sections above. Everything above this line is the
> ADJUST author's handoff and is left unchanged. Nothing in Bolton Connect
> imports, depends on, reads, or modifies the Adjust module; the two were built
> independently and only meet at the host level.

## Scope and current state

Implemented **Bolton Connect — AI-assisted employment and community support for
Bolton residents** as an independent CivicForge module. A resident describes their
situation in free text; the module produces a structured understanding, matches a
grounded Bolton support directory, suggests demonstration employment/training
routes, and generates a plain-English ten-section action plan to review **with a
human adviser**. A separate council adviser view lists consent-shared cases.

Repository: `/Users/ankit/Documents/Hackathon 16 oct/civicforge-ai`

**All implementation owned by this work is inside `modules/bolton-connect/`.** The
module's working files are uncommitted; there is no Bolton Connect commit SHA yet
(observed HEAD `eb3cc95` is not a Bolton Connect delivery commit). It has not been
registered in the host module registry or embedded in the host layout — that is a
separate, documented-not-applied change (`modules/bolton-connect/INTEGRATION.md`).

Bolton Connect serves its resident portal, its adviser view, and its API from a
**single** app on **127.0.0.1:8099**. This does not collide with ADJUST (3001 /
8766) or the host (8765).

## Work completed

1. Audited the existing stack and built the module without editing any host or
   Adjust files. All shared-app changes are documented, never applied.
2. Strict Pydantic v2 contracts (`extra="forbid"`): assessment, matching,
   pathways and a ten-section action plan, each item carrying a provenance label.
3. Deterministic resident assessment extracting employment status, experience,
   skills, goals, practical barriers, support needs, training interests and
   preferences; asks a single clarifying question when there is too little to act
   on rather than guessing. Optional vendor-neutral OpenAI-compatible LLM, **off
   by default**, output re-screened with a safe deterministic fallback.
4. Grounded Bolton support directory (11 services) from official sources, with a
   `verification_status` gate: only `verified`/`source_listed` active services are
   auto-recommendable; contact details are exposed only for `verified` entries.
5. Hybrid matching producing `ELIGIBLE` / `POTENTIALLY_ELIGIBLE` / `NOT_ELIGIBLE`
   / `UNKNOWN` with reasons and missing-information notes — indications to
   discuss, never entitlement decisions.
6. Employment/training pathways by target sector. Vacancies are demonstration
   examples only (`status="demonstration"`, no employer, disclaimer). A health
   condition or disability is never treated as grounds to exclude a route.
7. Consent-gated persistence (its own SQLite): sessions saved only on explicit
   consent, a consent audit trail, right-to-erase cascade, and de-identified
   adviser aggregates (counts only; no name or raw free text in case summaries).
8. Role-based adviser/admin endpoints (demo `X-Demo-Role` header, or bearer token
   outside demo mode). Prompt-injection and control-character screening at the
   schema boundary; body-size and per-client rate-limit middleware.
9. Build-free resident portal (accessible: skip link, aria-live, keyboard nav,
   responsive, print CSS) and an adviser dashboard; XSS-safe DOM construction.
10. Six synthetic demo personas (scenarios A–F), seeded idempotently on first run
    in demo mode so the adviser view is populated immediately.
11. Automated tests and a browser walkthrough of both views; wrote `README.md`
    and a documented-not-applied `INTEGRATION.md`.

## Exact areas added

Paths are relative to `modules/bolton-connect/`. Every listed path is
module-owned. `data/bolton_connect.db` is a runtime artefact (git-ignored; seeded
on first run) and is not source.

| Area | Files | Purpose |
|---|---|---|
| Standalone app | `backend/bolton_api/app.py`, `backend/bolton_api/__init__.py` | FastAPI app, CORS, body-size + rate-limit middleware, startup seeding, static mount |
| HTTP API | `backend/bolton_api/routes.py` | `/api/bolton-connect` router; resident + staff endpoints |
| Contracts | `backend/bolton_api/schemas.py` | Strict assessment/match/pathway/plan models; provenance + verification literals |
| Configuration | `backend/bolton_api/settings.py` | `BOLTON_`-prefixed settings; deterministic defaults |
| Assessment | `backend/bolton_api/assessment.py` | Deterministic extraction, clarifying-question logic, LLM sanitisation |
| Optional AI adapter | `backend/bolton_api/providers.py` | Vendor-neutral OpenAI-compatible client; off by default; key never leaked |
| Directory | `backend/bolton_api/directory.py`, `data/support_directory.json` | Grounded Bolton services; verification-gated loading |
| Matching | `backend/bolton_api/matching.py` | Eligibility states, reasons, missing-info; closed/unverified withheld from auto-recommend |
| Pathways | `backend/bolton_api/pathways.py` | Target-sector routes; demonstration-only opportunities |
| Action plan | `backend/bolton_api/action_plan.py` | Ten-section plan; per-item provenance tagging |
| Persistence | `backend/bolton_api/persistence.py` | stdlib `sqlite3`; consent audit, right-to-erase, de-identified aggregates |
| Auth | `backend/bolton_api/auth.py` | Role resolution (demo header / bearer token); staff/admin gates |
| Safety | `backend/bolton_api/safety.py` | Prompt-injection + control-char screening (`check_text`, `safe_excerpt`) |
| Demo data | `backend/bolton_api/demo.py`, `data/demo_residents.json` | Six synthetic personas (A–F); idempotent seeding |
| Host-mount adapter | `backend/bolton_api/plugin.py` | Passive `mount_into(app)` + `MODULE_MANIFEST`; declares no Adjust dependency |
| Prompt | `prompts/assessment_system_prompt.md` | System prompt for the optional extractor |
| Resident UI | `frontend/index.html`, `frontend/app.js` | Resident portal; provenance-labelled plan; consent + resume |
| Adviser UI | `frontend/adviser.html`, `frontend/adviser.js` | De-identified dashboard; case queue; unverified-recommendation warning |
| Styling | `frontend/styles.css` | Accessible responsive CSS, focus-visible, print rules |
| Tests | `tests/conftest.py`, `tests/test_scenarios.py`, `tests/test_api_and_safety.py` | 15 tests: scenarios A–F + API/safety |
| Launcher | `scripts/run.sh` | Standalone launch on 127.0.0.1:8099 (reuses repo venv or builds module `.venv`) |
| Documentation | `README.md`, `INTEGRATION.md` | Usage/safety model and documented-not-applied host integration |

## Existing areas left unchanged by this implementation

- Host `frontend/`, `backend/`, module registry, AI services, auth, migrations
  and existing synthetic data.
- The entire `modules/adjust/` tree, except this handoff file, which the user
  asked me to extend. ADJUST's own sections above are byte-for-byte unchanged;
  Bolton Connect content is additive and clearly delimited.
- The shared working tree's pre-existing unrelated edits (root README,
  deployment/hackathon docs, host Next type file, original launchers) — not
  attributed or overwritten.

## Runtime and API contract to retain

| Component | Current contract |
|---|---|
| UI (resident) | `http://127.0.0.1:8099/` |
| UI (adviser) | `http://127.0.0.1:8099/adviser.html` |
| API | `http://127.0.0.1:8099/api/bolton-connect/` |
| OpenAPI UI | `http://127.0.0.1:8099/docs` |
| ASGI application | `bolton_api.app:app`, working directory `modules/bolton-connect/backend` |
| Exported router | `bolton_api.routes:router` (prefix `/api/bolton-connect`); or `bolton_api.plugin:mount_into(app)` |
| Browser requests | same-origin `/api/bolton-connect/...` (single app serves UI + API) |
| Request storage | Own SQLite `data/bolton_connect.db`; tables `sessions`, `consent_events`, `cases`, `case_notes`. Written **only on explicit consent**; right-to-erase cascade |
| Env namespace | all variables prefixed `BOLTON_`; optional LLM is `BOLTON_LLM_*`, off by default |
| Auth | demo `X-Demo-Role: resident\|staff\|admin`, or `Authorization: Bearer <token>` outside demo mode |
| Export/print | Resident plan: browser Print + Download (JSON); no backend PDF endpoint |

Endpoints:

```text
GET    /api/bolton-connect/health
GET    /api/bolton-connect/directory
POST   /api/bolton-connect/assess
POST   /api/bolton-connect/match
POST   /api/bolton-connect/pathways
POST   /api/bolton-connect/plan
GET    /api/bolton-connect/sessions/{id}
DELETE /api/bolton-connect/sessions/{id}
GET    /api/bolton-connect/cases             (staff)
GET    /api/bolton-connect/cases/{id}        (staff)
PATCH  /api/bolton-connect/cases/{id}        (staff)
POST   /api/bolton-connect/cases/{id}/notes  (staff)
GET    /api/bolton-connect/stats             (staff)
```

Full schemas are in the API's `/docs` and `modules/bolton-connect/README.md`.
Results are Bolton-Connect-specific structures, not the host's persisted
`Case → Analysis` envelope.

## Combining ADJUST + Bolton Connect

The two modules are deliberately parallel and non-overlapping, which makes the
combined product mostly a host-level composition exercise:

| Concern | ADJUST | Bolton Connect | Collision? |
|---|---|---|---|
| Directory | `modules/adjust/` | `modules/bolton-connect/` | None |
| API namespace | `/api/adjust` | `/api/bolton-connect` | None |
| Env prefix | `ADJUST_` | `BOLTON_` | None |
| Ports | UI 3001, API 8766 (test 3186/8786) | UI+API 8099 | None (host API is 8765) |
| ASGI app | `adjust_api.main:app` | `bolton_api.app:app` | Separate processes |
| Exported router | `adjust_api.main:router` (prefix `/adjust`) | `bolton_api.routes:router` (prefix `/api/bolton-connect`) | None |
| Persistence | None (no employee-data storage) | Own SQLite, consent-gated, right-to-erase | Separate stores |
| Python package | `adjust_api` | `bolton_api` | Distinct top-level packages |
| `safety.py` | `adjust_api.safety` | `bolton_api.safety` | Same filename, different packages — no clash |

**Recommended path: Option A (shared entry page, independent modules).** It fits
both implementations with the least risk: give the host one landing/nav with a
link to each module while each retains its own UI/API/runtime and data boundary.
A combined launcher starts the three services (host, ADJUST, Bolton Connect).

For a single public port via reverse proxy: Bolton Connect's app already serves
its own static UI and `/api/bolton-connect/*` from one origin, so it needs no Next
`basePath` work (unlike ADJUST). Route `/api/bolton-connect/*` and the Bolton
Connect static paths to 8099; keep ADJUST's `/adjust` and `/api/adjust/*` routing
as the ADJUST handoff describes; and keep the host's `/api/:path*` catch-all
(8765) **after** both module-specific rules.

If instead merging into one FastAPI backend, mount Bolton Connect via
`bolton_api.plugin.mount_into(app)` (adds the router only). Note that including
only the router does **not** carry over Bolton Connect's middleware (body-size
cap, rate limit), its startup seeding, or its static-file mount — preserve those
in the combined app, exactly as the ADJUST handoff notes for its own middleware.

### Cross-module reconciliation — WorkWell Bolton

Both modules reference **WorkWell Bolton**, and they currently state different
things about its status. This is the one factual point to align before the
combined product ships:

- **ADJUST** (section "Work completed", item 7, and "Outstanding limits") marks
  WorkWell's continued funding/capacity **unconfirmed**, on the basis that the
  original notice funded the programme only to **March 2026**.
- **Bolton Connect** represents WorkWell as **active** and **funded to 31 March
  2027**, offered as `POTENTIALLY_ELIGIBLE` and **referral/invite-based** (never a
  self-referral or automatic sign-up), with a time-limited caveat to confirm it is
  still open. This reflects a live source check performed during the Bolton
  Connect build, which superseded the earlier March-2026 reading.

Neither module invents availability; they disagree only on the funding end-date
and whether to surface it. **Action for integration:** pick one verified source of
truth for WorkWell (recommend the Bolton Connect reading: active, referral-based,
funded to 31 Mar 2027, confirm-before-relying) and make both modules consistent. I
did **not** edit any ADJUST source to change this — flagging it here for a human to
decide.

## Results already obtained

| Check | Executed result |
|---|---|
| Automated tests (`pytest tests/`) | 15 passed (6 scenario A–F + 9 API/safety) |
| Scenario coverage | A clear case, B clarification, C retrain, D returning carer, E health/adjustments, F closed-programme-never-auto |
| Safety tests | consent-gated persistence, RBAC 403, de-identified aggregates, right-to-erase, demonstration-only vacancies, verification-gated contacts, injection + oversized-body rejection |
| Browser walkthrough | Resident portal (scenario A plan, provenance labels, WorkWell caveat, closed-scheme labelling, demonstration vacancies) and adviser view (de-identified counts, flag badges, unverified-recommendation banner); no console errors |
| Standalone server | `GET /api/bolton-connect/health` → 200; UI `/` and `/adviser.html` → 200 |
| Isolation | No `import adjust` anywhere in the module; `MODULE_MANIFEST.depends_on_adjust_module = False` |

Command to reproduce tests, from `modules/bolton-connect/`:

```sh
../../backend/.venv/bin/python -m pytest tests/ -v
```

Launch the module, from `modules/bolton-connect/`:

```sh
./scripts/run.sh            # http://127.0.0.1:8099/  (BOLTON_HOST / BOLTON_PORT override)
```

These are results from the completed Bolton Connect module build, not a claim that
a combined application has been tested.

## Outstanding limits to preserve in the combined product

Deterministic extraction/matching are heuristics, not validated assessment; the
optional LLM was exercised only with the deterministic fallback path, not a live
model. The support directory is grounded but small and needs a named editorial
owner and periodic re-verification (WorkWell's end-date above is the live example).
Demo-role headers are not production authentication. Accessibility was exercised in
Chrome only; screen-reader, zoom, cross-browser and print-accessibility coverage
remain outstanding. No legal-compliance or entitlement claim is made — every
eligibility state is an indication to confirm with a human adviser.

## Bolton Connect files to read first

1. This handoff section — ownership and merge hazards.
2. `modules/bolton-connect/INTEGRATION.md` — documented-not-applied host steps + `MODULE_MANIFEST`.
3. `modules/bolton-connect/README.md` — usage, pipeline and full safety model.
4. `modules/bolton-connect/backend/bolton_api/schemas.py` — the data contracts.
5. `modules/bolton-connect/tests/` — scenario A–F and API/safety evidence.

## ADJUST production hosting handoff — 16 October 2026

Public ADJUST: https://adjust-workplace-assistant.vercel.app. GitHub deployment source is commit `73dbc785ea9d0f8e4568a7b7523596ec3268610c`. Only module deployment metadata/entry points and documentation changed; the original root static demo remains preserved. Public API health returned 200 and all seven browser workflows passed, including one-page PDF printing.

Hosting uses Vercel Services: Next.js in `frontend/` and FastAPI through `api/index.py`, with module-root `vercel.json` and `pyproject.toml`. For future repository-linked builds, use root `modules/adjust`. This deployment does not merge ADJUST into Bolton Connect or the host UI. See `docs/vercel-deployment.md` for project IDs, exact verification command and the pending GitHub Login Connection required for automatic deployments.
