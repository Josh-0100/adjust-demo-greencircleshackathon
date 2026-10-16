# Working on CIVICFORGE AI

This repository is a reusable civic workflow prototype for a challenge revealed on hackathon day. Read `README.md`, `docs/architecture.md`, `docs/api-contract.md`, and `docs/challenge-adaptation.md` before changing interfaces.

## Continuation record

The workspace handoff record is `PROJECT_LOG.md` in this repository. Update it after every meaningful implementation or validation batch and before ending a session. Include current state, concrete changes, exact commands/results, failures, limitations, and next steps. `docs/build-*.md` retain parallel implementation checkpoints; a planned feature is not evidence of functionality.

## Development

- Preserve a working vertical slice: resident request → attributed evidence → persisted enquiry → staff review → labelled impact.
- Keep challenge-specific models, routes, workflows, evaluators and frontend components in the module registry. Unrelated modules must stay independent.
- Use synthetic data by default. Never invent real council policies, addresses, contacts, eligibility or availability.
- Keep deterministic demo mode operational with no paid provider. Mark synthetic resources, simulated analysis and estimates visibly.
- AI must not approve eligibility, financial support or consequential decisions. Human review and uncertainty must survive provider changes.
- Environment secrets are server-only; `.env` is ignored. Demo role headers are demonstration controls, not production authentication.
- User-authorised reversible implementation, fixes and validation should proceed without repeated permission requests.

## Verification

Use Python 3.11–3.13 and Node 22+. Start locally with `./scripts/start.sh`. Run `./scripts/check.sh`; use `./scripts/check.sh --e2e` for the complete suite once a Playwright browser is installed. `python3 scripts/smoke_test.py` verifies both servers through the frontend proxy and resets synthetic demo records; it refuses non-demo mode.

Never report a test passed unless it ran. Keep remaining deployment/security work honest. Event rules for prebuilt and AI-generated code are not confirmed; see `docs/hackathon-rules.md` and update it if the organiser supplies a policy.
