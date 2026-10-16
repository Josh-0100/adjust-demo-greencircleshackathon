from datetime import date

from .models import Referral

CHECKED = date(2026, 10, 16)


def referrals(today: date):
    # Directory entries are informational. They do not create referrals or share data.
    items = [
        Referral(id="access-to-work", name="Access to Work", publisher="GOV.UK",
                 provides="Practical work support may include specialist equipment, support workers and mental health support.",
                 eligibility="The worker should check the current age, paid-work, location and support-needs criteria on GOV.UK. ADJUST cannot decide eligibility.",
                 access="Read the overview, check eligibility and follow the official application route. The worker controls the application.",
                 official_url="https://www.gov.uk/access-to-work", verified_on=CHECKED, status="guidance_checked",
                 limitations="Funding is not guaranteed. Do not assume processing times or delay employer responsibilities while awaiting support."),
        Referral(id="acas", name="Acas advice", publisher="Acas",
                 provides="Official information on workplace adjustments and routes to employment advice.",
                 eligibility="Employers and workers can read the guidance and use the contact routes for their circumstances.",
                 access="Use Acas guidance or the helpline link on its official contact page.",
                 official_url="https://www.acas.org.uk/contact", verified_on=CHECKED, status="guidance_checked",
                 limitations="General guidance is not an individual legal determination. Seek appropriate advice where duties or disputes are unclear."),
        Referral(id="occupational-health", name="Occupational health", publisher="Acas",
                 provides="Specialist advice about how work and health interact, and possible changes to work.",
                 eligibility="Check your employer's service or explore a suitable external provider with the employee.",
                 access="Discuss the purpose, consent and information to share before arranging an assessment. See Acas for the process.",
                 official_url="https://www.acas.org.uk/using-occupational-health-at-work", verified_on=CHECKED, status="guidance_checked",
                 limitations="ADJUST does not assess fitness for work. Obtain permission before contacting an employee's doctor; provider access and charges vary."),
        Referral(id="bolton-workwell", name="WorkWell Bolton", publisher="Bolton Council / Let's Keep Bolton Moving",
                 provides="The published page describes voluntary Work and Health Coach support for work-related health barriers.",
                 eligibility="The published page describes support for Bolton residents in work or recently out of work due to health barriers. Ask the provider to confirm current criteria.",
                 access="Use the official local information page to check whether referrals are currently being accepted. Do not submit employee details without their involvement.",
                 official_url="https://letskeepboltonmoving.co.uk/education-employment/workwell/", verified_on=CHECKED, status="confirm_availability",
                 limitations="A live information/referral page was checked, but the original council notice funded the scheme only until March 2026. Current capacity and continued funding are unconfirmed."),
    ]
    if (today - CHECKED).days > 90 or today < CHECKED:
        for item in items:
            item.status = "confirm_availability"
            item.limitations = "This directory entry is due for review. Confirm current details directly. " + item.limitations
    return items
