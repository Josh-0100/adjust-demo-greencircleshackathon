# Repeatable demonstration

Use synthetic data and `LLM_PROVIDER=deterministic` for the repeatable live flow. The result is intentionally marked simulated. Adapt the challenge framing after the borough briefing; do not claim a real council service or actual resident outcome.

## Prepare

1. Start with `./scripts/start.sh` in one terminal and check `python3 scripts/health_check.py` in another.
2. Open [the demo route](http://localhost:3000/demo). Confirm borough, challenge, and active module match the story you will tell.
3. Reset with **Reset demonstration** or `python3 scripts/reset_demo.py`. Reset removes demo activity and imports and restores deterministic records. Save any data needed first.
4. Run the scenario twice, including staff review and reset. Keep the launcher terminal available for diagnostics.
5. Keep source excerpts, review flags, provider label, and impact categories visible. Do not show secrets or real personal data on the projector.

## A three-minute flow

| Time | Action | What to explain |
| --- | --- | --- |
| 0:00–0:25 | Show the problem and fictional resident | Describe a specific task and why the current process is difficult. |
| 0:25–1:10 | Submit the resident request | Use an enabled module; show useful next steps, evidence, and uncertainty. |
| 1:10–1:50 | Open council operations | Find the new persisted case, inspect category/priority/review, add a human note, and change status. |
| 1:50–2:20 | Show impact | Explain which activity was observed in the prototype and which savings are estimates. |
| 2:20–2:45 | Show safeguards | Display synthetic sources, human review, simulation/provider label, and an insufficient-evidence example. |
| 2:45–3:00 | Make the pilot ask | Name the problem owner, approved dataset, test method, and next small pilot. |

Use `/demo` for the guided path and the regular portal, operations, intelligence, impact, and administration pages to show the same underlying workflow. The demonstration is not a separate canned integration: show the case created by your submission.

On `/demo`, click **Meet the resident**, then **Run resident scenario**, inspect the evidence, choose **Review with staff**, and **Resolve with review note**. The page shows observed before/after case and resolution counts, then **Run it again** resets the dataset. It uses the configured demo scenario and the first enabled module in challenge configuration. For a different challenge, place the intended module first and write the scenario as a resident utterance. The portal's custom module exposes the structured home inputs.

## Example resident requests

Choose a module that is enabled in configuration. These examples describe fictional scenarios, not official services:

- **Council service navigator:** “I have moved into the borough and need help finding information about council tax and waste collections. What should I do next?”
- **Employment:** “I have customer service and spreadsheet skills and want to explore local entry-level office roles and training.”
- **Community:** “I would like a local community group where I can volunteer and help people use computers.”
- **Triage:** “There is a damaged street light on my road. Can this enquiry be directed to the right team?”
- **Learning:** “I want to retrain in digital administration. I can use email and basic spreadsheets but need a structured course pathway.”
- **Custom:** “My flat feels cold and I am worried about energy bills. I want to understand sensible next steps.” Use the home assessment fields to show a structured domain workflow.

Keep recommendations grounded in what is actually seeded for the selected borough. If no source matches, use the result to demonstrate that the system requests review instead of inventing an answer. The exact displayed result may change with configuration, dataset, and code; practise against the delivered build.

## Staff and administrator actions

The operations page exposes the persisted queue. Open the submitted case, inspect its evidence and escalation reason, add a concrete review note, and resolve it only after review. Explain that this status is an internal task indicator. It does not approve eligibility or make an external council decision.

Use intelligence to expose retrieval, workflow steps, duplicate suggestions, and confidence. Confidence and matching scores are heuristic. Use administration to show module/borough changes, approved text ingestion, and audit summaries. Demo-mode roles allow these actions locally; they are not real user authentication.

## Reset and reproducibility

**Reset demonstration** invokes the administrator-guarded `POST /api/demo/reset`. Its CLI equivalent is:

```bash
python3 scripts/reset_demo.py --url http://127.0.0.1:8765
```

Confirm the success response and reload the queue/impact view. Check that the initial seeded case count returns; do not assume the count is zero. Submit the same request again and verify the same resource/routing behavior. Timestamps, generated references, and measured processing time may differ. Reset clears imported resources and user activity. Challenge YAML should be reviewed separately.

## Backup and recovery

| Failure | Recovery |
| --- | --- |
| AI provider timeout, quota, or malformed response | Keep the returned simulated fallback label visible; set `LLM_PROVIDER=deterministic` and restart if needed. |
| No internet | Use the already-installed deterministic local build. Fresh dependency or browser installation still needs network access. |
| Backend unavailable | Check launcher output and `health_check.py`; restart the launcher. Frontend error states should explain retry. |
| Port occupied | Stop the application's previous launch or use free ports; do not kill another app blindly. |
| Missing evidence | Say that the source could not be verified; show staff review or choose an approved seeded example. |
| New module regression | Deactivate the module while fixing it; preserve the working shared flow. |
| Demo data changed | Save needed imports, use guarded reset, and repeat the scenario. |
| Total live environment failure | Present a previously captured recording/screenshots labelled as recorded prototype evidence, if you prepared them. Do not pretend they are live. |

Prepare the recording yourself only after the actual workflow works. No recording or deployment is supplied merely by this guide. The shared project log is the authoritative record of checks that ran and known blockers.
