# API contract (implementation agreement)

Base: `/api` (Next.js proxies to FastAPI). JSON keys snake_case. Errors use FastAPI `detail`; all user output rendered as text. Demo mode headers: `X-Demo-Role: resident|staff|admin`. Demo mode is synthetic, explicit and not production authentication. Staff endpoints accept admin. Frontend uses admin for configuration/reset only, staff for operations/intelligence/impact; public endpoints do not need headers.

`GET /api/health`: `{status, demo_mode, provider}`.

`GET /api/config`: `{challenge: {borough, title, description, problem_statement, target_users, desired_outcomes, selected_modules, success_metrics, constraints, data_sources, demo_scenario, human_review_required}, demo_mode, boroughs: string[], escalation_threshold: number}`.

`PUT /api/config` (admin): body `{challenge: {...complete challenge fields}, escalation_threshold: number}`. Persist validated YAML + return GET shape. Validates borough/modules; reloads on next request, no code edit required.

`GET /api/modules`: `{modules: [{id, name, description, icon, enabled, input_hint, example_prompt, capabilities: string[], workflow_steps: string[]}]}`. IDs: `service-navigator`, `employment`, `community`, `triage`, `learning`, `custom`.

`GET /api/resources?module_id=&q=&borough=`: `{resources: Resource[]}`.
Resource: `{id: number, title, category, module_id, borough, description, content, source_label, source_url: string|null, synthetic: boolean, skills: string[], next_steps: string[]}`. Metadata and passages must be retained, including an honest synthetic label. Public demo resources never purport to be official council services.

`POST /api/enquiries`: `{message: string, module_id: string, borough?: string, resident_name?: string}` → complete Case. Reject disabled modules. Result includes persisted case + retrieved sources + review outcome.

Case: `{id: number, reference, resident_name, message, module_id, borough, category, priority: low|normal|high|urgent, status: new|in_review|resolved, department, created_at: ISO string, updated_at: ISO string, review_note: string|null, analysis: Analysis}`.

Analysis: `{summary, intent, confidence: number (0..1), needs_human_review: boolean, escalation_reason: string|null, recommendations: [{title, description, next_steps: string[], match_score: number|null, skills_gap: string[]}], sources: [{resource_id: number, title, excerpt, source_label, source_url: string|null, synthetic: boolean}], safety_notes: string[], workflow_steps: [{name, status: complete|review|warning, detail}], provider, simulated: boolean, processing_ms: number, duplicate_of: number|null}`.

`GET /api/cases?status=&module_id=` (staff) → `{cases: Case[]}`.
`GET /api/cases/{id}` (staff) → Case.
`PATCH /api/cases/{id}` (staff): `{status: in_review|resolved, review_note: string}` → Case. Must require human note for resolution; no automatic eligibility decisions.

`POST /api/workspace/analyse` (staff): same input/response as POST enquiries, persisted and audited.

`GET /api/impact` (staff): `{metrics: [{key, label, value: number, unit, kind: observed|prototype_test|estimated|simulated, description}], trend: [{label, enquiries: number, resolved: number}], categories: [{label, count: number}], total_cases: number, review_count: number, resolved_count: number, provider, demo_mode: boolean}`. Runtime counts observed within synthetic demo; estimates explicitly distinguish operational assumptions. No fabricated test accuracy.

`GET /api/audit` (admin): `{events: [{id, action, actor, entity, created_at, detail}]}` (safe summaries, no secrets).

`POST /api/documents` (admin): `{title, content, borough, module_id, source_label, source_url?: string|null, synthetic: boolean, approved: boolean}` → Resource. Bounded text ingestion, explicit approval, valid http(s) URL only, prompt injection rejection, source metadata stored. No untrusted URL fetch.

`POST /api/demo/reset` (admin): clear demo cases/evaluation/audit/imports; seed deterministic synthetic records; returns `{status: "reset", case_count: number}`. Forbidden when demo disabled.

`POST /api/cases/{id}/feedback` (public): `{rating: 1..5}` → `{status: "recorded"}`. Rating contributes to observed demo satisfaction.

Custom registry: each backend module exposes descriptor, resource mapping, classify and recommend behavior and optional APIRouter registration; frontend keyed component map can specialize custom inputs/results. Include implemented custom example workflow, not an empty placeholder.
