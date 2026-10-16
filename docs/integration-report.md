# CIVICFORGE AI integration report

## Pre-change inspection — 16 October 2026

Inspected Adjust's `modules/adjust/integration-manifest.json` and Bolton Connect's `modules/bolton-connect/backend/bolton_api/plugin.py` / `INTEGRATION.md`, plus actual API, UI, settings, stores, dependencies and tests before application edits. At this pre-change checkpoint the PowerPoint was unopened; the user subsequently authorised its colours and a supplied logo. The later presentation-only update is recorded in [branding.md](branding.md).

| Concern | Finding / integration decision |
| --- | --- |
| API namespaces | `/api/bolton-connect/*`, `/api/adjust/*` and original `/api/*` are distinct. Dispatch complete module apps before the host catch-all; do not rename APIs. |
| Frontend routes | Original host `/` must become the requested landing page; retain its full existing portal at `/portal`. Isolate module documents/styles/scripts. Adjust's Next assets need an optional base path. |
| Dependencies | Host/Adjust use Next 15, React 19, TypeScript; backend FastAPI/Pydantic/httpx compatible. Bolton has a build-free UI and standard-library SQLite. No dependency upgrade needed. |
| Environment | Host uses unprefixed auth/demo settings; Bolton uses `BOLTON_*`; Adjust uses `ADJUST_*`. Integrated Bolton must inherit host auth and demo mode. Keep standalone defaults. |
| Database | Host SQLAlchemy and Bolton SQLite are separate despite similarly named tables. Adjust persists no employee data. No shared migrations or data transfer; reject aliased database paths. |
| Authentication | Host and Bolton demo roles are synthetic controls, not identities. Integrated staff/admin checks must accept the same host credentials. Adjust's public local discussion flow does not grant council access. |
| Shared components | Reuse complete module interfaces; isolate their global CSS/JS and preserve host components. Shared navigation must not carry case IDs, descriptions or invitation fragments between modules. |
| Middleware | Bolton's passive adapter drops its request guard/startup; Adjust's exported legacy router drops current case routes and privacy/error middleware. Preserve complete apps and their lifecycles. |
| Consent | Resident save/share choices remain explicit. Adjust reviewed handoffs stay inside Adjust. Navigation passes no sensitive data between modules. |
| Capability mismatch | No existing tracked referral workflow: Referrals can expose the existing consent-shared case/service guidance only. Adjust suggestions/conversation require both reviewed contributions; links must not skip those gates. |
| Baseline tests | Bolton 15 passed; Adjust backend 99 passed, frontend 60 passed. Original host checks pending. Historical results in project logs are not treated as current validation. |

Implementation, executed validation, changed files, deployment and limitations will be recorded below after integration.

## Delivered integration

The original application remains operational. Its previous resident portal is at `/portal`; `/operations`, `/intelligence`, `/impact`, `/admin`, `/demo` and their original APIs retain their functionality. `/` is now **CIVICFORGE AI — Bolton Connect**, with the three requested primary choices.

Navigation opens with a menu button on desktop and mobile, closes on selection/Escape/backdrop, and constrains keyboard focus while open. It contains exactly the requested module hierarchy, plus links to the existing workspace. Integrated pages identify Bolton without rewriting the original configurable challenge.

| Navigation | Existing interface / behaviour |
| --- | --- |
| Resident Support → Assessment | Bolton Connect's existing resident form. |
| Local Services / Training / Employment Pathways / Action Plan | Stable anchors in the existing completed result; assessment remains a prerequisite. |
| Workplace Adjustments → Employer Assessment | Adjust AI's existing employer/employee workspace. |
| Adjustment Suggestions / Conversation Guide / Adjustment Plan | Existing combined-plan sections, available after both reviewed contributions. |
| Council Dashboard → Case Review | Bolton Connect's consent-shared case queue. |
| Referrals | Existing service guidance inside an opened case. No sending/tracking feature was added. |
| Aggregated Insights | Existing de-identified Bolton summary counts. Adjust data is excluded. |

### Runtime and route boundaries

