# Bolton Connect

AI-assisted employment and community support for residents of **Bolton, Greater
Manchester** — delivered as a self-contained CivicForge module.

A resident describes their situation in their own words. Bolton Connect turns
that into a structured understanding, matches it against a grounded directory of
Bolton support services, suggests employment and training routes, and produces a
plain-English action plan to talk through **with a human adviser**. A separate
council adviser view lists shared cases for review.

> This is a decision-support prototype. It never decides whether someone is fit
> for work, never confirms entitlement to any benefit or service, and never
> presents demonstration vacancies as live. Every plan is explicitly framed as
> something to review with a person.

---

## Isolation contract

This module is built to run and be developed **independently** of the rest of the
repository, including the parallel *Adjust* module:

- **Own API namespace** — every route is under `/api/bolton-connect`.
- **Own settings namespace** — every environment variable is prefixed `BOLTON_`.
- **Own data store** — a module-local SQLite database (`data/bolton_connect.db`)
  owning only its four tables (`sessions`, `consent_events`, `cases`,
  `case_notes`). It registers nothing with any host ORM.
- **No dependency on the Adjust module** — nothing here imports it, and the
  integration adapter declares `depends_on_adjust_module: False`.
- **No automatic edits to shared entry points** — any change the host app would
  need is *documented* in [`INTEGRATION.md`](./INTEGRATION.md), never applied.

Everything (frontend, backend, prompts, schemas, tests, data, docs) lives inside
`modules/bolton-connect/`.

---

## Running it

The module reuses the repo's backend virtualenv if present, otherwise it creates
its own and installs this module's dependencies:

```bash
cd modules/bolton-connect
./scripts/run.sh
```

Then open:

- Resident portal — <http://127.0.0.1:8099/>
- Adviser view — <http://127.0.0.1:8099/adviser.html>

Host/port are overridable with `BOLTON_HOST` / `BOLTON_PORT`. On first run in demo
mode, six clearly-labelled **synthetic** cases (scenarios A–F) are seeded so the
adviser view is populated immediately.

Run the standalone server by hand instead of the script:

```bash
cd modules/bolton-connect/backend
uvicorn bolton_api.app:app --host 127.0.0.1 --port 8099
```

---

## The pipeline

```
resident text ─▶ assess ─▶ match ─▶ pathways ─▶ action plan
                  │          │          │            │
            structured   grounded   demonstration  10-section
            understanding services   routes        plan + provenance
```

1. **Assess** (`assessment.py`) — a deterministic engine extracts employment
   status, experience, skills, goals, practical barriers, support needs,
   training interests and preferences into a validated `ResidentAssessment`. If
   there is too little to act on, it asks a single clarifying question instead of
   guessing. An optional vendor-neutral LLM can refine this; its output is
   re-screened and always has a safe deterministic fallback.
2. **Match** (`matching.py`) — hybrid AI + deterministic matching against the
   directory. Each service gets a state of `ELIGIBLE`, `POTENTIALLY_ELIGIBLE`,
   `NOT_ELIGIBLE` or `UNKNOWN` with reasons and missing-information notes. These
   are **indications to discuss**, never entitlement decisions.
3. **Pathways** (`pathways.py`) — employment and training exploration by target
   sector. Vacancies are **demonstration examples only**. A health condition or
   disability is explicitly never treated as a barrier to exploring a route.
4. **Action plan** (`action_plan.py`) — a ten-section plan where every item is
   tagged with its provenance so verified facts are visually distinct from AI
   suggestions.

---

## Safety and ethics model

