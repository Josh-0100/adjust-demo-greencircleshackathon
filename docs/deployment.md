# Launch, configuration, and deployment

## Local launch

Use Node.js 22+ with npm and Python 3.11–3.13. `scripts/setup.sh` chooses an installed compatible Python version; use `CIVICFORGE_PYTHON=/absolute/path/to/python3.13 ./scripts/setup.sh` when the default interpreter is unsuitable. Python 3.14 is outside this project's supported setup range.

From the project root:

```bash
./scripts/start.sh
```

For a browser-opening launch, double-click `Open CIVICFORGE AI.command` on macOS or `Open CIVICFORGE AI.bat` on Windows in the project folder. Both require the runtimes above, prepare missing dependencies, wait for the application, and open the unified landing page `/`. Keep the launcher's terminal open; Ctrl+C stops the servers it started. A second launch opens an already healthy application. The Windows launcher uses `scripts/start_windows.py` and searches for an existing Windows virtual environment, the Python launcher (`py`), or a supported Python on `PATH`; `CIVICFORGE_PYTHON` can select an explicit executable path.

When moving between computers, copy the source without `backend/.venv/` and `frontend/node_modules/` and `modules/adjust/frontend/node_modules/`; these dependencies belong to the computer that installed them. If copying removes macOS executable permissions, run `chmod +x "Open CIVICFORGE AI.command" scripts/*.sh` from the project folder once. First setup requires internet access.

When necessary, the shell launcher invokes `scripts/setup.sh`; the Windows helper prepares the same dependencies directly. Backend packages live in `backend/.venv`, and frontend packages are installed with `npm ci`. Shell setup runs the database bootstrap, and FastAPI startup applies the versioned schema and seeds the initial demo on both platforms. The launchers bind locally, check that their ports are free, wait for API health, and start both the host and isolated Adjust Next.js interfaces. Ctrl+C shuts down the processes they started. Initial package installation requires internet; the installed deterministic demo needs no external AI API.

