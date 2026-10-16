# Backend implementation checkpoint

Owner: backend agent. Scope: `backend/`, `config/`, `data/synthetic/`.

2026-10-13: Read the supplied brief and `docs/api-contract.md`. Created configuration, strict schemas, role boundaries, SQLAlchemy models, safe text checks, and atomic YAML persistence. All ten boroughs and six modules are supported. Non-demo mode will require distinct configured staff/admin tokens; demo headers are visibly synthetic boundaries.

Next: plugin implementations, retrieval, provider abstraction, routes, migrations, synthetic seeds, executed API tests.

2026-10-13 milestone 2: Six module plugins, source passage retrieval, rule classification/priority, duplicate suggestions, structured optional provider, role-protected APIs, persisted learning progress and typed custom warm-home assessment are implemented. A real validated read-only ToolRegistry calls retrieval and emits safe audit records. Module evaluation and impact hooks allow a challenge plugin to add custom criteria without core edits. LLM output is accepted only as an exact excerpt from resident input; fabricated policy or source references fall back to deterministic processing.

Environment/install evidence: created `backend/.venv` with `/opt/homebrew/bin/python3.13` (Python 3.13.13). `UV_CACHE_DIR=/private/tmp/civicforge-uv-cache uv pip install --python .venv/bin/python -r requirements.txt` failed sandbox DNS then succeeded with approved network escalation (32 installed packages). No keys are required for the deterministic demo.

Executed `.venv/bin/python -m app.database.bootstrap`: Alembic migration succeeded and seeded 180 labelled fictional resources across all ten boroughs and 8 fictional cases. Initial revision `0001_initial` is portable; `0002_module_evaluation` adds criteria and backfills existing rows.

Executed `.venv/bin/python -m pytest`: **25 passed** in 1.01s. Covers six complete modules, role restrictions, human note resolution, dynamic config, evidence absence, emergencies, duplicates, approved ingestion, prompt injection, malicious structured provider output, outage fallback, learning persistence, custom rules, request sizes/rate limits, observed vs estimated metrics, feedback, repeated reset and non-demo token boundaries. One dependency deprecation warning in Starlette's TestClient/AnyIO alias.

Executed `.venv/bin/python -m app.evaluation.benchmark`: 12 labelled fictional fixtures, 12 correct categories, 12 expected-source checks and 12 grounding checks passed. This tiny hand-written baseline does **not** establish real resident accuracy or deployment performance. Retrieval quality can still be improved; there is no semantic embedding model. Dashboard never presents benchmark scores as live council outcomes.

Remaining verification: rerun after refining weak secondary retrieval matches; root owns live-server smoke, frontend integration and browser tests. Production limitations: prototype shared tokens, per-process rate limits, administrator-attested document approval, no identity-bound resident feedback, lexical injection filter, single-worker migration/bootstrap, and no live council/provider integration tested. PostgreSQL types/migrations are implemented but no PostgreSQL server has run here.
