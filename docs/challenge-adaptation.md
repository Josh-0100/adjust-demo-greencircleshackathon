# Adapt to the borough challenge

Keep a complete vertical slice: resident request → grounded recommendation → persisted case → staff review → measured outcome. Activate only the modules needed for the actual problem. The prepared repository's competition use is subject to [the organiser's rules](hackathon-rules.md).

## 1. Capture the problem before editing

Record the borough, problem owner's account of the current process, target users, desired outcomes, constraints, permitted data, and what success would look like in a short pilot. Ask the challenge owner which actions require staff approval. Use fictional examples until data permission and handling are clear.

| Problem shape | Starting module | Demonstration value |
| --- | --- | --- |
| Finding a council service | `service-navigator` | Evidence-backed signposting and a next step. |
| Employment or local recruitment | `employment` | Explainable skill overlap and gaps. |
| Discovering community support | `community` | Resource discovery with borough filtering. |
| Repetitive enquiries and routing | `triage` | Classification, duplicate suggestion, and review queue. |
| Retraining and course pathways | `learning` | Course recommendations and recorded learning progress. |
| A different domain or process | `custom` or a new module | Its own inputs, workflow, API, evaluation, and impact. |

The `custom` example supports a cold-home assessment. Treat it as an extension pattern; do not reframe an unrelated challenge to fit it.

## 2. Update configuration

Edit `config/challenge_config.yaml` or use the administrator page. Preserve the expected shape and valid borough/module IDs:

```yaml
challenge:
  borough: "Salford"
  title: "A clear challenge-specific title"
  description: "One sentence explaining the intended value."
  problem_statement: "The challenge owner's concrete problem."
  target_users: ["Residents", "Council staff"]
  desired_outcomes: ["A measurable task becomes easier"]
  selected_modules: ["triage"]
  success_metrics: ["Correct route on an approved test set"]
  constraints: ["Synthetic data", "Human review before action"]
  data_sources: ["Fictional demo resources"]
  demo_scenario: "A named fictional person completes one useful task."
  human_review_required: true
```

Keep other top-level settings such as `escalation_threshold` when present. Configuration controls branding, challenge context, available modules, and demo framing. A metric label in configuration is a goal; add collection/evaluation code to make it a measured result.

## 3. Add an isolated module

Backend extension points are `backend/app/modules/base.py` and `backend/app/modules/registry.py`. Each `CivicModule` exposes a descriptor, resource-module mapping, classification and recommendation behavior, and can expose an optional `APIRouter`. Copy the implemented `backend/app/modules/custom.py` example and use the actual signatures in the base class.

Give the new module a stable ID. Register it in one place, activate it in configuration, and add relevant resources. Keep domain rules inside its module. Common source validation, role boundaries, audit, and case persistence should remain in the shared core.

The implemented backend interface is:

```python
class CivicModule:
    # UI metadata: id, name, description, icon, input_hint, example_prompt,
    # capabilities, workflow_steps; resource_modules maps stored catalogues.
    router = None  # optional FastAPI APIRouter

    def descriptor(self, enabled: bool): ...
    def classify(self, message: str) -> Classification: ...
    def recommend(self, message: str, resources: list[tuple[Resource, float]]) -> list[Recommendation]: ...
    def explain(self, message: str) -> str: ...
    def evaluate(self, message: str, analysis: Analysis) -> list[EvaluationCriterion]: ...
    def impact_metrics(self, cases: list, evaluations: list) -> list[ModuleImpactMetric]: ...
```

The registry stores instances in `MODULES`; `register_module(instance)` rejects duplicate IDs. Register before `create_app()` mounts optional routers. `EvaluationCriterion` has `key`, `passed`, and `detail`. `ModuleImpactMetric` has `key`, `label`, `value`, `unit`, `kind`, and `description`. See the warm-home module for a concrete evaluator/collector.

