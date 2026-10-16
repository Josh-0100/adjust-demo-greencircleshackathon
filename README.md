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
