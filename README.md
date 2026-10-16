# Adjust demo

Practical help for Bolton's small employers to keep people with health conditions in work. Built for the Build for Greater Manchester hackathon (Bolton challenge).

A manager describes a staff member's situation in plain words. Adjust returns:

- sourced adjustment ideas from Acas, HSE and GOV.UK guidance
- a script for the conversation and next steps
- Access to Work help, including the employer cost share for the business size
- matching schemes such as Statutory Sick Pay, WorkWell Bolton and Disability Confident
- a one-page summary, with a plain-language copy for the employee

## How it works

This is a single static page (`index.html`) with no build step and no backend. Nothing typed into it is stored.

In this demo, descriptions are read with keyword matching. In the full build an AI model would do that step. Scheme eligibility and cost shares always come from fixed rules.

## Deploying

Import the repo into Vercel with the framework preset set to **Other**. There is no build command and the output directory is the repo root.

## Status

Prototype. Not an official council service, and not medical or legal advice. Scheme details last checked 16 October 2026.

## Full-stack ADJUST implementation

The independent workplace adjustments assistant is included in [`modules/adjust/`](modules/adjust/README.md). It includes a Next.js employer interface, FastAPI endpoints, 32 source-linked guidance passages, clarification and recommendation workflows, employee conversation guidance, referral information, a reviewed discussion-plan/PDF print flow, tests and integration documentation.

Run from the repository root with Node.js 22+ and Python 3.11–3.13 installed:

```sh
python3 modules/adjust/scripts/start.py
```

The UI starts at `http://127.0.0.1:3001`, with its independent API on `http://127.0.0.1:8766`. Default analysis uses local rules, with no model service or database required. The launcher prepares module dependencies when needed; first setup requires internet access.

See the [integration handoff](modules/adjust/INTEGRATION_HANDOFF.md), [API contract](modules/adjust/docs/api-contract.md) and [executed validation](modules/adjust/docs/validation.md). The last implementation check passed 53 backend, 10 frontend and 7 browser tests, TypeScript and a production build. Content has an editorial source check; independent professional review remains outstanding.

The root `index.html` remains the original static demo. The full-stack module runs separately and needs a running Python API; the existing Vercel static-site configuration does not deploy that backend.