```text
Browser → CIVICFORGE Next.js :3000
           /                         unified landing
           /portal + original routes original application
           /resident-support         isolated Bolton resident document
           /workplace-adjustments    isolated Adjust AI document
           /council                  isolated Bolton adviser document
           /modules/adjust/*      → Adjust Next.js :3002 (internal)
           /module-assets/bolton-connect/* → host API static assets
           /api/*                 → host FastAPI :8765
                                      original /api/* → original app/store
                                      /api/bolton-connect/* → complete Bolton app/store
                                      /api/adjust/* → complete stateless Adjust app
```

The embedded documents retain their own CSS and script scopes. Adjust has an optional base path and same-origin framing policy; its standalone defaults still disallow framing. No module was rebuilt or replaced. The only module-owned edits are integration configuration, display name/sidebar, section anchors, a context-local settings hook and long-text wrapping.

### Conflicts resolved

1. **Incomplete router adapters:** dispatch complete module ASGI applications with their original full API paths and explicit lifespan entry/exit. Adjust's two-sided endpoints, privacy middleware, error redaction and body limit remain active. Bolton's startup, seed and request controls remain active. Module requests do not spend the original host's rate budget.
2. **Identity/demo mismatch:** integrated Bolton inherits host `DEMO_MODE`, `STAFF_API_TOKEN` and `ADMIN_API_TOKEN`; separate module settings cannot re-enable demo access. Tests reject demo headers and legacy module tokens under a non-demo host. The launcher refuses reuse when the running mode differs from the requested mode.
3. **Route/style/asset collisions:** move the original portal to `/portal`; keep module documents isolated; proxy Adjust's namespaced Next assets to its own interface process. Use explicit Bolton `index.html` to avoid Next/StaticFiles trailing-slash redirect loops.
4. **Store collisions:** reject paths that resolve to the host database, including aliases/symlinks/hard links. No tables are merged, renamed or copied. Adjust remains stateless. No database migration is added; the original host Alembic migrations and Bolton's existing additive table creation remain unchanged.
5. **Privacy and erasure:** preserve explicit resident saving/sharing, separate reviewed Adjust handoffs, bounded bodies and redacted errors. All integrated module API responses receive `no-store`, `no-referrer` and `nosniff`, including oversized-body errors. DELETE remains available for Bolton's existing erase route.
6. **Invitation lifecycle:** resolve incoming Adjust fragments before mounting its document, strip the host fragment, and remount for a repeated reviewed link after clearing a session. This fixes an intermittent initial-load race exposed by the full browser suite.
7. **Responsive long values:** wrap saved links, references and long resident names within Bolton result/detail cards. Verified at 390px with a maximum-length unbroken fictional name.

### Consent and authorisation

Navigation transfers no resident text, names, session/case identifiers, health details or private employer figures between modules. Shared navigation reads section IDs/layout only. Only Adjust's own reviewed handoff fragment is forwarded into Adjust; its existing allowlist validation still runs. Existing plan requests exclude private descriptions and cost figures. No transfer from Bolton to Adjust was introduced, so no cross-module consent mechanism is needed or implied.

Resident saving and adviser sharing remain separate, unchecked choices. Only explicitly shared Bolton cases enter the council queue. Existing saved-plan links are capability links; existing Adjust handoff links are reviewed content, not verified identity or proof of agreement. Both limitations remain explicit.

## Files changed for this integration

The repository already contained unrelated uncommitted launcher/documentation changes and untracked modules. Those were preserved; no commit, reset, replacement of the application, public deployment or PowerPoint read was performed.

