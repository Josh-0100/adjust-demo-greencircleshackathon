# Source verification — 16 October 2026

`catalogue.json` contains 32 short editorial paraphrases from 17 exact official pages. Every passage records topic, official URL, publisher, source section, applicable scenarios, review date, expiry, status and a named editorial **role**. `catalogue.py` is the authoring record used to create this JSON; runtime reads JSON only. Changes to the JSON must be reviewed alongside the authoring record if retained.

**Content owner role:** ADJUST prototype content maintainer. A specific accountable human and an independent qualified reviewer have not been appointed. `verified` means the source page was inspected and the paraphrase tied to a section. It does not certify legal interpretation, medical suitability or continuing availability. Do not present this as independent professional validation.

## Pages inspected

| Publisher | Exact source | Sections used |
|---|---|---|
| Acas | [Reasonable adjustments](https://www.acas.org.uk/reasonable-adjustments) | What reasonable means; examples |
| Acas | [Making and handling requests](https://www.acas.org.uk/reasonable-adjustments/asking-for-reasonable-adjustments) | Handling requests; deciding on adjustments |
| Acas | [Having a meeting](https://www.acas.org.uk/reasonable-adjustments/having-a-meeting) | Working together; preparing |
| Acas | [Reviewing and keeping a record](https://www.acas.org.uk/reasonable-adjustments/reviewing-reasonable-adjustments-and-keeping-a-record) | Review; adjustment passports |
| Acas | [Mental health adjustments](https://www.acas.org.uk/reasonable-adjustments/mental-health-adjustments) | Hours; workload; communication; environment |
| Acas | [Occupational health](https://www.acas.org.uk/using-occupational-health-at-work) | Uses; permission before contacting a doctor |
| HSE | [Manual handling overview](https://www.hse.gov.uk/msd/manual-handling/index.htm) | Risk hierarchy; no universal legal weight limit |
| HSE | [Avoid handling](https://www.hse.gov.uk/msd/manual-handling/avoid-hazardous-manual-handling.htm) | Redesign; mechanical aids |
| HSE | [Assess handling](https://www.hse.gov.uk/msd/manual-handling/assess-manual-handling.htm) | Whole task; workforce consultation |
| HSE | [Reduce injury risk](https://www.hse.gov.uk/msd/manual-handling/reduce-risk-injury.htm) | Loads; layout; pace |
| HSE | [DSE assessments](https://www.hse.gov.uk/msd/dse/assessment.htm) | Workstation; assessor review |
| HSE | [Stress Management Standards](https://www.hse.gov.uk/stress/standards/overview.htm) | Work design; joint discussion |
| GOV.UK | [Employer adjustment guidance](https://www.gov.uk/reasonable-adjustments-for-disabled-workers) | General duty guidance; adviser route |
| GOV.UK | [Access to Work](https://www.gov.uk/access-to-work) | Support overview |
| GOV.UK | [Eligibility](https://www.gov.uk/access-to-work/eligibility) | Current criteria; diagnosis not required to apply |
| GOV.UK | [Application route](https://www.gov.uk/access-to-work/apply) | Online, telephone, accessible formats |
| NHS | [Urgent mental health help](https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/) | 111/urgent GP; 999/A&E when life is at risk or safety cannot be maintained |

The NHS page's own next-review date was April 2026. It remained accessible when checked; its core emergency signposting is used, with clinical review outstanding. The runtime editorial review expires on 14 January 2027. A source that is pending, withdrawn, future-dated, expired, missing ownership/locator, or mismatched against the exact publisher/URL allowlist cannot support a recommendation.

## Referral-specific checks

- [Acas contact page](https://www.acas.org.uk/contact): official guidance/helpline entry point. No operating hours, callback times or individual outcomes promised.
- [WorkWell Bolton](https://letskeepboltonmoving.co.uk/education-employment/workwell/): published local description and referral form inspected. [Bolton NHS directory](https://www.boltonft.nhs.uk/community-directory/lets-keep-bolton-moving/) identifies Let's Keep Bolton Moving as a Bolton Council service.
- [Bolton Council launch notice](https://www.bolton.gov.uk/news/article/1838/workwell-is-just-the-job-for-bolton): original funding only to March 2026. The GMCA directory still describes a pilot target to that date. Since this is October 2026, a live page alone does not establish continued funding, capacity or acceptance of new referrals. The UI explicitly says **Confirm availability** and presents no guarantee.
- The [GMCA WorkWell directory](https://www.greatermanchester-ca.gov.uk/what-we-do/education-work-and-skills/working-well/greater-manchester-workwell-service/) was available in search-indexed text; a direct request returned 402. It is not used to claim current programme availability.

No submitted URL is fetched at runtime. Live link health is not silently treated as ongoing content review. Recheck sources and edit review metadata only after actually inspecting the pages; obtain qualified review before real-world use.
