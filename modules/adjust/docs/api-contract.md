# Independent ADJUST API

Base path `/api/adjust/`, default loopback port 8766. The module's Next.js UI proxies this namespace only. There is no storage API, authentication/session cookie or case identifier. Input/output fields use snake_case. FastAPI's `/docs` exposes the complete generated schema.

| Method/path | Purpose |
|---|---|
| `GET /health` | Module identity, local provider, configuration flag, current passage count, no-persistence flag |
| `GET /knowledge?q=` | Current validated passages; bounded optional topic/publisher search |
| `GET /support` | Four referral-directory entries with verification dates and limitations |
| `GET /scenarios` | Five fictional demonstration situations and expected behaviours |
| `POST /analyse` | Safety gate → extraction → clarification or retrieval → source validation → authored options/conversation/referrals |
| `POST /plan` | Recompute trusted options and build a manager-reviewed discussion draft |

Analysis example:

```json
{
  "description": "A warehouse picker reports back pain and struggles with repeated lifting and picking.",
  "role": "Warehouse picker",
  "constraints": "Small team with limited space.",
  "answers": {},
  "use_ai": false
}
```

`description` is 20–4,000 characters; `role` up to 120; constraints up to 500. Allowed clarification-answer keys: `role`, `tasks`, `barriers`, `constraints`, `employee_view`. Answer role has a 120-character maximum, others 500. Unknown fields are rejected. No employee name is requested or required. `use_ai` defaults false; enabling it requests the optional server-configured provider and falls back safely if unavailable.

Analysis returns `status`, `analysis`, `questions`, `recommendations`, `conversation`, `sources`, `referrals`, `safety`, provider/simulation metadata, `human_review_required: true`, `data_persisted: false`, notices and creation date. Status is one of `ready`, `clarification`, `insufficient_evidence`, `urgent`, `emergency`. Emergency/urgent results omit normal options, conversation and referrals. Clarification results offer no recommendations. An evidence gap can still offer a source-checked general conversation and referral routes, but no invented task-specific option.

Plan example:

```json
{
  "situation": {
    "description": "A warehouse picker reports back pain and struggles with repeated lifting and picking.",
    "role": "Warehouse picker",
    "constraints": "Small team with limited space.",
    "answers": {},
    "use_ai": false
  },
  "selected_ids": ["handling-review"],
  "next_steps": "Proposed: manager and employee to review the task with a competent assessor this week.",
  "review_date": "2026-10-30",
  "human_reviewed": true
}
```

The sample review date must be updated if testing after that date. One to three unique selected IDs are permitted. Next steps must be 5–500 characters, and review date must not be in the past. `human_reviewed` must be true. Plans are rebuilt using local rules/current evidence and do not trust submitted recommendations, citations or a cached result. The response remains labelled `Discussion draft`; manager review does not assert employee agreement.

Errors: 422 for invalid inputs/selections/review; 409 for unsafe, incomplete or insufficiently supported plans; 413 for requests over 16 KB; safe 503 if the service cannot complete a request. Validation responses omit the original input. No errors include provider bodies or credentials. Results have `Cache-Control: no-store`. Request size is bounded even without a Content-Length header.

PDF is a frontend browser print facility, not a separate API endpoint. No plan file is written by the backend.
