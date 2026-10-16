# Vercel deployment

The repository contains two experiences: the original static root `index.html` and the independent full-stack ADJUST module. To deploy the full module, set the Vercel project root to **`modules/adjust`**, not the repository root.

The module's `vercel.json` uses **Vercel Services (beta)**. One service builds `frontend/` as Next.js; the second serves the existing FastAPI app through `api/index.py`. Public `/api/adjust/*` requests reach Python first, and other requests reach Next.js. No localhost backend URL or external model key is needed for the hosted demonstration.

The API service explicitly includes the backend package and reviewed knowledge JSON, and excludes frontend files/tests/docs from its function bundle. The module-level `pyproject.toml` selects a supported Python version and pins runtime dependencies. This does not alter local launch behaviour or the host CIVICFORGE application.

## Verified production deployment — 16 October 2026

- Public app: [adjust-workplace-assistant.vercel.app](https://adjust-workplace-assistant.vercel.app).
- Project: `adjust-workplace-assistant` (`prj_neD81fL2lytCSQ6SK8oyGECVUGbz`), team `amalviy311-3822s-projects`.
- Deployment: `dpl_8F56PAe9eBXXgZCm4CUswifx41Rv`, production state **READY**. Published source commit: `73dbc785ea9d0f8e4568a7b7523596ec3268610c` on GitHub `main`.
- Public `/api/adjust/health` returned HTTP 200 with `provider=local-rules`, `knowledge_entries=32`, `data_persisted=false` and `ai_configured=false`.
- `ADJUST_TEST_URL=https://adjust-workplace-assistant.vercel.app ADJUST_BROWSER_CHANNEL=chrome npm run test:e2e` passed **7/7** workflows in 20.4 seconds, including a one-page A4 draft PDF, clarification, evidence gaps, emergency stop, keyboard/mobile flow and the three-option limit. Only fictional inputs were used.
- The account has no GitHub Login Connection yet. The API and CLI both rejected Git linking with HTTP 400; a retry after the user's acknowledgement returned the same result. The current production deployment was uploaded through the authenticated CLI. Automatic builds on GitHub pushes are **not connected**. In Vercel account settings, connect GitHub under Authentication / Login Connections, using an account with access to `Josh-0100/adjust-demo-greencircleshackathon`; then run `vercel git connect https://github.com/Josh-0100/adjust-demo-greencircleshackathon.git --yes --scope amalviy311-3822s-projects`. Set the Git project's root directory to `modules/adjust` before a repository-triggered build.

## Git-linked project

Use the repository `Josh-0100/adjust-demo-greencircleshackathon`, production branch `main`, and root directory `modules/adjust`. Keep project build settings automatic so the two services use their respective frameworks. No database, paid provider, secret, domain purchase or plan upgrade is required for the default demonstration.

Use Vercel CLI 64.3.1 or newer for the current Services configuration. For CLI deployment after linking the correct project/team:

```sh
cd modules/adjust
vercel deploy --prod --yes --scope amalviy311-3822s-projects
```

Verify the returned deployment URL and `/api/adjust/health`, then run the module's browser workflows against that URL. The owner explicitly requested this production deployment. Global Vercel agent setup does not itself require creating a project; this project is created for the explicitly requested ADJUST deployment.

## Checks after deployment

- Homepage loads the ADJUST workspace.
- `/api/adjust/health` reports module `adjust`, 32 current passages and no persistence.
- Warehouse input returns source-supported options; vague input requires clarification.
- Specialist evidence gaps produce no invented recommendation.
- Crisis inputs stop the ordinary workflow.
- Human-reviewed plans and browser PDF printing work over the same public origin.

The local source/validation limitations still apply. This is a prototype, with editorial source checks and qualified content review pending. Vercel hosting does not establish legal or clinical validation.

## Agent setup reference

Followed [Vercel's setup playbook](https://vercel.com/get-started.md): verify/install CLI, use the installed Vercel plugin guidance, and configure the shared user-wide `https://mcp.vercel.com` endpoint through Codex. OAuth is completed by the user. Vercel CLI was updated to 64.3.1 and authenticated as `amalviy311-3822`. The Vercel plugin was already installed. Codex registered `vercel` in the shared user configuration and completed OAuth; documentation search and authenticated team listing both succeeded. No reload was needed. Do not commit `.vercel/` or credentials.

Official references: [Services](https://vercel.com/docs/services), [routing](https://vercel.com/docs/services/routing), [service configuration](https://vercel.com/docs/services/config-reference), [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi).
