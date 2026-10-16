# Pitch and pilot

Make the pitch about the borough's task and the working workflow. The reusable foundation is preparation; the challenge-specific result and evidence should lead. Follow [the organiser's disclosure rules](hackathon-rules.md) once confirmed.

## Three-minute script template

**Problem — 25 seconds.** “For [target user] in [borough], completing [task] currently involves [specific friction confirmed by the council representative]. This causes [observed problem or a clearly stated hypothesis]. Our prototype helps the user [concrete outcome].”

**Demonstration — 85 seconds.** Show the fictional resident's request, evidence-linked recommendations and next step. Then show the same case in the staff queue, its review flag, and a human note/status update. Say which sources are synthetic and which behavior is simulated. If the challenge needs structured inputs, demonstrate the domain component instead of a generic conversation.

**Evidence and safeguards — 35 seconds.** “We observed [actual prototype count/time] in this run. On [number] labelled test examples we measured [actual executed result]. We estimate [saving] only under [manual baseline/review assumptions]. Staff retain the decision, and missing evidence prompts review.” Omit any number without a recorded method and result.

**Feasibility and ask — 35 seconds.** “We propose a [small duration/scope] staff-assisted pilot with [problem owner], [approved source set], and [success criteria]. We need [data/operational sponsor/test participants]. We will measure [task completion, routing quality, review effort, user feedback], and stop or adjust if [failure condition].”

## Show honest value

| Claim | Suitable evidence | Avoid |
| --- | --- | --- |
| Easier service discovery | An end-to-end task with relevant cited resources and user testing | Calling fictional records official services. |
| Better triage | A labelled classification/routing fixture plus review outcomes | Turning a heuristic score into accuracy. |
| Time saved | Measured process time and an explicit manual baseline including review | Presenting dashboard estimates as council savings. |
| Good recommendations | A labelled relevance test and feedback sample size | Claiming job, course, or support eligibility. |
| Reliable demonstration | Executed checks, live walkthrough, repeatable reset and fallback | Claiming deployment from a Dockerfile. |
| Responsible use | Visible uncertainty, source metadata, staff decisions, and documented gaps | Claiming production-grade security or compliance. |

Metric categories are **observed**, **prototype test**, **estimated**, and **simulated**. Observed synthetic activity is evidence about this prototype, not a real-world outcome.

## Practical operational model

Begin with one borough team, one narrowly defined task, and a maintained approved source set. Staff review consequential cases. Name the source owner, escalation owner, support owner, and reviewer of evaluation results. Compare the pilot with the current manual process, including the additional review work.

Viability depends on the measured reduction in task effort or improved discovery, the cost of maintaining sources, staff oversight, integration, hosting, and optional model calls. Do not invent revenue, council procurement commitments, or unit economics. The local deterministic mode demonstrates the workflow; a model's cost and benefit need measurement when an approved provider is introduced.

## Likely questions

- **Why use AI?** Explain the particular language or matching task it improves. Describe the rule-based parts honestly and say that the default live demonstration is simulated.
- **What if the answer is wrong?** Show citations, uncertainty, insufficient-evidence behavior, and the human review queue. A staff decision remains necessary.
- **What have you measured?** Refer to recorded tests and this demo's activity. Show assumptions beside estimates and state fixture sizes.
- **Can the council deploy it tomorrow?** It is a local prototype. Identity, security/data review, source ownership, accessibility, operational support, and pilot evaluation are required.
- **How is it reusable?** Show validated challenge configuration and one registry module that owns typed input, workflow, routes, evaluation, and impact. Other boroughs can reuse the core while retaining their domain rules.
- **What was built before today?** Disclose the prepared foundation and the actual challenge-day additions according to the confirmed event conditions.

Before presenting, replace template fields with the actual challenge, rehearse the three-minute flow twice, verify reset, keep a deterministic backup ready, and update `../PROJECT_LOG.md` with the exact working scenario and remaining limitations.
