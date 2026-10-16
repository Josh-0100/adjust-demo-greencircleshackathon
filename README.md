# Adjust AI

Adjust AI brings practical workplace conversations, resident support and adviser review into one local prototype. People can describe what they need, review sourced suggestions and choose their next steps. Human review and explicit consent remain part of the existing workflows.

Synthetic demo data and a deterministic AI provider are the defaults. No paid API is needed for the demonstration. The application is a prototype with authentication boundaries prepared for replacement by a real identity provider; it is not approved for live council data or production use.

If a coding session ends, resume from the continuously maintained [PROJECT_LOG.md](PROJECT_LOG.md). It records the working state, commands actually run, failed checks, limitations, and the next actions.

## Run locally

For one-click launch, open this project folder and double-click the file for your computer:

- **macOS:** `Open CIVICFORGE AI.command`
- **Windows:** `Open CIVICFORGE AI.bat`

Install Node.js 22+ (including npm) and Python 3.11–3.13 first. The launchers install missing project dependencies, start the application, and open the demo in your default browser after it is ready. Keep the terminal window open while using the application; press Ctrl+C to stop it. Double-clicking again opens the existing healthy application. The first setup requires internet access.

Keep each launcher inside this project folder, alongside `frontend/`, `backend/`, and `scripts/`. When copying the project to another computer, omit `frontend/node_modules/` and `backend/.venv/` so dependencies are installed for that computer. On macOS, if the executable permission was lost while copying, run `chmod +x "Open CIVICFORGE AI.command" scripts/*.sh` once from this directory.

From this directory:

```bash
./scripts/start.sh
```

The launcher prepares dependencies and the demo database when needed, then starts the frontend at [localhost:3000](http://localhost:3000) and the API at [localhost:8765](http://localhost:8765). Start at [the unified landing page](http://localhost:3000/). Keep the terminal open; Ctrl+C stops the processes. Initial dependency installation needs internet access. Once dependencies are installed, the deterministic demonstration runs locally without an AI service.

For separate setup and checks:

```bash
./scripts/setup.sh
./scripts/check.sh
python3 scripts/health_check.py
```

Copy `.env.example` to `.env` only when you need to override the supplied defaults. Configure paid providers in the backend environment. API credentials must never be placed in a `NEXT_PUBLIC_*` variable or committed.

## What to demonstrate

| Area | Meaningful workflow |
| --- | --- |
| Public portal | Select an enabled module, describe a need, inspect evidence and next steps, and record feedback. |
| Council operations | Inspect persisted cases, filter the queue, add a human review note, and update the case status. |
| Intelligence workspace | Analyse a request, inspect classification, retrieval, uncertainty, and escalation. |
| Impact dashboard | Inspect case activity, processing measurements, and explicitly labelled estimates. |
| Administrator | Change borough/challenge settings, activate modules, import approved text, and review audit events. |
| Demo | Walk through resident input, grounded result, staff perspective, outcomes, and safeguards; reset for the next run. |

Every resource shown in the supplied dataset is fictional and visibly labelled. The demonstration does not establish real service availability, council policy, eligibility, or realised savings.

## Adapt on the day

Edit `config/challenge_config.yaml` or use administrator configuration. Choose modules that fit the challenge: `service-navigator`, `employment`, `community`, `triage`, `learning`, or `custom`. A new problem can introduce its own models, routes, frontend components, evaluators, and impact metrics through the module registry.

[Challenge adaptation](docs/challenge-adaptation.md) contains the integration points and two paste-ready prompts. Keep the original request → evidence → review → measurement workflow working while adapting it.

## Project map

```text
frontend/      Next.js, TypeScript, Tailwind, reusable UI, browser tests
backend/       FastAPI, Pydantic, SQLAlchemy, retrieval, AI providers, modules
config/        Challenge settings and active module configuration
data/          Fictional records for the local demonstration
scripts/       Setup, launch, checks, seed, health, and reset
docs/          Architecture, adaptation, demo, risks, deployment, and pitch
```

## Integrated modules

The landing page follows the supplied practical-help reference: describe a situation, choose Employee or Business, and continue into the existing assessment. The Adjust logo sits at the left of the header and Talk to an advisor opens existing workplace advice links at the right. Resident Support, Workplace Adjustments and Council Dashboard remain available from the menu button on desktop or mobile. The original portal remains at [/portal](http://localhost:3000/portal); operations, intelligence, impact, configuration and the guided demo retain their routes.

The integrated launcher runs the host UI on 3000, the complete host/module APIs on 8765, and an isolated Adjust interface on loopback 3002. Standalone module launchers remain available. Resident save/share consent and Adjust reviewed handoffs remain separate; navigation never transfers resident data into a workplace conversation. The supplied Adjust logo and PowerPoint palette now brand all three interfaces and printable plans; see [branding sources and colours](docs/branding.md).

See [the integration report](docs/integration-report.md) for conflicts, changed files, executed tests, limitations and deployment steps.

The frontend sends `/api/*` requests through Next.js to FastAPI. SQLite holds the local demonstration data. SQLAlchemy isolates the database layer for a future PostgreSQL deployment; changing database engines also requires migrations and verification.

## Guides and evidence

- [Architecture](docs/architecture.md) and [API contract](docs/api-contract.md)
- [Challenge adaptation](docs/challenge-adaptation.md)
- [Repeatable demonstration and recovery](docs/demo-guide.md)
- [Responsible AI and production gaps](docs/responsible-ai.md)
- [Local and container deployment](docs/deployment.md)
- [Pitch outline and pilot plan](docs/pitch-guide.md)
- [Hackathon rules research](docs/hackathon-rules.md)
- [Executed test results](docs/test-results.md)

Test commands alone are not evidence of passing tests. Check the latest recorded execution results in the shared [project log](PROJECT_LOG.md); retain failed and blocked checks as well as successful ones. Continue work from that log if coding-agent credits run out. Per-area build logs under `docs/` provide additional context.

With both servers running, `python3 scripts/smoke_test.py` verifies the resident → evidence → review → impact flow through the frontend API proxy and resets the synthetic dataset. It changes demo activity and refuses non-demo mode.

## Event status

The confirmed event is [Green Circles Manchester | AI Hackathon | Supported by Barclays](https://www.eventbrite.co.uk/e/green-circles-manchester-ai-hackathon-supported-by-barclays-tickets-1996447720876), on Friday 16 October 2026. The checked public listings do not resolve whether prebuilt application code, existing frameworks, or AI-generated code are permitted. This repository must not be represented as competition-compliant until the organiser confirms those rules. See [the research record](docs/hackathon-rules.md).