| Extension | Where to implement | Integration requirement |
| --- | --- | --- |
| Typed inputs | Pydantic models in the new module or a module-owned schema file | Bounded fields, explicit validation, no hidden eligibility decisions. |
| Persistent data | SQLAlchemy models in the module's own file | Import before metadata creation and add an Alembic migration for schema changes. |
| Workflow | `CivicModule` classification/recommendation methods and module-owned helpers | Return structured output with evidence, uncertainty, and review state. |
| Specialized endpoint | Optional module `router` | Use shared authorization/session helpers; preserve input and output validation. |
| Evaluator | Override `evaluate(message: str, analysis: Analysis)` | Return `list[EvaluationCriterion]`; shared case creation persists the criteria. |
| Impact collector | Override `impact_metrics(cases: list, evaluations: list)` | Return `list[ModuleImpactMetric]` with explicit evidence kind and description. |
| Frontend experience | `frontend/components/module-registry.tsx` and a module-owned component | Key by module ID; share the case/evidence/review envelope. |

The registry is the boundary for independent plugins. Shared case creation and impact reporting already invoke evaluator and collector hooks generically. Runtime safeguard criteria must not be described as classification or retrieval accuracy. Use a separate labelled fixture for those benchmarks. Do not encode a new domain's rules as special cases in common orchestration or dashboards.

## 4. Add models, workflows, and routes

The working custom example provides `POST /api/custom/assess`, returning `{assessment, case}`. Its assessment inputs are domain-specific, while its case uses the common `Case → Analysis` contract. Keep that pattern when a challenge needs more than a text enquiry: validate the domain input, calculate a transparent assessment, create/reuse the case through the shared path, and attach staff review.

For learning, the staff-facing `GET` and `POST /api/learning/progress/{case_id}` demonstrate a module-owned persistent workflow. New tables need reversible Alembic migrations under `backend/alembic/versions/`. Do not assume that `create_all()` migrates an existing table. After adding and reviewing the migration, run:

```bash
cd backend
.venv/bin/python -m app.database.bootstrap
```

Return to the project root before using the launcher or check scripts.

Consequential actions should create a suggestion or pending review step. They must not autonomously approve, reject, allocate, or determine eligibility for a public service.

## 5. Adapt the frontend

Inspect `frontend/components/module-registry.tsx` for `frontendModuleRegistry`. Each entry supplies `icon`, `shortName`, and optional `InputComponent`, `ResultComponent`, and `submit` hooks. `submit` adapts domain input to its endpoint and returns the shared `Case`; `ResultComponent` receives `{item: Case}`. Add a dedicated component when the domain needs structured fields, comparison, a plan, or progress. Use `frontend/lib/types.ts` and `frontend/lib/api.ts` for typed contracts and API calls. Keep `frontend/components/analysis-panel.tsx` for citations, provider identity, uncertainty, and review messaging.

The initial `ModuleId` type enumerates the six built-ins, and the input hook uses the custom home-assessment type. Replacing `custom` can replace its input type and component together. An additional module ID requires extending `ModuleId` and adding its registry entry; a different structured input should introduce a typed per-module adapter rather than reuse home fields. Keep its data-to-API conversion in its own plugin and retain the existing modules.

Use clear task language, keyboard-operable controls, labelled fields, visible loading/error states, and useful empty states. Keep synthetic/demo labels prominent. A service or resource card should explain what the user can do next and whether the underlying source is fictional or verified. Do not merely rename the chat prompt and call it a new workflow.

## 6. Connect approved data

Use the administrator's bounded text ingestion through `POST /api/documents`. Supply title, content, borough, module ID, source label, source URL when appropriate, `synthetic`, and `approved`. Approval is an explicit application flag, not independent verification of policy.

Have the challenge owner confirm the source's content, scope, currency, and permission. Keep provenance and passages. Mark fictional sources `synthetic: true`. Never invent contact details, real service availability, or eligibility. Ingestion accepts text; it does not fetch submitted URLs or parse arbitrary uploaded files. Add other ingestion formats only with size/type limits and a documented review path.

## 7. Create evaluation evidence

Write a small labelled fixture with a representative positive case, ambiguous case, out-of-scope case, insufficient evidence, prompt injection, and a sensitive request requiring review. For matching, include known required skills and expected gaps. Record expected classifications, relevant resource IDs, and human-review requirements.

