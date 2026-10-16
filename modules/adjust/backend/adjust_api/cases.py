"""Stateless two-person discussion drafts built only from reviewed need IDs.

Descriptions are used for a bounded local suggestion step and are never copied
into the shared contract. There is no case, link, token or text storage here.
"""
import re
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import Field, field_validator

from .models import Safety, StrictModel
from .safety import normalise, safety_check

Role = Literal["employee", "employer"]
SupportKind = Literal["health", "carer", "both"]
BusinessSize = Literal["under_50", "50_249", "250_plus"]

EMPLOYEE_NEEDS = {
    "later-start": "Mornings are hard; I would like to discuss a later start.",
    "breaks": "I need regular breaks during the working day.",
    "standing": "Standing for long periods is hard.",
    "lifting": "Repeated lifting or carrying is hard.",
    "quiet": "I need a quieter place for focused work.",
    "written": "I would like clear written instructions and priorities.",
    "workload": "I need help managing workload and deadlines.",
    "flexibility": "I need flexibility around caring responsibilities.",
    "appointments": "I need to discuss time for appointments.",
    "discuss-needs": "I would like to discuss what would help me at work.",
}
EMPLOYER_NEEDS = {
    "cover": "We need reliable cover during agreed working hours.",
    "core-tasks": "Some core duties need to stay in place.",
    "fixed-hours": "Working hours need to stay fixed.",
    "limited-budget": "We need to work within a limited budget.",
    "small-space": "There is limited space for equipment or a separate room.",
    "tried-flexible": "Flexible working arrangements have already been tried.",
    "discuss-practicalities": "We would like to discuss what is practical for the business.",
}

ACAS_ADJUSTMENTS = "https://www.acas.org.uk/reasonable-adjustments"
ACAS_MEETING = "https://www.acas.org.uk/reasonable-adjustments/having-a-meeting"
ACAS_MENTAL_HEALTH = "https://www.acas.org.uk/reasonable-adjustments/mental-health-adjustments"
ATW_EMPLOYERS = "https://www.gov.uk/government/publications/access-to-work-guide-for-employers/access-to-work-factsheet-for-employers"
ATW_COST_SHARE = "https://www.gov.uk/government/publications/access-to-work-staff-guide/access-to-work-staff-guide"
FLEXIBLE_WORKING = "https://www.gov.uk/flexible-working"
CARERS_LEAVE = "https://www.gov.uk/carers-leave"


class Need(StrictModel):
    id: str
    text: str


class Catalogue(StrictModel):
    employee_needs: list[Need]
    employer_needs: list[Need]


class PrepareRequest(StrictModel):
    role: Role
    description: str = Field(min_length=20, max_length=4000)
    support_kind: SupportKind = "health"
    business_size: BusinessSize | None = None
    role_context: str = Field(default="", max_length=700)
    practicalities: str = Field(default="", max_length=700)
    tried: str = Field(default="", max_length=700)


class PrepareResponse(StrictModel):
    status: Literal["review", "urgent", "emergency"]
    needs: list[Need]
    safety: Safety


class EmployeeContribution(StrictModel):
    reviewed: Literal[True]
    need_ids: list[str] = Field(max_length=10)
    support_kind: SupportKind

    @field_validator("need_ids")
    @classmethod
    def known_ids(cls, value):
        return validate_ids(value, EMPLOYEE_NEEDS)


class EmployerContribution(StrictModel):
    reviewed: Literal[True]
    need_ids: list[str] = Field(max_length=10)
    business_size: BusinessSize

    @field_validator("need_ids")
    @classmethod
    def known_ids(cls, value):
        return validate_ids(value, EMPLOYER_NEEDS)


def validate_ids(value: list[str], catalogue: dict[str, str]) -> list[str]:
    if len(set(value)) != len(value):
        raise ValueError("Review each work need once.")
    if any(item not in catalogue for item in value):
        raise ValueError("Choose work needs from the reviewed catalogue.")
    return value


class CombinedPlanRequest(StrictModel):
    employee: EmployeeContribution
    employer: EmployerContribution
    review_date: date


class PlanItem(StrictModel):
    id: str
    title: str
    detail: str
    url: str


class JointConversation(StrictModel):
    opening: str
    questions: list[str]
    agree: list[str]


class CombinedPlan(StrictModel):
    title: str
    created_on: date
    review_date: date
    start_now: list[PlanItem]
    options: list[PlanItem]
    conversation: JointConversation
    help: list[PlanItem]
    legal_note: str
    disclaimer: str