| Files | Purpose |
| --- | --- |
| `backend/app/integrations.py` (new), `backend/app/main.py` | Complete module dispatch, lifecycles, host identity, store checks, privacy/error boundary, Bolton static assets, DELETE CORS. |
| `backend/tests/test_integration.py` (new), `backend/tests/conftest.py` | Thirteen integration cases and disposable module stores for host tests. |
| `frontend/app/page.tsx`, `frontend/app/layout.tsx` | Unified landing and document title. |
| `frontend/app/portal/page.tsx` (new location) | Preserve the full previous resident portal. |
| `frontend/app/resident-support/page.tsx`, `frontend/app/workplace-adjustments/page.tsx`, `frontend/app/council/page.tsx` (new) | Existing module interfaces under the unified shell. |
| `frontend/components/app-shell.tsx`, `frontend/components/module-frame.tsx` (new), `frontend/app/globals.css` | Requested hierarchy, button-operated drawer, isolated documents, section navigation, reviewed invitation lifecycle, responsive landing. |
| `frontend/next.config.ts` | Namespaced module asset/interface proxying. |
| `frontend/tests/e2e/integration.spec.ts` (new), `frontend/tests/e2e/civic-workflow.spec.ts` | Four integration journeys; preserve six original browser tests at the relocated portal. |
| `modules/bolton-connect/backend/bolton_api/settings.py` | Context-local host configuration, preserving standalone defaults and concurrent app isolation. |
| `modules/bolton-connect/frontend/app.js`, `adviser.html`, `styles.css` | Stable existing section anchors and narrow-screen long-value wrapping. |
| `modules/adjust/frontend/next.config.ts`, `app/page.tsx`, `app/layout.tsx`, `app/globals.css` | Optional base path/framing, embedded mode, Adjust AI display name and sidebar toggle; original palette retained. |
| `modules/adjust/frontend/components/two-sided-workspace.tsx`, `components/combined-plan.tsx` | Existing section anchors and unified reviewed invitation/return URLs. |
| `modules/adjust/frontend/tests/two-sided-workspace.test.tsx` | Embedded link/sidebar regression test. |
| `modules/adjust/frontend/tsconfig.json`, `modules/adjust/.gitignore` | Generated integration build-type paths; exclude separate build outputs. |
| `scripts/start.sh`, `scripts/start_windows.py`, `scripts/setup.sh`, `scripts/check.sh`, `.env.example` | Three-process startup/reuse/cleanup, mode mismatch rejection, both frontend dependencies and all integration checks. Existing double-click wrappers remain compatible. |
| `backend/Dockerfile`, `frontend/Dockerfile`, `modules/adjust/frontend/Dockerfile.integrated` (new), `docker-compose.yml`, `.dockerignore` | Include existing module code, isolated Adjust service/readiness and separate store; exclude module secrets/build output. |
| `README.md`, `docs/deployment.md`, `docs/integration-report.md`, `docs/test-results.md`, `PROJECT_LOG.md` | Operation, validation, limitations and handoff. |

## Executed validation — 16 October 2026

Final full gate (exit 0):

```bash
PLAYWRIGHT_CHROMIUM_EXECUTABLE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' ./scripts/check.sh --e2e
```

| Check | Result |
| --- | --- |
| Host backend, including integration | 38 passed (25 original + 13 new). |
| Standalone Bolton backend | 15 passed. |
| Adjust backend | 99 passed. |
| Host frontend unit tests | 10 passed. |
| Adjust frontend unit tests | 61 passed (60 original + 1 integration test). |
| Both TypeScript checks | Passed. |
| Host production build `.next-validation` | Passed; original and integrated routes generated. |
| Embedded Adjust production build `.next-integrated` | Passed with `/modules/adjust` and embedded mode. |
| Host Playwright | 10 passed in 34.0s (6 original + 4 integration). No skipped tests. |
| Standalone Adjust Playwright | 8 passed after scoped frontend integration edits. |
| Original live proxy smoke | All six modules passed; staff review, feedback, labelled impact, access/validation/audit boundaries and two resets passed. |
| Launcher live startup and repeat execution | Host/API/embedded Adjust ready; repeat exits0 and reuses healthy services. |
| Launcher requested non-demo while demo running | Exits1 with explicit mode-mismatch/restart message; does not reuse the demo. |
| Script syntax, Compose YAML, whitespace | Python compilation, Bash syntax, YAML/service dependency parsing, `git diff --check` passed. |

Existing FastAPI `on_event`, AnyIO/Starlette and terminal colour deprecation/configuration warnings remain; they did not fail the suites. First static YAML parsing used the unsupported default interpreter without PyYAML; rerun in the project Python3.13 virtual environment passed. No container-runtime success is claimed.

The first combined browser run exposed the invitation race (9 passed, 1 failed); it was fixed and the entire final gate reran successfully. Initial standalone narrow-screen plan testing exposed long-value overflow; the wrapping fix passed a complete repeat with a maximum-length name.

### Complete resident journey: independently and unified

