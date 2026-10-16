# Vercel deployment

The repository contains two experiences: the original static root `index.html` and the independent full-stack ADJUST module. To deploy the full module, set the Vercel project root to **`modules/adjust`**, not the repository root.

The module's `vercel.json` uses **Vercel Services (beta)**. One service builds `frontend/` as Next.js; the second serves the existing FastAPI app through `api/index.py`. Public `/api/adjust/*` requests reach Python first, and other requests reach Next.js. No localhost backend URL or external model key is needed for the hosted demonstration.

The API service explicitly includes the backend package and reviewed knowledge JSON, and excludes frontend files/tests/docs from its function bundle. The module-level `pyproject.toml` selects a supported Python version and pins runtime dependencies. This does not alter local launch behaviour or the host CIVICFORGE application.

## Git-linked project

Use the repository `Josh-0100/adjust-demo-greencircleshackathon`, production branch `main`, and root directory `modules/adjust`. Keep project build settings automatic so the two services use their respective frameworks. No database, paid provider, secret, domain purchase or plan upgrade is required for the default demonstration.

For CLI deployment after linking the correct project/team:

```sh
cd modules/adjust
vercel deploy
```

Use the returned preview URL to verify the UI and `/api/adjust/health`, then run the module's browser workflows against that URL. Promote or deploy production only within the owner's deployment request. Global Vercel agent setup does not itself require creating a project; this project is created for the explicitly requested ADJUST deployment.

## Checks after deployment

- Homepage loads the ADJUST workspace.
- `/api/adjust/health` reports module `adjust`, 32 current passages and no persistence.
- Warehouse input returns source-supported options; vague input requires clarification.
- Specialist evidence gaps produce no invented recommendation.
- Crisis inputs stop the ordinary workflow.
- Human-reviewed plans and browser PDF printing work over the same public origin.

The local source/validation limitations still apply. This is a prototype, with editorial source checks and qualified content review pending. Vercel hosting does not establish legal or clinical validation.

## Agent setup reference

Followed [Vercel's setup playbook](https://vercel.com/get-started.md): verify/install CLI, use the installed Vercel plugin guidance, and configure the shared user-wide `https://mcp.vercel.com` endpoint through Codex. OAuth is completed by the user. Documentation search and authenticated team listing verify the connection. Do not commit `.vercel/` or credentials.

Official references: [Services](https://vercel.com/docs/services), [routing](https://vercel.com/docs/services/routing), [service configuration](https://vercel.com/docs/services/config-reference), [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi).
