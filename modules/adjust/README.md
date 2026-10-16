# ADJUST — Bolton Workplace Adjustments Assistant

An independent CIVICFORGE AI module for small employers. Describe work barriers, clarify missing context, explore sourced discussion options, prepare an employee conversation, find official support and print a one-page discussion draft.

**Local hackathon prototype.** Default analysis is deterministic and visibly labelled simulated. Guidance has received an editorial source check, not independent clinical or legal validation. No model service, account, payment or database is needed.

## Open ADJUST

Double-click **Open ADJUST.command** on macOS or **Open ADJUST.bat** on Windows, inside this folder. Or run:

```sh
cd modules/adjust
python3 scripts/start.py
```

The employer UI opens at **http://127.0.0.1:3001**. Its independent FastAPI API is at **http://127.0.0.1:8766/docs**, under `/api/adjust/`. Keep the terminal open; Ctrl+C stops only the processes started by this launcher. A second launch reuses an existing healthy ADJUST pair.

Prerequisites: Node.js 22+ and Python 3.11–3.13. The launcher uses the existing project's installed runtimes when present. On macOS it creates a module-owned `frontend/node_modules` symlink to reuse the installed packages, without editing them. If dependencies are absent, it installs an independent environment inside ADJUST; first installation needs network access. Windows installs its own frontend packages. The launch helper itself can run under a newer Python while selecting a supported backend runtime. Native Windows execution has not been validated on this Mac.

Use `python3 scripts/start.py --setup-only` for setup, or `--no-open` to start without opening a browser. `ADJUST_PYTHON`, `ADJUST_API_PORT` and `ADJUST_UI_PORT` override runtime/ports. Everything binds to loopback. The module does not read the host application's `.env`, database or configuration.

## What works

- All seven employer screens: overview, situation, clarification, options, conversation, support and plan; plus searchable guidance library.
- Bounded role/task/barrier extraction, reported limitations, constraints and missing information. It never determines diagnosis, legal disability or medical fitness.
- 32 curated passages with exact official URL, publisher, section locator, owner role, editorial review date, expiry and verification status.
- Authored options for handling tasks, desk work, work pressure, communication, environment, fatigue and mobility. Each option includes steps, employee questions, citations, limitations and referral guidance.
- Source validation checks exact URL/publisher pairs, status, review dates and required metadata. Missing or expired evidence fails closed. Retrieval is local and never follows submitted URLs.
- Employee-led conversation wording, written agreement prompts and follow-up.
- Acas, occupational health, Access to Work and a cautious WorkWell Bolton route. The original local funding notice ended in March 2026; current availability is explicitly unconfirmed despite a published local referral page.
- Human-reviewed discussion draft with one to three options, next steps, review date and source list. **Print / save PDF** uses the browser's print dialog and “Save as PDF”; there is no server-side PDF renderer or hidden export service. The automated Chromium test verifies the standard three-option draft fits one A4 page. Very long user text or browser print settings may require more pages; barrier excerpts are marked.
- Five built-in fictional examples, including vague input and a specialist evidence gap.

## Privacy and safety

Inputs/results live in process/browser memory only. There are no case tables, storage endpoints, localStorage, sessionStorage, cookies, analytics or employee identifiers. Uvicorn access logging is disabled by the launcher. API errors omit submitted input. Responses use `Cache-Control: no-store`. Clearing the session or reloading removes the current draft. This does not control browser extensions, operating-system memory, crash reporting or files a manager exports.

Explicit crisis/immediate-danger phrases stop the adjustment workflow before optional AI or recommendations and show NHS emergency/urgent routes. These conservative phrase checks are **not clinical triage** and can miss paraphrases or flag historical descriptions. Emergency guidance is also visible on the situation screen. Do not rely on ADJUST to decide whether a situation is safe.

No adjustment is automatically implemented. Plan generation requires a manager's review, reanalyses the situation against the current library and rejects fabricated selections, missing evidence, past review dates and unsafe content. Manager review is not employee agreement or professional approval. Do not delay appropriate risk assessment or employer responsibilities while seeking funding.

No shared host files, registry entries, database schema or Bolton Connect code are changed. See the [repository audit](docs/repository-audit.md) and [integration manifest](integration-manifest.json). Linking or mounting the module inside the host is a separate shared-file change for the owner to review.

## Optional AI extraction

Default operation does not contact another AI. To deliberately enable a compatible extraction endpoint, set the server-only `ADJUST_AI_BASE_URL`, `ADJUST_AI_MODEL` and `ADJUST_AI_API_KEY` environment variables described in `.env.example`. The launcher does not load that file automatically; export the variables in your shell. Never use `NEXT_PUBLIC_*` for secrets.

The UI offers a per-request opt-in only when configured. Enabling it transmits the situation to that provider; use fictional data unless an appropriate handling arrangement exists. The model can only supply exact input excerpts for missing fields. Invalid schema, fabricated excerpts, prohibited claims, timeouts and provider errors return the deterministic fallback. A model cannot generate recommendations, citations or decisions. Source-bound options remain authored local rules. No live external model call was used to build or test this module. Model tests use mocks.

## Checks

From this folder:

```sh
python3 scripts/check.py
```

Runs the independent backend suite, TypeScript, frontend unit tests and a separate production build. It does not rebuild the existing CIVICFORGE frontend/backend. For browser scenarios and PDF export:

```sh
# First time, if a Playwright browser is not installed:
cd frontend
npx playwright install chromium
cd ..
python3 scripts/check.py --e2e

# Or use an already-installed Chrome browser:
ADJUST_BROWSER_CHANNEL=chrome python3 scripts/check.py --e2e
```

The end-to-end runner starts independent test servers on 3186/8786 with their own build folder and stops them afterwards. Set `ADJUST_TEST_URL=http://127.0.0.1:3001` to exercise an already-running ADJUST instance instead. Reports, screenshots and the example PDF appear under `frontend/test-results/` and contain fictional data only. See [validation results](docs/validation.md) for executed checks and limitations.

## Module map

```text
backend/adjust_api/   isolated app, schemas, safety, extraction, providers, retrieval, options and plan
backend/tests/        deterministic source, AI mock, API, safety and plan tests
frontend/            independent Next.js / React / TypeScript employer workspace
knowledge/           reviewed source catalogue and verification record
scripts/             independent launcher and validation runner
docs/                audit, accessibility and validation records
integration-manifest.json
```

Before any live pilot: appoint an accountable named human content reviewer, obtain qualified guidance review, assess data handling and identity/access needs, improve semantic extraction and safety evaluation, conduct assistive-technology testing and establish source maintenance. ADJUST does not claim legal compliance or measured real-world accuracy.