Use backend tests for workflow invariants and API boundaries, component tests for domain inputs/results, and Playwright for the complete task plus reset. When reporting accuracy, state the fixture size and that it is a prototype test. Do not infer real-world accuracy from deterministic examples. Estimated staff savings should expose the assumed manual baseline and review effort.

## 8. Prepare the demonstration

Pick one fictional resident, one plausible task, two or three useful sources, and an actionable result. Seed deterministically, use the default provider, walk the same flow twice, reset, and verify the initial state returns. Include a request that produces insufficient evidence or review so safeguards are visible.

Adapt `/demo` to explain the actual problem, resident action, staff workflow, evidence, outcome type, and pilot next step. Follow [demo-guide.md](demo-guide.md) for live and backup paths.

## 9. Recover while preserving work

If a provider fails, use `LLM_PROVIDER=deterministic` and restart. If a new module fails, deactivate its ID in configuration while fixing it. If the seed state becomes inconsistent, use the guarded demo reset; do not delete the database. If credits end, resume from `../PROJECT_LOG.md` and this directory's build logs. Record modified files, commands that actually ran, failure output, and the next concrete action after each meaningful change.

## 10. Verify the final prototype

```bash
./scripts/check.sh --e2e
python3 scripts/health_check.py
python3 scripts/smoke_test.py
```

Run `./scripts/start.sh` in a separate terminal before health/smoke checks. The smoke check uses and resets synthetic demo records. Execute the real task in the browser on desktop and mobile widths; verify disabled modules, evidence, review notes, reset, unavailable provider fallback, error recovery, and honest impact labels. Capture actual execution results in the project log. Container deployment and PostgreSQL require their own verification; a local test does not establish either.

## Prompt 1 — implement the revealed challenge

Paste this into the coding agent and replace the bracketed fields:

```text
Continue CIVICFORGE AI in this repository. First read PROJECT_LOG.md
from the project root, README.md, docs/api-contract.md, docs/architecture.md,
docs/challenge-adaptation.md, and docs/hackathon-rules.md. Inspect actual code
and the latest checks. Preserve working behavior and update the shared log
after each meaningful step so another agent can resume without credits.

Borough: [BOROUGH]
Problem statement from the council representative: [PROBLEM]
Target users: [USERS]
Desired outcomes and testable success criteria: [OUTCOMES]
Constraints, permissions, permitted prebuilt code, and data: [CONSTRAINTS]
Approved source content with provenance, or synthetic-only: [SOURCES]

Implement one complete, challenge-specific resident-to-staff workflow.
Select relevant modules; use an isolated new registry plugin when this is a
different problem. Support its typed data, workflow, frontend component,
optional API routes, labelled evaluator, and honest impact metrics. Update
challenge_config.yaml, approved/synthetic resources, and /demo. Preserve
human review for consequential actions, citations, uncertainty, role
boundaries, and a visibly simulated deterministic fallback. Never invent
council policy, contacts, availability, integrations, or measured results.
Run appropriate tests and the live flow, fix failures, and record exact
commands/results, limitations, and remaining work. Implement now.
```

## Prompt 2 — validate, repair, and prepare the pitch

```text
Continue the challenge implementation from PROJECT_LOG.md at the project
root and docs/ build logs. Read actual source and the agreed challenge.
Run ./scripts/check.sh --e2e, start the app, and verify a resident request,
grounded result, staff review, impact labels, and repeatable /demo reset.
Test insufficient evidence, malformed input, unauthorized staff/admin
access, provider unavailability, keyboard use, mobile layout, and error
recovery. Fix regressions and rerun only affected checks, then the required
final suite. Record failures as well as successes; claim no unexecuted test.

Prepare one reliable three-minute live demo and a deterministic backup.
Update docs/demo-guide.md and docs/pitch-guide.md for the actual borough,
problem, evidence, safeguards, prototype results, and realistic pilot ask.
Keep operational estimates separate from observed activity and test results.
Confirm the organiser's prebuilt/AI-code rules from recorded evidence;
leave compliance unconfirmed if no answer exists. Finish the working
prototype and handoff log, not just a plan. No external messages unless
the user explicitly authorizes them.
```
