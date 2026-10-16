# ADJUST — better work, together

A fictional Bolton workplace demo for **employees and employers**. Either person can start. Each describes their side privately, reviews a plain-language list of work needs, and invites the other person. A single sourced conversation plan is created only after both reviewed contributions are present.

## Run locally

Double-click **Open ADJUST.command** (macOS) or **Open ADJUST.bat** (Windows), or run:

```sh
python3 scripts/start.py
```

UI: **http://127.0.0.1:3001**. API: **http://127.0.0.1:8766/docs**. Node 22+ and Python 3.11–3.13 are required. The launcher prepares independent dependencies or reuses installed runtimes, binds to loopback and opens the UI. Ctrl+C stops its own processes. Native Windows execution is not validated on this Mac.

The previously published [public demo](https://adjust-workplace-assistant.vercel.app) is the earlier employer-only release until these changes are separately deployed. This implementation does not publish or push changes automatically.

## The two-sided flow

1. Choose **I’m an employee** or **I’m an employer**.
2. Describe the situation using fictional details. Employees can optionally select unpaid caring responsibilities or both. Employers add business size, role requirements, practical constraints and previous attempts.
3. A conservative safety check runs over all description fields. Possible crisis stops the flow and shows NHS 111, Samaritans 116 123 and 999.
4. Review suggested work needs. Replace each statement using the dropdown, remove any item or add another. The fixed work-language catalogue prevents condition names and original text entering a link. This is bounded local matching, not a generative model; review is essential.
5. Confirm what to share and copy an invitation link. The recipient sees read-only reviewed needs, adds their own side and reviews it.
6. Both contributions produce a plan with no-cost changes to agree, sourced options, a conversation agenda, support and a future review date. The second person sends a **return link** so the starter can open the same plan. There is no saved room, automatic update or waiting-case service.
7. Print or save as a one-page A4 PDF through the browser. An exported file is outside ADJUST.

The employer-only cost comparison uses blank-by-default, employer-entered figures for adjustment costs, confirmed Access to Work funding, recruitment, vacancy cover, training, ramp-up and optional legal risk. It shows totals without an employment recommendation. Legal risk left blank is unquantified, not zero. A stated budget shortfall points to Acas and a fair process. Its fixed notice explains adjustment duties and uncapped discrimination compensation. Figures never enter links, APIs or the plan and clear on leaving that screen.

## Privacy and demo limits

There is no database, account, case identifier, cookie, browser storage, analytics or default external AI call. API requests/responses are not saved by this application. Original words exist transiently in browser/server memory for the suggestion step and are cleared from the UI after review or a safety stop. Only reviewed **canonical work-need IDs**, support category, business size and review date can enter the handoff. No free text is accepted in the combined-plan request.

Links put these reviewed selections in a URL fragment, which is not sent with the page request. The UI removes the fragment from its current address immediately after capturing it. Closing/reloading, clearing the session or leaving the page clears its in-memory draft, including browser back/forward-cache state. **Copied invitation/return links and exported PDFs cannot be recalled**. Anyone holding a link can read its reviewed selections; share it privately. There is no identity verification and neither checkbox proves actual agreement. Use fictional data only. Hosting infrastructure, extensions and exported files are outside these application-level claims.

Local phrase checks are not clinical triage and can miss or overflag a crisis. Official support routes remain visible before submission. ADJUST does not diagnose, determine legal disability, decide eligibility or funding, or approve changes. Both people must discuss practicality, safety and agreement.

## Sources and rights

[Official guidance checked 16 October 2026](knowledge/two-sided-guidance.md) records exact primary URLs and qualifications. Carer plans include the day-one right to **request** flexible working, qualifying unpaid Carer’s Leave, Bolton Council’s carer’s assessment and a Carer’s Allowance eligibility/benefits check. Caring alone does not create the disability reasonable-adjustment duty.

Access to Work is not automatic funding and does not pay for adjustments an employer is legally required to make. The plan shows business-size cost-sharing guidance from DWP’s staff guide with confirmation required: public official sources contain differences in wording. The private calculator deducts only a confirmed amount entered by the employer. WorkWell Bolton’s original funding ended in March 2026; current availability must be confirmed.

The legacy extraction, optional AI adapter, 32-passage validated source catalogue and employer API remain available for compatibility. The current two-sided UI always uses authored local rules and the new stateless `/api/adjust/case/*` endpoints. The new guidance is editorially checked and is not independent legal or clinical validation.

## Validation and files

```sh
python3 scripts/check.py
ADJUST_BROWSER_CHANNEL=chrome python3 scripts/check.py --e2e
```

The complete runner checks this module only. Browser tests start an isolated UI/API pair; they use fictional inputs and inspect real PDF output. See [executed results](docs/validation.md) and [current log](PROJECT_LOG.md), including limitations. A Playwright Chromium installation or supported Chrome is needed for E2E.

- `backend/adjust_api/cases.py`: strict two-sided API, safety, canonical needs and sourced plan.
- `frontend/components/two-sided-workspace.tsx`: both routes, review, handoff and privacy lifecycle.
- `frontend/components/combined-plan.tsx`: shared printable plan.
- `frontend/components/cost-comparison.tsx`: employer-private calculator.
- `frontend/lib/case-api.ts`: strict handoff allowlist and API types.
- `knowledge/two-sided-guidance.md`: official checks and qualifications.
- `docs/api-contract.md`: current and compatibility API contracts.

Unrelated CIVICFORGE and Bolton Connect application code is unchanged. Shared-host integration and publishing are separate work.
