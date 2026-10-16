# Responsible AI and security

CIVICFORGE AI is a synthetic-data prototype. It supports staff decisions through evidence and review. It must never independently approve, reject, or determine eligibility for a public service. A resolved case is a staff workflow status, not a benefits or entitlement decision.

## Safeguards in the design

| Boundary | Behavior | Limit |
| --- | --- | --- |
| Input | Pydantic field validation, bounded requests, module/borough checks | Valid input can still be false, biased, or harmful. |
| Retrieval | Stored passages and source metadata, explicit synthetic label | A recorded source URL does not prove current policy or availability. |
| Generation | Optional provider supplies an exact resident-text extract with validated source IDs; facts/recommendations remain deterministic | Heuristic confidence is not a calibrated measure of correctness. |
| Evidence | Citations tied to retrieved resources, insufficient-evidence messaging | Lexical search can miss relevant evidence. |
| Review | Sensitive or uncertain recommendations escalated; human note before resolution | Human oversight requires trained staff and a defined process. |
| Ingestion | Bounded approved text, HTTP(S) source URL validation, injection screening | Pattern screening is defense in depth, not complete prompt-injection prevention. |
| Roles | Resident/staff/admin dependencies at API boundaries | Demo headers do not authenticate a person. |
| Rendering | Text rendering of resident input and generated output | Future rich content must be sanitised and tested. |
| Activity | Audit summaries, processing measurements, explicit simulation labels | Local logs are not a production monitoring or tamper-proof audit service. |
| Request limits | Per-process request rate/body bounds | Reverse-proxy controls and multi-instance limits are still needed. |

Inspect backend security/safety tests and the latest test log to see what was actually exercised. No production-grade security claim follows from this table.

## Identity and secret handling

`DEMO_MODE=true` accepts `X-Demo-Role: resident|staff|admin`; the frontend supplies demo roles for its prototype screens. Anyone able to call the API can select these headers. Use this only with synthetic information on trusted local access.

Non-demo operation uses distinct `STAFF_API_TOKEN` and `ADMIN_API_TOKEN` values with at least 24 characters. Token validation creates an API boundary, but static shared tokens are not a complete council identity system. The frontend requires an authenticated server-side session layer before non-demo use. Add an approved identity provider, verified role claims, session expiry/revocation, and audited authorization checks before a pilot.

Keep `LLM_API_KEY`, API tokens, and database credentials in the backend environment or a managed secret store. Do not put them in frontend code, `NEXT_PUBLIC_*` variables, source control, screenshots, or logs. The supplied `.env.example` has no credentials. Rotate any real secret accidentally exposed.

## Data and evidence policy

All supplied records are fictional. They are not official council services and must remain labelled. Do not enter real resident identifiers, health information, benefits records, or safeguarding information into the demonstration. Imported non-synthetic material needs documented approval, provenance, currency, and permission. The `approved` field records an operator assertion rather than validating those facts.

The prototype performs no autonomous action against a council system. Its tool-style operations are bounded application functions. Untrusted source text should be treated as evidence, never as an instruction to override safeguards or disclose configuration. Display the source used, distinguish source content from inference, and say when information cannot be verified.

If an external model is configured, review its data handling before sending permitted information. Record the provider, model, request scope, retention requirements, location, contract, and fallback policy with the council's security/data teams. Do not treat an OpenAI-compatible API shape as a guarantee of privacy, residency, or suitability.

## Impact honesty

Every metric has a category:

- **Observed:** a count or duration collected in this running prototype, including activity over synthetic cases.
- **Prototype test:** a result from an executed, described test set or named runtime invariant checks with a known size and method. Runtime safeguard checks do not measure accuracy.
- **Estimated:** a calculation based on stated assumptions such as manual handling time and required review.
- **Simulated:** a fabricated demonstration value or deterministic demonstration behavior.

Observed demo case counts do not establish outcomes for real residents. Resolution indicators reflect staff updates. Matching scores express rule-based overlap; they do not establish hiring suitability. The demo rating average includes fictional seeded feedback as disclosed by its metric description; live prototype feedback also needs a response count. Neither establishes resident satisfaction. Savings exclude unmodelled integration, staff training, oversight, procurement, and infrastructure costs unless explicitly included.

## Before a real council pilot

Agree the scope and ownership with the council. Complete the council's security, data-protection, procurement, and accessibility reviews; establish permitted data, retention/deletion, lawful processing, and any assessment required for the use case. This document is an engineering checklist, not a legal determination.

The pilot needs verified authentication, least-privilege authorization, HTTPS, secrets management, managed migrations, encrypted backups with restore tests, monitoring, incident handling, and a defined staff review/escalation process. Benchmark retrieval and classification on a representative approved test set; assess language, disability, demographic, and access barriers. Check recommendations for unequal effects. Provide an appeal/correction route and a usable non-digital alternative where the service needs one.

Accessibility needs keyboard and screen-reader testing, meaningful focus and labels, contrast checks in both themes, readable language, zoom/reflow, mobile task completion, and testing with users. Passing prototype browser tests is not an accessibility certification.

Maintain a review date for source content, a model-change log, regression fixtures, and a named operational owner. Release first into a constrained staff-assistance pilot with measurable stop conditions. Real resident benefit and operational savings must be measured during that pilot.