def item(id_: str, title: str, detail: str, url: str = ACAS_ADJUSTMENTS) -> PlanItem:
    return PlanItem(id=id_, title=title, detail=detail, url=url)


def prepare_contribution(request: PrepareRequest) -> PrepareResponse:
    fields = [request.description, request.role_context, request.practicalities, request.tried]
    text = normalise("\n".join(fields))
    safety = safety_check(text)
    # Extend recall for this new route without changing legacy analysis. These
    # intentionally conservative phrases are a stop signal, not clinical triage.
    if safety.level == "routine" and re.search(
        r"\b(?:(?:end|ending|take|taking) (?:my|their|his|her|your) (?:own )?life|"
        r"ending it all|(?:don't|do not) want to (?:live|be alive))\b", text
    ):
        safety = Safety(level="emergency", title="Pause. Immediate safety comes first.",
                        message="If your life is at risk or you cannot keep yourself or someone else safe, call 999 or go to A&E now.")
    elif safety.level == "routine" and re.search(r"\b(?:can't|cannot|can not) go on\b", text):
        safety = Safety(level="urgent", title="Get urgent professional support first",
                        message="If you feel you cannot go on, get urgent support. In England call NHS 111 and select the mental health option. If life is at risk, call 999.")
    if safety.level != "routine":
        # Use the existing safety contract while making all requested routes
        # available for both people; no descriptions enter the response.
        safety = safety.model_copy(update={"official_url": safety.official_url or "https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/", "actions": [
            "If someone is in immediate danger or cannot be kept safe, call 999 or go to A&E now.",
            "For urgent mental health help in England, call NHS 111 and select the mental health option.",
            "For someone to talk to, call Samaritans free on 116 123, any time.",
            "Pause this workflow and seek appropriate support. These phrase checks are not clinical triage.",
        ]})
        return PrepareResponse(status=safety.level, needs=[], safety=safety)
    if request.role == "employee":
        rules = {
            "later-start": r"\b(?:morning\w*|later start|start later|early start\w*)\b",
            "breaks": r"\b(?:break\w*|fatigue|tired|exhaust\w*|rest\w*)\b",
            "standing": r"\b(?:stand\w*|on my feet|on their feet)\b",
            "lifting": r"\b(?:lift\w*|carry\w*|carrying|manual handling)\b",
            "quiet": r"\b(?:nois\w*|quiet\w*|distract\w*|concentrat\w*)\b",
            "written": r"\b(?:written|instruction\w*|remember\w*|communication)\b",
            "workload": r"\b(?:workload|deadline\w*|overwhelm\w*|priorit\w*|pressure|stress\w*)\b",
            "flexibility": r"\b(?:carer\w*|caring|unpaid care|look\w* after)\b",
            "appointments": r"\b(?:appointment\w*|treatment|hospital visit\w*)\b",
        }
        ids = [key for key, pattern in rules.items() if re.search(pattern, text)]
        if request.support_kind in {"carer", "both"} and "flexibility" not in ids:
            ids.append("flexibility")
        catalogue = EMPLOYEE_NEEDS
        ids = ids or ["discuss-needs"]
    else:
        rules = {
            "cover": r"\b(?:cover\w*|customer\w*|opening hours|staffing|rota)\b",
            "core-tasks": r"\b(?:core|essential|cannot change|can't change|must|safety|duties)\b",
            "fixed-hours": r"\b(?:fixed (?:opening |working )?hours|fixed shifts?|(?:hours|shifts?) (?:cannot|can't) change|(?:start|opening) time (?:cannot|can't) change|(?:cannot|can't) change (?:the )?(?:hours|shifts?|start time))\b",
            "limited-budget": r"\b(?:budget|no money|cost\w*|afford\w*|fund\w*)\b",
            "small-space": r"\b(?:small (?:space|shop|office)|limited (?:floor )?space|no (?:separate|spare) room)\b",
        }
        ids = [key for key, pattern in rules.items() if re.search(pattern, text)]
        if re.search(r"\b(?:flexib\w*|later start|different hours|shift\w*)\b", normalise(request.tried)):
            ids.append("tried-flexible")
        catalogue = EMPLOYER_NEEDS
        ids = ids or ["discuss-practicalities"]
    return PrepareResponse(status="review", needs=[Need(id=id_, text=catalogue[id_]) for id_ in ids], safety=safety)


