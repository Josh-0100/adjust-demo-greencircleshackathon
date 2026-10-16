# Two-sided flow validation — 16 October 2026

Executed on the final two-sided implementation, using fictional inputs only:

| Check | Command / result |
| --- | --- |
| Backend + legacy compatibility | From backend: `../../../backend/.venv/bin/python -m pytest -q` — **99 passed**, one existing Starlette/AnyIO deprecation warning |
| TypeScript | From frontend: `npm run typecheck` — passed |
| Frontend units | `npm test` — **60 passed**: API6, old workspace4, handoff codec40, new workspace4, cost comparison6 |
| Production build | `NEXT_TELEMETRY_DISABLED=1 ADJUST_BUILD_DIR=.next-check npm run build` — passed, root14.7KB / first-load117KB |
| Live browser workflows | `ADJUST_TEST_URL=http://127.0.0.1:3001 ADJUST_BROWSER_CHANNEL=chrome npm run test:e2e` — **8 passed in19.2s** |
| Real PDF output | Chromium confirmed a valid PDF and exactly **one A4 page** for both health and all10 employee/all7 employer needs with health+carer support |
| Launcher restart | New local pair ready on3001/8766; stopped test pair3186/8786. Unix port preflight reuses a recently closed port and still rejects an active listener |

Browser coverage includes both initiating roles, read-only received needs, replacing/removing work needs, no plan before both contributions, original-tab and new-tab return links, invalid/private payload exclusion, absence of local/session storage, stripped hashes, reload clearing, keyboard/mobile reflow, employee/employer crisis stops, private cost figures excluded from network/links/print and erased on leaving the screen, and renewal of a return link whose review date is due.

Tests inspect decoded handoffs for fictional private markers/condition names and inspect actual plan request bodies. Unit coverage includes pending plan completion after pagehide, strict handoff allowlisting, input bounds, source safety and business-size/carer guidance. Both-party flags are demonstration checks; they do not authenticate people or establish real consent.

PDF artifacts (ignored output) are under `frontend/test-results/adjust-employee-starts-rev-8b23b--same-private-one-page-plan-chromium/combined-health-plan.pdf` and `adjust-all-reviewed-needs--128e2-produce-a-real-one-page-PDF-chromium/combined-all-needs-health-and-carer-plan.pdf`. Browser print settings and other engines remain unverified; no accessible-PDF certification.

Failures found and resolved: default Playwright browser build was unavailable, so installed Chrome was selected without downloads; same-path fragment navigation initially failed to reopen a return link and now has a guarded hashchange handler; expired review dates now have an explicit renewal form; two text assertions were corrected to compare textContent consistently and the updated Bolton title. Initial CSS append and a small cleanup command used incorrect relative paths and made no edits; paths were corrected. Initial build CSS support warning was fixed. The launcher originally misidentified TIME_WAIT as an occupied port; Unix SO_REUSEADDR fixes immediate restart while retaining occupied-listener rejection. Native Windows remains untested.

Official guidance was checked against primary pages; no independent legal/clinical validation, clinical safety accuracy claim, live external model call, production identity/access control, deployment or Git push is part of this change. The local rule catalogue can miss or oversimplify needs; people must review it. Copied links/PDFs retain their reviewed information outside the active page.

---

The earlier employer-only validation below is historical evidence for compatibility, not the current two-sided screen set.

# Executed validation — 16 October 2026

Final complete command, from `modules/adjust`:

```sh
ADJUST_BROWSER_CHANNEL=chrome python3 scripts/check.py --e2e
```

**Exit 0.** The helper reused the supported Python 3.13.13 environment and installed Node v26 runtime/dependencies; it built ADJUST only, launched separate test servers on 3186/8786, executed browser scenarios, and shut those test servers down.

| Check | Result |
|---|---|
| Independent backend pytest | 53 passed; one existing Starlette/AnyIO deprecation warning |
| TypeScript | Passed |
| Frontend Vitest/Testing Library | 10 passed |
| Independent production Next build | Passed; root page 14.6 KB, first load 116 KB |
| Playwright with installed official Chrome | 7 passed in 12.8 seconds |
| Browser PDF | Valid PDF header, exactly one A4 page for the full three-option warehouse draft |
| Desktop/mobile screenshots | Visually inspected; no clipping or horizontal overflow in tested views |
| Colour contrast samples | All seven sampled text/background pairs exceed 4.5:1 |
| `git diff --check` | Passed for tracked working-tree changes |

Backend tests cover extraction, five demo scenarios, clarification completion, explicit negation, constraints, evidence gaps, exact URL/publisher validation, expired/future/pending/withdrawn sources, metadata, optional AI mocks and fallback, no default model network call, crisis override, crisis content in answers, human review, plan tampering, review dates, long barrier excerpts, API validation, request-body limits, safe errors and absence of storage files/endpoints.

Frontend tests cover bounded/labelled input, focus, reset, default model opt-out, API namespace, no-store requests, safe validation/proxy/network/timeout errors, preservation of entered text after failure, and unavailable-service messaging without fabricated evidence counts.

Browser workflows cover the landing/library/search, warehouse → options → conversation → support → reviewed plan → PDF, clarification, evidence gaps, crisis stopping normal results, keyboard skip/focus, 390-pixel mobile layout, reload privacy and the three-option selection limit. All use fictional descriptions. The exported example is `frontend/test-results/adjust-plan.pdf`; screenshots are in the same ignored directory.

Actual reused frontend packages: Next 15.5.27, React/React DOM 19.3.0, TypeScript 5.9.3, Vitest 3.2.7, Playwright 1.64.0 and Lucide 0.468.0. No packages were changed in the host frontend.

## Failures found and resolved

- The first backend-test invocation used an incorrect relative executable path; the corrected command ran successfully.
- AbortError handling relied on a cross-realm Error instance check. Replaced it with a safe name check; timeout test now passes.
- Corrected a unit-test value matcher and selector ambiguities caused by the responsive resource links, duplicate support controls and Next's hidden route announcer. These were test harness issues, not user-facing source failures.
- Playwright's expected Chromium revision 1248 was not cached. Reused installed official Chrome using the documented environment switch; no new browser was downloaded.
- Direct loopback startup was restricted by the command sandbox. Approved local execution started the independent servers and test servers successfully.
- Added explicit negative-mention handling and marked bounded barrier excerpts in the one-page plan; final backend tests cover both.

## Isolation and limits

No existing frontend/backend application source, registry, configuration, host launcher or database file was edited by ADJUST. A pre-implementation SHA-256 inventory was compared after implementation. All original application files matched. The shared `PROJECT_LOG.md` changed externally during the session to record a public preview; it was not edited or reverted by this implementation. Existing uncommitted changes were preserved.

The original application's build/test suite was not rerun: the user explicitly prohibited rebuilding the existing frontend/backend, and this implementation is isolated. The module-owned check exercises only ADJUST.

No live model, paid API, production identity provider, actual employee data, independent legal/clinical review, native Windows run, screen-reader audit, browser zoom audit or cross-browser/PDF accessibility certification was performed. Source freshness checks and passing prototype fixtures do not establish real-world legal accuracy, clinical safety or service availability. Content maintenance and qualified review remain necessary before any live use.
