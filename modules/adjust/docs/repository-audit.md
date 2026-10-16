# Repository audit — 16 October 2026

Read `AGENTS.md`, root README, architecture, API contract and challenge-adaptation guide before implementation. The existing working tree already contains launcher/documentation edits; those have been preserved. A SHA-256 inventory of every tracked file was captured before implementation for the final isolation check.

| Area | Existing implementation | ADJUST decision |
|---|---|---|
| Frontend | Next.js 15, React 19, TypeScript, app router | Same stack in a separate module-owned Next application; no changes to host routes/layout |
| Styling/components | Tailwind 4 plus global CSS, Lucide, Radix Slot, custom buttons/cards/fields | Reuse installed Lucide/React/Next dependencies and accessible label/card/disclosure patterns; own CSS to avoid global coupling |
| Backend | FastAPI/Pydantic, APIRouter, module registry | Independent FastAPI app and exported module router using `/api/adjust/` |
| Auth | Public resident routes plus demonstration role headers; static bearer tokens outside demo | No inheritance of demonstration permissions. Loopback-only companion with no record access; production identity needs separate design |
| Database | SQLAlchemy/SQLite, Alembic, persisted cases/evaluation/audit | No connection, model import, migration, employee records or case persistence |
| AI | Deterministic provider with optional compatible endpoint; source-bound behavior | Separate local extraction and authored-option pipeline; optional exact-excerpt extractor behind explicit opt-in, mocked in tests |
| Retrieval | Local lexical retrieval over seeded/synthetic resources | Separate reviewed official guidance catalogue, no synthetic council policy reuse |
| APIs | Next proxies `/api/*` to host API on 8765 | Own Next proxy for `/api/adjust/*` only, independent API on 8766 |
| Testing | pytest, Vitest/Testing Library, Playwright | Own tests/configuration, isolated build folders and browser test servers |
| Launch | Existing one-click macOS/Windows launchers and scripts | Own launchers and helper; existing launchers untouched |
| Bolton Connect | No matching Bolton Connect implementation identified in the inspected source inventory | No host application code changed, including any Connect-related work |

The registry can accept optional routers, but registering ADJUST would require shared imports/configuration and potentially frontend type/registry changes. The brief explicitly withholds shared-file changes. The delivered companion therefore runs independently and provides a reviewable integration manifest rather than modifying the host.

The root `AGENTS.md` asks for ongoing handoff records in the root project log. To respect the user's stricter module-only ownership rule and prohibition on shared-file changes, this implementation maintains `modules/adjust/PROJECT_LOG.md`. The existing shared log is left untouched.

No actual employee data, paid API, provider credentials or production authentication was used. Source editorial review is documented separately; this audit does not establish clinical safety, legal compliance, or programme availability.