| Guarantee | How it is enforced |
|---|---|
| No medical diagnosis / fitness-for-work judgement | Barriers are recorded only as practical limitations in the resident's own phrasing; no diagnosis is inferred. |
| No invented services, contacts or eligibility | The directory is grounded in official sources; contact details are exposed only for `verified` services (`public_contact()`). |
| Time-limited / closed programmes never auto-recommended | `auto_recommendable` requires an active, `verified`/`source_listed` service; historical/expired/unverified entries are withheld and caveated even when a resident matches them. |
| Demonstration vacancies never shown as live | Every `Opportunity` is `status="demonstration"` with a disclaimer and no employer. |
| Verified facts vs AI suggestions | Every plan item carries a `provenance` label (`verified`, `official_source`, `ai_suggestion`, `resident_stated`, `synthetic_demo`). |
| Save / resume only with explicit consent | Sessions persist only on `consent_save`/`consent_share`; every consent decision is written to an audit trail. |
| Right to erase | `DELETE /sessions/{id}` cascades to any case and notes derived from it. |
| De-identified analytics | The adviser summary uses counts only; case summaries omit the resident's name and raw free text. |
| Role-based access | Adviser/admin endpoints require the `staff` role (demo `X-Demo-Role` header, or a bearer token outside demo mode). |
| Input safety | Resident text is screened for embedded instructions (prompt injection) and control characters at the schema boundary; oversized bodies and request floods are rejected by middleware. |

---

## Configuration

All variables use the `BOLTON_` prefix (see `settings.py`). Defaults are safe for
an offline demo.

| Variable | Default | Purpose |
|---|---|---|
| `BOLTON_DEMO_MODE` | `true` | Enables demo role header + synthetic seeding. |
| `BOLTON_LLM_PROVIDER` | `deterministic` | `deterministic` (no network/key) or `compatible` (any OpenAI-compatible JSON endpoint). |
| `BOLTON_LLM_BASE_URL` / `BOLTON_LLM_API_KEY` / `BOLTON_LLM_MODEL` | empty | Used only when provider is `compatible`. The key is never logged or returned. |
| `BOLTON_DATABASE_PATH` | `data/bolton_connect.db` | Module-local SQLite store. |
| `BOLTON_ADVISER_API_TOKEN` / `BOLTON_ADMIN_API_TOKEN` | empty | Bearer tokens for staff/admin outside demo mode. |

The LLM is **optional and vendor-neutral**. With the default deterministic
provider the module needs no API key and makes no network calls.

---

## Testing

```bash
cd modules/bolton-connect
../../backend/.venv/bin/python -m pytest tests/ -v
```

`tests/test_scenarios.py` covers the six required demonstration scenarios; and
`tests/test_api_and_safety.py` covers consent-gated persistence, role-based
access, de-identified aggregates, the right to erase, demonstration-only
vacancies, verification-gated contacts, and rejection of prompt-injection and
oversized payloads.

### Demonstration scenarios (A–F)

| # | Persona | What it demonstrates |
|---|---|---|
| A | Lost a warehouse job, bad back, wants to return to work | A clear case with a practical limitation (not a diagnosis). |
| B | "Not sure where to start" | Too little information — asks a clarifying question rather than guessing. |
| C | Retail worker wanting to retrain into IT | Career change; local digital-skills routes and face-to-face preference. |
| D | Returning carer who has lost confidence | "Lost confidence" is **not** read as job loss; stays economically inactive. |
| E | Health condition, in work, wants adjustments | Workplace-adjustment support; health never used to exclude. |
| F | Young UC claimant asking about a closed scheme | A matched-but-closed programme is never auto-recommended. |

Personas are synthetic and live in `data/demo_residents.json`.

---

## Project structure

```
modules/bolton-connect/
├── backend/bolton_api/      FastAPI app, pipeline, persistence, auth, plugin
├── frontend/                Build-free resident portal + adviser view
├── data/                    Grounded support directory + synthetic personas
├── prompts/                 Assessment system prompt (for the optional LLM)
├── tests/                   Scenario A–F + API/safety tests
├── scripts/run.sh           Standalone launcher
├── README.md                This file
└── INTEGRATION.md           Documented (not applied) host-integration steps
```
