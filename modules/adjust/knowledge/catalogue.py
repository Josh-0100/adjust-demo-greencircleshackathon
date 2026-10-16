"""Editorial summaries of pages inspected on 16 October 2026.

These are paraphrases, not quotations or individually assessed legal advice.
The named owner is a prototype editorial role; qualified review remains outstanding.
"""

OWNER = "ADJUST prototype content maintainer (editorial role)"
REVIEWED = "2026-10-16"
REVIEW_DUE = "2027-01-14"

# Exact URLs are allowlisted. A trusted hostname alone is not sufficient evidence.
PAGES = {
    "acas-adjust": ("Acas", "https://www.acas.org.uk/reasonable-adjustments"),
    "acas-request": ("Acas", "https://www.acas.org.uk/reasonable-adjustments/asking-for-reasonable-adjustments"),
    "acas-meeting": ("Acas", "https://www.acas.org.uk/reasonable-adjustments/having-a-meeting"),
    "acas-record": ("Acas", "https://www.acas.org.uk/reasonable-adjustments/reviewing-reasonable-adjustments-and-keeping-a-record"),
    "acas-mental": ("Acas", "https://www.acas.org.uk/reasonable-adjustments/mental-health-adjustments"),
    "acas-oh": ("Acas", "https://www.acas.org.uk/using-occupational-health-at-work"),
    "hse-overview": ("Health and Safety Executive", "https://www.hse.gov.uk/msd/manual-handling/index.htm"),
    "hse-avoid": ("Health and Safety Executive", "https://www.hse.gov.uk/msd/manual-handling/avoid-hazardous-manual-handling.htm"),
    "hse-assess": ("Health and Safety Executive", "https://www.hse.gov.uk/msd/manual-handling/assess-manual-handling.htm"),
    "hse-reduce": ("Health and Safety Executive", "https://www.hse.gov.uk/msd/manual-handling/reduce-risk-injury.htm"),
    "hse-dse": ("Health and Safety Executive", "https://www.hse.gov.uk/msd/dse/assessment.htm"),
    "hse-stress": ("Health and Safety Executive", "https://www.hse.gov.uk/stress/standards/overview.htm"),
    "gov-adjust": ("GOV.UK", "https://www.gov.uk/reasonable-adjustments-for-disabled-workers"),
    "atw-overview": ("GOV.UK", "https://www.gov.uk/access-to-work"),
    "atw-eligibility": ("GOV.UK", "https://www.gov.uk/access-to-work/eligibility"),
    "atw-apply": ("GOV.UK", "https://www.gov.uk/access-to-work/apply"),
    "nhs-urgent": ("NHS", "https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/"),
}