def access_to_work(size: BusinessSize, carer_only: bool) -> PlanItem:
    shares = {
        "under_50": "Under 50 employees: the staff guide lists nil employer cost share.",
        "50_249": "50–249 employees: the staff guide lists a £500 threshold, then 20% of the next £10,000 of approved shared costs.",
        "250_plus": "250+ employees: the staff guide lists a £1,000 threshold, then 20% of the next £10,000 of approved shared costs.",
    }
    prefix = "Caring alone does not establish eligibility. " if carer_only else "The worker can check eligibility and apply. "
    detail = prefix + shares[size] + " Cost sharing applies only to some equipment/adaptations, usually after six weeks in the job; exemptions apply. Official guidance differs in how the band is described: confirm the actual award and share with Access to Work. Statutory reasonable adjustments are not funded; no award is guaranteed."
    return item("access-to-work", "Access to Work: confirm funding and cost share", detail, ATW_COST_SHARE)


def make_combined_plan(request: CombinedPlanRequest, today: date | None = None) -> CombinedPlan:
    today = today or date.today()
    if request.review_date <= today:
        raise HTTPException(422, "Choose a review date after today.")
    employee = set(request.employee.need_ids)
    employer = set(request.employer.need_ids)
    caring = request.employee.support_kind in {"carer", "both"}
    health = request.employee.support_kind in {"health", "both"}
    fixed_hours = "fixed-hours" in employer

    start_now = [item("agree-priorities", "Agree priorities and a check-in", "Agree today's priorities, a named contact and a short check-in; write down any trial both people accept.", ACAS_MEETING)]
    if "later-start" in employee and not fixed_hours:
        start_now.append(item("agreed-start", "Discuss an adjusted start time", "If both people agree and cover can be maintained, trial a different start and finish time without adding cost.", ACAS_MENTAL_HEALTH))
    elif employee & {"breaks", "standing"}:
        start_now.append(item("agreed-breaks", "Agree breaks within the working day", "Agree brief breaks or changes of activity within existing hours and safe cover; do not transfer unsafe work to another person.", ACAS_MENTAL_HEALTH))
    elif employee & {"written", "workload", "quiet"}:
        start_now.append(item("clear-tasks", "Make tasks easier to follow", "Agree clear written priorities and a quiet focus period within the existing workspace and agreed hours.", ACAS_MENTAL_HEALTH))
    else:
        start_now.append(item("review-work", "Review the work together", "Discuss which tasks, communication or work patterns can change using existing resources; agree changes before trying them.", ACAS_MEETING))

    options: list[PlanItem] = []
    if "lifting" in employee:
        options.append(item("safe-handling", "Assess handling tasks before changes", "Use a competent task assessment to avoid hazardous handling where possible and reduce remaining risks. Consider suitable aids; do not assume lifting technique or sharing a load makes it safe.", "https://www.hse.gov.uk/msd/manual-handling/assess-manual-handling.htm"))
    elif employee & {"standing", "breaks"}:
        options.append(item("workstation-review", "Review the workstation and tasks", "Discuss suitable seating, access, breaks and changes of activity; assess the actual work and any equipment before use.", ACAS_ADJUSTMENTS))
    elif employee & {"quiet", "written", "workload"}:
        space = "Use existing space and consider scheduled quiet periods; a separate room has not been assumed." if "small-space" in employer else "Consider a quieter work area, clear instructions and manageable priorities."
        options.append(item("work-design", "Review work design", space + " Agree a short trial and how to judge whether it helps.", ACAS_MENTAL_HEALTH))
    elif health:
        detail = "Explore support within the fixed working hours; changing the start time is not assumed possible." if fixed_hours else "Discuss changes to tasks, communication, work patterns or the environment that meet the reviewed needs."
        options.append(item("review-options", "Explore suitable adjustments", detail + " Consider what is effective and reasonable in this workplace.", ACAS_ADJUSTMENTS))
    if "appointments" in employee and len(options) < 3:
        options.append(item("appointment-planning", "Plan appointment time", "Discuss notice, cover and whether working time, leave or an agreed adjustment can help; record what has been agreed.", ACAS_ADJUSTMENTS))
    if caring:
        # Preserve both statutory carer routes even when several work needs were
        # selected. Additional reviewed needs remain in the meeting questions.
        options = options[:1]
        options.extend([
            item("flexible-working", "Right to request flexible working", "Employees can make a statutory request from their first day. This is a right to request; the requested arrangement is not guaranteed. Discuss the business needs and follow the statutory process.", FLEXIBLE_WORKING),
            item("carers-leave", "Unpaid Carer's Leave", "From day one, eligible employees can take up to one usual working week of unpaid leave in each 12 months for a dependant with a long-term care need, including half-days. Check the notice rules.", CARERS_LEAVE),
        ])

    questions = []
    if employee:
        questions.append("Which of these reviewed needs matters most today? " + " ".join(EMPLOYEE_NEEDS[id_] for id_ in request.employee.need_ids))
    else:
        questions.append("What, if anything, would make work easier? No employee needs have been included in the shared list.")
    if employer:
        questions.append("How can we meet the work needs alongside these practical points? " + " ".join(EMPLOYER_NEEDS[id_] for id_ in request.employer.need_ids))
    else:
        questions.append("What does the role require, and what is practical for the business?")
    if fixed_hours and "later-start" in employee:
        questions.append("With working hours fixed, what support within those hours could help with mornings?")
    if "tried-flexible" in employer:
        questions.append("What helped or did not help in the previous flexible working trial, and what would be different now?")
    questions.append("Which trial can we agree, who will arrange it, and how will we know whether it is helping?")

    help_items = [
        access_to_work(request.employer.business_size, caring and not health),
        item("acas", "Acas", "Get impartial advice on adjustments, flexible working, leave and a fair workplace process; seek advice if cost or feasibility is uncertain.", "https://www.acas.org.uk/contact"),
        item("occupational-health", "Occupational health", "Where relevant, discuss an occupational health assessment of workplace support needs; explain consent, what will be shared and any cost first.", "https://www.acas.org.uk/using-occupational-health-at-work"),
    ]
    if health:
        help_items.append(item("bolton-workwell", "Bolton work and health support", "Ask the published WorkWell Bolton route about current support. Original pilot funding ended in March 2026; current availability and acceptance of referrals must be confirmed.", "https://letskeepboltonmoving.co.uk/education-employment/workwell/"))
    if caring:
        help_items.extend([
            item("carer-assessment", "Carer's assessment: Bolton Council", "If the person you care for lives in Bolton, ask Bolton Council for an assessment of your support needs; otherwise contact their council. An assessment does not guarantee a funded service.", "https://www.bolton.gov.uk/carers"),
            item("carers-allowance", "Check Carer's Allowance", "Check GOV.UK eligibility, including at least 35 hours of care, a qualifying benefit for the person cared for and earnings rules. A claim can affect both people's benefits; get a benefits check before claiming.", "https://www.gov.uk/carers-allowance/eligibility"),
        ])
    if health:
        legal_note = "Employers have a duty to make reasonable adjustments for disabled employees. ADJUST does not determine disability or what is reasonable."
        if caring:
            legal_note += " Caring alone does not create that duty; carers can use their flexible-working and leave rights."
    else:
        legal_note = "Caring alone does not create a duty to make reasonable adjustments. Carers can use flexible-working and Carer's Leave rights; the adjustment duty applies to disabled employees."
    return CombinedPlan(
        title="Our workplace conversation plan", created_on=today, review_date=request.review_date,
        start_now=start_now, options=options[:3],
        conversation=JointConversation(
            opening="Let's talk about what would help at work and what is practical, then agree a small trial together.",
            questions=questions,
            agree=["Write down the agreed changes, who will arrange them, any costs and safe cover.", "Record the trial period, how to raise a concern and the review date; update the plan together."],
        ),
        help=help_items, legal_note=legal_note,
        disclaimer="Fictional demo discussion draft, using authored local rules. Both people have reviewed what is shared; they have not yet agreed this plan. No eligibility, funding, medical or employment decision is made. Private descriptions are not included or saved by ADJUST.",
    )


router = APIRouter(prefix="/case", tags=["ADJUST two-sided discussion"])


@router.get("/catalogue", response_model=Catalogue)
def catalogue_route():
    return Catalogue(employee_needs=[Need(id=id_, text=text) for id_, text in EMPLOYEE_NEEDS.items()],
                     employer_needs=[Need(id=id_, text=text) for id_, text in EMPLOYER_NEEDS.items()])


@router.post("/prepare", response_model=PrepareResponse)
def prepare_route(request: PrepareRequest):
    return prepare_contribution(request)


@router.post("/plan", response_model=CombinedPlan)
def combined_plan_route(request: CombinedPlanRequest):
    return make_combined_plan(request)
