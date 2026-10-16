from datetime import date

from fastapi import HTTPException

from .extraction import extract, questions_for
from .knowledge import KnowledgeLibrary
from .models import AnalyseRequest, AnalyseResponse, Analysis, Conversation, Plan, PlanRequest
from .providers import Extractor, enrich
from .recommendations import recommend
from .referrals import referrals
from .safety import input_text, safety_check

DISCLAIMER = ("Discussion draft for human review with the employee. ADJUST is a prototype providing general, source-linked workplace options, "
              "not medical advice or definitive legal advice. It does not diagnose, determine legal disability or fitness for work, "
              "make employment decisions, or guarantee funding. Seek qualified advice where needed.")
NOTICES = ["Options need discussion with the employee and appropriate assessment before implementation.",
           "No employee name is required. Descriptions and plans are not saved by this module.",
           "Local rules simulate analysis. Source review is an editorial check, not independent professional validation."]


def conversation_for(recommendations, library, today):
    sources = ["A03", "A05", "A06", "A07", "A08"]
    if not library.resolve(sources, today):
        return None
    return Conversation(
        opening="I'd like to understand which parts of your work are difficult at the moment and discuss whether practical changes could help. You can choose what to share; we can focus on work rather than medical details.",
        questions=["Which parts of your work are difficult, and what is already working well?",
                   "What changes do you think might help?",
                   "What would you feel comfortable trying, and how should we check whether it helps?",
                   "What, if anything, would you like shared with colleagues, and with whom?"],
        potential_options=[item.title for item in recommendations],
        agreement_summary="Let's record only what we agree: the change to try, who will arrange it, when it will start, and when we will review it. We can revisit it if your needs or the work change.",
        follow_up=["Confirm any agreed changes in writing with the employee.",
                   "Agree a review date and an earlier check-in if something is not working.",
                   "Discuss appropriate specialist advice if needs or safety remain unclear."],
        source_ids=sources)


def analyse(request: AnalyseRequest, library: KnowledgeLibrary | None = None,
            today: date | None = None, extractor: Extractor | None = None) -> AnalyseResponse:
    library = library or KnowledgeLibrary()
    today = today or date.today()
    safety = safety_check(input_text(request))
    if safety.level != "routine":
        return AnalyseResponse(status=safety.level, analysis=Analysis(), questions=[], recommendations=[], conversation=None,
                               sources=library.resolve(["N01", "N02"], today), referrals=[], safety=safety,
                               provider="Local safety rules", simulated=True, notices=NOTICES, created_on=today)
    extracted = extract(request)
    outcome = enrich(extracted, input_text(request), request.use_ai, extractor)
    analysis = outcome.analysis
    options = [] if analysis.clarification_required else recommend(analysis, library, today)
    status = "clarification" if analysis.clarification_required else "ready" if options else "insufficient_evidence"
    conversation = conversation_for(options, library, today)
    ids = {id_ for option in options for id_ in option.source_ids}
    if conversation:
        ids.update(conversation.source_ids)
    sources = [entry for entry in library.validated(today) if entry.id in ids]
    notices = list(NOTICES)
    if status == "insufficient_evidence":
        notices.insert(0, "The reviewed library does not contain sufficient task-specific evidence for this situation. No adjustment recommendation has been generated. Discuss the barriers and seek relevant professional advice.")
    if analysis.constraints:
        notices.append("Check every option against the stated constraints. A cost or space concern does not itself settle what is reasonable; consider alternatives and appropriate advice.")
    if request.use_ai and not outcome.simulated:
        notices[2] = "Optional AI extracted input excerpts. Local rules selected source-bound options; professional validation remains outstanding."
    return AnalyseResponse(status=status, analysis=analysis, questions=questions_for(analysis), recommendations=options,
                           conversation=conversation, sources=sources, referrals=referrals(today), safety=safety,
                           provider=outcome.provider, simulated=outcome.simulated, provider_note=outcome.note,
                           notices=notices, created_on=today)


def make_plan(request: PlanRequest, library: KnowledgeLibrary | None = None, today: date | None = None) -> Plan:
    today = today or date.today()
    if not request.human_reviewed:
        raise HTTPException(422, "Review the options and confirm human review before creating a discussion draft.")
    if request.review_date < today:
        raise HTTPException(422, "Choose a review date of today or later.")
    if safety_check(request.next_steps).level != "routine":
        raise HTTPException(409, "Immediate or urgent support needs must be addressed before creating a workplace adjustment plan.")
    # Rebuild against trusted knowledge. Never trust client-supplied recommendations,
    # citations, provider output or an earlier result cached in the browser.
    situation = request.situation.model_copy(update={"use_ai": False})
    result = analyse(situation, library, today)
    if result.status != "ready":
        raise HTTPException(409, "A plan needs a complete situation and current source-supported options. Review the situation first.")
    index = {item.id: item for item in result.recommendations}
    if any(id_ not in index for id_ in request.selected_ids):
        raise HTTPException(422, "Choose only the source-supported options returned for this situation.")
    selected = [index[id_] for id_ in request.selected_ids]
    ids = {id_ for option in selected for id_ in option.source_ids} | {"A07", "A08"}
    questions = list(dict.fromkeys(q for option in selected for q in option.employee_questions))[:3]
    tasks = ", ".join(result.analysis.tasks)[:180]
    # Keep the one-page summary bounded. Mark excerpts rather than silently
    # implying the complete input has been reproduced in an exported file.
    barriers = [barrier if len(barrier) <= 180 else barrier[:177].rstrip() + "… [excerpt]"
                for barrier in result.analysis.barriers[:3]]
    return Plan(title="Workplace adjustment plan", workplace_situation=f"Role: {result.analysis.role}. Tasks: {tasks}.",
                barriers=barriers, adjustments=selected, discussion_questions=questions,
                agreed_next_steps=request.next_steps, external_support=result.referrals,
                review_date=request.review_date, sources=[entry for entry in result.sources if entry.id in ids],
                disclaimer=DISCLAIMER, created_on=today)