PASSAGES = [
    ("A01", "Start with the individual", "Discuss the person's own workplace barriers and ideas. Practicality, cost and effects on other people's safety need individual consideration.", "acas-adjust", ["general"], "What 'reasonable' means"),
    ("A02", "Different ways of working", "Possible changes include redistributing duties, adapting equipment, changing the workplace or varying working arrangements.", "acas-adjust", ["general", "mobility"], "Examples of reasonable adjustments"),
    ("A03", "Listen without assumptions", "Arrange a discussion, listen to the employee and consider their particular circumstances without making assumptions.", "acas-request", ["general"], "How the employer should handle a reasonable adjustment request"),
    ("A04", "Agree specialist input", "Discuss occupational health input together when advice is needed to identify suitable changes.", "acas-request", ["general"], "How to decide what reasonable adjustments are needed"),
    ("A05", "Prepare a supportive meeting", "Agree a suitable time and place. Think about how to ask sensitively and explain what will happen next.", "acas-meeting", ["general"], "Preparing for the meeting"),
    ("A06", "Employee participation", "Employer and employee should work together to agree adjustments. The employee can choose what they want to disclose.", "acas-meeting", ["general"], "Having a meeting; Preparing for the meeting"),
    ("A07", "Review changes regularly", "Review arrangements together regularly and when the job, workplace or person's circumstances change.", "acas-record", ["general"], "Reviewing reasonable adjustments"),
    ("A08", "Keep an agreed record", "A record can capture work barriers, agreed changes and possible future needs, helping the employee communicate arrangements.", "acas-record", ["general"], "Keeping a record; Reasonable adjustments passports"),
    ("A09", "Discuss breaks and hours", "Shorter, more frequent breaks or flexible hours are possible mental health adjustments to consider individually.", "acas-mental", ["stress", "fatigue"], "Working hours and patterns"),
    ("A10", "Make workload manageable", "Consider reviewing tasks and deadlines, splitting work into smaller tasks and agreeing regular support.", "acas-mental", ["stress", "concentration"], "Changing someone's role and responsibilities; Additional support"),
    ("A11", "Reduce distracting demands", "A quieter workspace or a separate rest area may help. Suitability depends on the person and their work.", "acas-mental", ["stress", "sensory"], "Changing the physical working environment"),
    ("A12", "Agree communication preferences", "Discuss preferred communication methods and predictable check-ins rather than assuming what will help.", "acas-mental", ["stress", "communication"], "Reviewing working relationships and communication styles; Additional support"),
    ("O01", "When occupational health may help", "Occupational health can advise on work barriers, adjustments and returning after sickness absence, through an internal service or outside agency.", "acas-oh", ["general"], "Using occupational health at work"),
    ("O02", "Permission for a doctor's report", "An employer must obtain the worker's permission before contacting their doctor. Discuss the purpose and next steps first.", "acas-oh", ["general"], "Checking if your work uses occupational health"),
    ("H01", "Manual handling risk hierarchy", "Avoid hazardous handling where reasonably practicable, assess unavoidable handling and reduce remaining risks. There is no universal legal lifting-weight limit.", "hse-overview", ["manual"], "Overview"),
    ("H02", "Avoid unnecessary lifting", "Redesign the task or movement of materials to remove hazardous handling where possible.", "hse-avoid", ["manual"], "Avoid hazardous manual handling"),
    ("H03", "Explore mechanical assistance", "Appropriate mechanical aids can reduce or remove manual handling risks; the task and work layout affect what is suitable.", "hse-avoid", ["manual"], "Avoid hazardous manual handling"),
    ("H04", "Assess the whole handling task", "Consider load, posture, frequency, travel distance, environment and individual capability when assessing unavoidable handling.", "hse-assess", ["manual"], "Assess manual handling you can't avoid"),
    ("H05", "Involve the people doing the job", "Workers and their representatives can identify difficult tasks and suggest practical ways of reducing handling risks.", "hse-assess", ["manual"], "Consult your workforce"),
    ("H06", "Review loads and layout", "Smaller loads, shorter carrying distances and less twisting or lifting from awkward heights can reduce risk.", "hse-reduce", ["manual"], "Reduce the risk of injury"),
    ("H07", "Review handling pace", "Consider changing routines that create excessive handling rates or tight deadlines as part of risk reduction.", "hse-reduce", ["manual"], "Reduce the risk of injury"),
    ("H08", "Assess the workstation", "Review equipment, furniture, work conditions and the job. Pain, discomfort or changes to workstation use can trigger reassessment.", "hse-dse", ["desk"], "Workstations and assessment"),
    ("H09", "Have an assessor review results", "A trained assessor should review workstation assessment results, clarify uncertainties and ensure problems are addressed.", "hse-dse", ["desk"], "DSE assessment software"),
    ("H10", "Explore sources of work pressure", "Consider demands, control, support, relationships, role and change when discussing work-related stress.", "hse-stress", ["stress"], "What are the Management Standards?"),
    ("H11", "Work together on improvements", "Use discussion with employees and representatives to understand underlying causes and agree practical workplace improvements.", "hse-stress", ["stress"], "What are the Management Standards?"),
    ("G01", "Read the official duty guidance", "GOV.UK explains the employer adjustment duty and examples. An individual legal assessment requires appropriate advice.", "gov-adjust", ["general"], "Reasonable adjustments for workers with disabilities or health conditions"),
    ("G02", "Disability Employment Adviser route", "GOV.UK signposts the Disability Employment Adviser at the local Jobcentre Plus for adjustment advice.", "gov-adjust", ["general"], "Get help and advice"),
    ("T01", "Access to Work support", "Depending on need, support may include equipment, support workers or mental health support. An application is not a funding guarantee.", "atw-overview", ["referral"], "What Access to Work is"),
    ("T02", "Check Access to Work criteria", "The official criteria cover age, paid work, location and support needs. A diagnosis is not required to apply; ADJUST does not decide eligibility.", "atw-eligibility", ["referral"], "Eligibility; Your disability, illness or health condition"),
    ("T03", "Official application route", "The worker can use the official application page, including online and telephone routes and accessible-format information.", "atw-apply", ["referral"], "Apply online; Apply by phone"),
    ("N01", "Immediate safety takes priority", "Call 999 or go to A&E when life is at risk or someone cannot be kept safe. Pause the adjustment workflow.", "nhs-urgent", ["safety"], "Immediate action required"),
    ("N02", "Urgent mental health advice", "For urgent mental health help, contact NHS 111 and select the mental health option, or seek an urgent GP appointment.", "nhs-urgent", ["safety"], "Urgent advice"),
]


def entries():
    return [dict(id=id_, topic=topic, summary=summary, official_url=PAGES[page][1],
                 publisher=PAGES[page][0], last_reviewed=REVIEWED, content_owner=OWNER,
                 scenarios=scenarios, verification_status="verified", evidence_locator=locator,
                 review_due=REVIEW_DUE)
            for id_, topic, summary, page, scenarios, locator in PASSAGES]