Default addresses are [localhost:3000](http://localhost:3000) and [API documentation at localhost:8765/docs](http://localhost:8765/docs). Alternate ports can be set in `.env` with `BACKEND_PORT`, `FRONTEND_PORT`, `ADJUST_EMBED_PORT` (default 3002), and a matching `BACKEND_URL`/`CORS_ORIGINS`.

Do not kill an unrelated process occupying a port. Stop the application's own existing terminal session or select free ports. `python3 scripts/health_check.py --url http://127.0.0.1:8765 --wait 20` checks the running API.

## Environment

Copy `.env.example` to `.env` if defaults need changing. Settings are parsed as environment data with dotenv; the launcher does not execute the file as shell code. Never commit it.

| Variable | Default/use |
| --- | --- |
| `DEMO_MODE` | `true`; enables synthetic demo roles and guarded reset. |
| `DATABASE_URL` | Absolute project SQLite path under `data/civicforge.db`. |
| `CHALLENGE_CONFIG_PATH` | Project `config/challenge_config.yaml`. |
| `BACKEND_PORT` / `FRONTEND_PORT` | Local launcher ports, 8765 / 3000. |
| `BACKEND_URL` | Server-side Next.js proxy target; not a browser secret. |
| `CORS_ORIGINS` | Allowed local frontend origins. |
| `STAFF_API_TOKEN` / `ADMIN_API_TOKEN` | Required, distinct, ≥24 characters with demo disabled. |
| `LLM_PROVIDER` | `deterministic`, or `compatible` for the optional JSON adapter. |
| `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY` | Server-only provider settings; configure the approved HTTPS API base. |
| `LLM_TIMEOUT_SECONDS` | 8 seconds; bounded backend timeout. |
| `REQUEST_LIMIT_PER_MINUTE` | 120 requests per process by default. |
| `REQUEST_MAX_BODY_BYTES` | 50,000 bytes by default. |

Paid-provider configuration is optional. Confirm its contract, privacy, cost, JSON response support, and model behavior before use. Missing/failed provider calls must preserve the visible deterministic fallback label. API-shape compatibility is not a verified integration with every provider.

## Database lifecycle

The local database persists across server restarts. Schema bootstrap uses Alembic versioning through:

```bash
cd backend
.venv/bin/python -m app.database.bootstrap
```

For the demo's predictable seed state, start the API and run from the project root:

```bash
python3 scripts/reset_demo.py
```

`scripts/seed_demo.py` delegates to the same guarded reset for a running demo. Reset clears demonstration cases, feedback/evaluation/audit activity, and imported resources and restores the seeded state. It is refused outside demo mode. Preserve any approved demo imports/configuration you need before resetting. Configuration is separate from the database; inspect the implemented reset contract before assuming it restores YAML.

SQLAlchemy supports a future PostgreSQL database URL, and the requirements include its driver. PostgreSQL has not been established as a working deployment by the SQLite checks. Test migrations, seed behavior, constraints, pooling, concurrent access, and backup/restore against the actual PostgreSQL environment before using it.

## Check the project

```bash
./scripts/check.sh
./scripts/check.sh --e2e
```

The first command runs all three backend suites, both TypeScript/unit suites, and isolated production builds for the host (`.next-validation/`) and embedded Adjust (`.next-integrated/`) so an active development server can keep its own build output. `--e2e` also runs Playwright against the running local app. If its browser is not installed, install the required Playwright Chromium browser using the documented frontend test configuration before rerunning. With the launcher running in a separate terminal, `python3 scripts/smoke_test.py` verifies both servers through the frontend proxy and resets synthetic demo state. Record the exact results in `../PROJECT_LOG.md` relative to this document. A written test or successful compile does not prove the live workflow.

## Docker Compose

Dockerfiles and Compose configuration are provided for the three integrated services. They use Python 3.13 and Node 22, non-root users, health checks, loopback-bound host ports, and named volumes for data and configuration.

```bash
docker compose up --build
```

Check `/api/health`, complete `/demo`, reset, restart the containers, and verify persistence. Stop with `docker compose down`; keep the named volumes. Do not add `--volumes` unless you intend to erase that demo state and have preserved anything needed.

The Compose file deliberately configures deterministic demo mode. `.env` provider overrides do not automatically replace explicit Compose `environment` values. Apply and review explicit configuration when changing that behavior. Configuration is retained in a named volume; later image rebuilds may not replace an existing volume's YAML.

Container build/runtime success must be recorded only after execution. Docker was unavailable in the initial local build environment, so supplied configuration alone is not a verified container deployment.

## Pilot and hosted deployment

No cloud deployment is implied. Before hosting, complete [responsible-ai.md](responsible-ai.md): authenticated server-side sessions, HTTPS, managed secrets and database, migrations/backups, request controls, monitoring, operational ownership, source review, and approved data handling. The demo frontend's role headers are not a public-access security model. Host a synthetic demonstration only with appropriate access restrictions; a production pilot requires separate verification and approval by the council.


## Integrated Bolton Connect and Adjust AI

See [the integration report](integration-report.md) for the exact route matrix, identity/data boundaries, validation and limitations. `./scripts/start.sh` now invokes the same cross-platform lifecycle helper as the Windows launcher. It starts three owned processes and leaves standalone Adjust on 3001/8766 unchanged. `ADJUST_EMBED_PORT` defaults to 3002; the helper supplies its `/modules/adjust` base path, embedding flag and API URL. The embedded UI's build directory `.next-civicforge` is separate from standalone `.next`.

The API process composes both complete module apps. Bolton's mode and staff/admin credentials inherit the host; standalone `BOLTON_*` identity settings cannot override them. `BOLTON_DATABASE_PATH` must differ from `DATABASE_URL`. Adjust has no persistence. Back up both SQLite files before deployment, keep them separate and restore both if rolling back. This integration adds no database migration; existing host Alembic bootstrap and Bolton's existing additive setup remain unchanged.

For a production frontend build, supply `BACKEND_URL` and `ADJUST_FRONTEND_URL` at build time (Next rewrites are built into the application). For the embedded Adjust build and runtime use `ADJUST_BASE_PATH=/modules/adjust ADJUST_EMBEDDED=1 ADJUST_BACKEND_URL=<host-api-url>`. Serve only the unified public origin; port3002 remains an internal service. Full exact commands are in the integration report.

The Compose definition includes the module backend sources, separate Bolton data path and isolated Adjust UI service. Docker is unavailable on this machine, so container build/run is unverified. Non-demo APIs enforce common bearer credentials, but the existing browser interfaces lack a real sign-in/session flow; do not deploy this prototype with real council/employee data. No public deployment was performed.