- Actual standalone Bolton ran on loopback8109 with its own temporary SQLite database and deterministic provider. Browser: assessment → services/training/employment → complete plan → explicit save/share → saved-link resume → adviser note/status readback. Unconsented submission left counts unchanged; unauthorised adviser request was403. Mobile390px completed result and adviser view had no horizontal overflow, including an80-character unbroken fictional name. All21 browser requests stayed on8109; no host or Adjust requests occurred. Test-owned server/database were removed; original seed count restored before cleanup.
- Through unified navigation: landing resident choice → same complete assessment/plan → each requested result-section link without losing the plan → explicit save/share → Case Review → adviser note and `in_review` readback. Then Employer Assessment opened an empty workplace form; no resident markers, case/session identifiers or raw data entered Adjust requests. Test-created integrated sessions were erased by the test.

Standalone command used by the verification harness:

```bash
node /tmp/civicforge-bolton-standalone-check/journey.cjs
# Starts backend/.venv/bin/python -m uvicorn bolton_api.app:app
# from modules/bolton-connect/backend on8109 with a disposable BOLTON_DATABASE_PATH.
```

### Complete employer journey: independently and unified

- Standalone Adjust's eight existing browser journeys passed against its own3001/8766 services, including employer-first and employee-first discussion, reviewed invitation/return links, combined plan, actual one-page PDF, mobile/keyboard, private cost isolation and existing safety stops. Command from `modules/adjust/frontend`:

```bash
ADJUST_TEST_URL=http://127.0.0.1:3001 ADJUST_BROWSER_CHANNEL=chrome npm run test:e2e
```

- Through unified navigation: landing employer choice → employer assessment → explicitly review shareable contribution → invitation within `/workplace-adjustments` → second party review → combined suggestions/conversation/plan → starter's identical returned plan. Checked all requested workplace section links, absence of private free text in links/combined-plan bodies, unchanged Bolton counts, fragment stripping and reopening the same saved link after clearing. No module review or consent gate is bypassed.

## Known limitations

- This remains a fictional local prototype. Shared API credentials are enforced, but the original browser interfaces have no production identity-provider/sign-in/session layer; the adviser page uses demo role headers. Outside demo mode those headers fail closed. A production authentication system was not added during integration.
- Referrals means existing service/referral guidance; no tracked referral system exists or was introduced. Aggregated Insights covers Bolton cases only and excludes workplace data.
- Adjust needs both reviewed contributions before suggestions/conversation/plan. Its handoffs do not verify identities, cannot recall copied links/PDFs, and carry reviewed canonical needs in fragments. Bolton saved links are opaque capabilities.
- No real-data, live-model, clinical/legal determination, penetration, assistive-technology, native Windows or PostgreSQL migration validation was performed. Existing source-review and service-availability limitations remain in each module's documentation.
- Docker configuration was updated and parsed, but Docker is unavailable here; image build/runtime and container persistence are unverified. No public deployment or new tunnel was created.
- Module interfaces remain separate documents within the shared shell, each keeping its own styling. Leaving a module clears its unsaved in-memory state under existing privacy behaviour; use existing consented saves/reviewed handoffs when appropriate.
- After the completed integration, the user authorised the PowerPoint palette and supplied logo. Both now appear across the interfaces and print headers; Adjust AI retains its name. See [branding.md](branding.md) for the visual-only follow-up and provenance.

## Deployment instructions

### Local synthetic demonstration

1. Use Python3.11–3.13 and Node22+. From this repository run `./scripts/start.sh`, or double-click the existing macOS/Windows launcher. Initial dependency installation needs internet. Open `http://127.0.0.1:3000/`.
2. Keep the terminal open. The helper runs host API8765, host UI3000 and embedded Adjust UI3002 on loopback, checks health, and cleans up its own children on Ctrl+C. Repeating the launcher reuses healthy matching-mode services. Stop the old launcher before changing mode, tokens, store paths or service URLs.
3. Optional root `.env`: `BACKEND_PORT`, `FRONTEND_PORT`, `BACKEND_URL`, `CORS_ORIGINS`, `ADJUST_EMBED_PORT`, `BOLTON_DATABASE_PATH` and existing server-only provider configuration. The helper supplies the embedded interface URL/base path. Never place keys in public frontend variables.
4. Run the final gate above against the running app. Use installed Playwright Chromium instead of the shown local Chrome executable on another machine. Module standalone launchers remain unchanged: Bolton `./modules/bolton-connect/scripts/run.sh`; Adjust `python3 modules/adjust/scripts/start.py`.

### Production-mode local build commands (synthetic verification only)

Run each server in its own terminal after preparing dependencies. Supply the same environment for a frontend's build and start; Next rewrite targets/base path are baked into its build.

```bash
# Terminal 1: complete host and module APIs
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765

# Terminal 2: isolated Adjust interface (from repository root)
cd modules/adjust/frontend
ADJUST_BASE_PATH=/modules/adjust ADJUST_EMBEDDED=1 ADJUST_BACKEND_URL=http://127.0.0.1:8765 ADJUST_BUILD_DIR=.next-integrated npm run build
ADJUST_BASE_PATH=/modules/adjust ADJUST_EMBEDDED=1 ADJUST_BACKEND_URL=http://127.0.0.1:8765 ADJUST_BUILD_DIR=.next-integrated npm run start -- --hostname 127.0.0.1 --port 3002

# Terminal 3: host interface (from repository root)
cd frontend
BACKEND_URL=http://127.0.0.1:8765 ADJUST_FRONTEND_URL=http://127.0.0.1:3002 NEXT_BUILD_DIR=.next-validation npm run build
BACKEND_URL=http://127.0.0.1:8765 ADJUST_FRONTEND_URL=http://127.0.0.1:3002 NEXT_BUILD_DIR=.next-validation npm run start -- --hostname 127.0.0.1 --port 3000
```

These are production JavaScript builds of the synthetic prototype, not approval to use real data. If `DEMO_MODE=false`, supply distinct host staff/admin tokens of at least24 characters and complete an authenticated browser session integration before live use. Integrated Bolton ignores separate module identity tokens and follows the host.

### Data safety and rollback

Stop writers and back up `data/civicforge.db`, `modules/bolton-connect/data/bolton_connect.db` (or configured paths), and `config/challenge_config.yaml` before upgrading. Include SQLite WAL/SHM state using a consistent SQLite backup procedure if writers cannot be stopped. Never point the two apps at the same store. This change introduces no migration or copying between stores. Retain both existing data files when reverting application code; do not delete data volumes or use demo reset as a rollback mechanism. Adjust has no server data to migrate.

### Containers

`docker compose up --build` defines the host API, host UI and internal Adjust UI, with separate Bolton/host database paths, readiness dependencies and persistent data/configuration volumes. This path has not been executed here. Verify image build, all three health endpoints, both complete journeys, consent/auth boundaries, restart persistence and rollback in the target environment before relying on it. Keep ports internal behind one authenticated HTTPS origin for any approved hosted environment. No deployment has been performed by this integration task.


## Subsequent authorised branding

The user supplied `IMG_9385.PNG` and explicitly authorised the PowerPoint colours after integration completed. [Branding sources and palette](branding.md) records exact colours, unchanged logo assets and presentation-only scope. Original integration test evidence above remains historical; final branding validation is recorded separately in the project log and test-results document.


## Subsequent reference-page and fluid-layout redesign

The user subsequently replaced the three-choice landing requirement with the supplied `Adjust_ practical help to keep people in work.html` design. The current `/` uses its practical-help heading, scenario form, example chips and Employee/Business controls, then enters the existing Adjust assessment with all confirmation/review gates. Header branding is Adjust AI at the far left and Talk to an advisor at the far right; the link reaches existing advice sources. Resident and adviser workflows remain in the menu.

CIVICFORGE and Bolton Connect product labels have been removed from visible screens, document titles, controlled synthetic provenance labels and generated print/download branding. Internal API paths, IDs, existing database files and historical records remain compatible. Geographical Bolton and official source attribution remain accurate. Persisted legacy synthetic labels are renamed only when displayed, without rewriting user content or the store.

The resident/adviser documents now use fluid responsive layouts for assessment, results, queue and detail views. Intrinsic iframe sizing follows content, including cached initial loads and internal document navigation; shared section/advisor navigation scrolls the host to the correct content. See `docs/ui-redesign.md` and the project log for current scope and executed verification.
