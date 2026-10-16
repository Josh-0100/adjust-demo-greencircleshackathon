"""Resident assessment engine (Phase 3).

The default path is a fully local, deterministic extractor: it reads the
resident's own words and maps them to bounded, explainable fields. It never
invents experience, skills, or circumstances, and it never names a medical
diagnosis or judges fitness for work — practical limitations are recorded only
as the resident phrases them.

When an operator configures the optional vendor-neutral provider, we attempt an
LLM extraction, then sanitise *every* field back through the same schema and
safety screen. Any problem falls back to the deterministic result, so the
module is always safe offline.
"""
from __future__ import annotations

import re

from .providers import run_llm_assessment
from .safety import check_text, safe_excerpt
from .schemas import (
    AssessmentRequest,
    EmploymentStatus,
    ResidentAssessment,
)
from .settings import Settings

# ---------------------------------------------------------------------------
# Lexicons. Each entry maps canonical output -> trigger phrases. Phrases are
# matched as whole words/sequences against the lowercased text.
# ---------------------------------------------------------------------------

_NEGATORS = (
    "no",
    "not",
    "don't",
    "dont",
    "cannot",
    "can't",
    "cant",
    "never",
    "without",
    "lack",
    "haven't",
    "havent",
    "didn't",
    "didnt",
    "won't",
    "wont",
    "struggle with",
    "poor",
)

# Markers that a sector is a future aspiration rather than past experience.
_FUTURE_MARKERS = (
    "want to",
    "wants to",
    "would like",
    "like to",
    "hoping to",
    "hope to",
    "interested in",
    "get into",
    "move into",
    "retrain",
    "train in",
    "training in",
    "study",
    "learn",
    "keen to",
    "looking to",
)

# Employment status detection, most specific first.
_STATUS_RULES: list[tuple[EmploymentStatus, tuple[str, ...]]] = [
    (
        "unemployed",
        (
            "unemployed",
            "lost my job",
            "lost my position",
            "out of work",
            "made redundant",
            "redundant",
            "redundancy",
            "jobseeker",
            "looking for work",
            "looking for a job",
            "seeking work",
            "between jobs",
            "not working",
            "no job",
        ),
    ),
    (
        "self_employed",
        ("self-employed", "self employed", "freelance", "sole trader", "my own business", "run my own"),
    ),
    (
        "student",
        ("i'm a student", "im a student", "i am a student", "at college", "at university", "studying for"),
    ),
    ("retired", ("retired", "i have retired", "took early retirement")),
    (
        "economically_inactive",
        (
            "full-time carer",
            "full time carer",
            "carer for",
            "caring for",
            "looking after my",
            "long-term sick",
            "long term sick",
            "economically inactive",
            "unable to work",
        ),
    ),
    (
        "employed",
        ("currently employed", "i work as", "i work at", "i work in", "in work", "my current job", "i'm employed", "im employed"),
    ),
]

# Sector / role experience. Canonical label -> trigger phrases.
_EXPERIENCE_ALIASES: dict[str, tuple[str, ...]] = {
    "warehouse": ("warehouse", "warehousing", "picker packer", "pick and pack"),
    "retail": ("retail", "shop assistant", "shop work", "sales assistant", "cashier", "checkout"),
    "hospitality": ("hospitality", "waiter", "waitress", "bar work", "barista", "pub", "hotel"),
    "catering": ("catering", "kitchen", "chef", "cook", "kitchen porter"),
    "care": ("care work", "carer", "care home", "support worker", "healthcare assistant", "care assistant"),
    "cleaning": ("cleaning", "cleaner", "domestic"),
    "construction": ("construction", "building site", "labourer", "bricklayer", "joiner", "plasterer", "scaffolder"),
    "driving": ("driver", "driving", "hgv", "lgv", "delivery driver", "courier", "taxi"),
    "manufacturing": ("manufacturing", "factory", "production line", "assembly"),
    "administration": ("admin", "administration", "administrator", "office work", "receptionist", "data entry"),
    "customer service": ("customer service", "call centre", "call center", "contact centre", "helpdesk"),
    "security": ("security guard", "door supervisor", "sia"),
    "teaching": ("teacher", "teaching assistant", "classroom assistant", "tutor"),
    "nursing": ("nurse", "nursing"),
    "hairdressing": ("hairdresser", "hairdressing", "barber", "beauty therapist"),
    "mechanic": ("mechanic", "car repair", "vehicle technician"),
    "gardening": ("gardener", "gardening", "landscaping", "groundskeeper"),
    "it": ("software", "developer", "it support", "programmer", "web developer"),
    "finance": ("accountant", "accounts", "bookkeeper", "bookkeeping", "payroll"),
    "sales": ("sales rep", "sales representative", "telesales", "account manager"),
}

# Explicitly-stated transferable skills only. Never inferred from experience.
_SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "communication": ("communication", "good communicator", "communicating"),
    "teamwork": ("teamwork", "team work", "work in a team", "working in a team", "team player"),
    "leadership": ("leadership", "leading a team", "managing a team", "team leader", "supervising", "supervisor experience"),
    "customer service": ("customer service skills", "good with customers", "dealing with customers"),
    "problem solving": ("problem solving", "problem-solving"),
    "organisation": ("organised", "organisation skills", "organisational skills", "time management"),
    "numeracy": ("good with numbers", "numeracy", "maths skills"),
    "literacy": ("good at writing", "literacy skills"),
    "it skills": ("computer skills", "it skills", "good with computers", "microsoft office", "excel", "word processing"),
    "driving licence": ("driving licence", "driving license", "clean licence", "full licence"),
    "forklift": ("forklift licence", "forklift license", "forklift ticket", "counterbalance"),
    "first aid": ("first aid",),
    "languages": ("bilingual", "speak two languages", "languages",),
    "cooking": ("cooking skills", "food hygiene"),
}

# Practical barriers. Canonical plain-English label -> trigger phrases. These are
# recorded as the resident frames them and are NEVER clinical findings.
_BARRIER_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Difficulty with heavy lifting", ("heavy lifting", "can't lift", "cant lift", "cannot lift", "lifting heavy", "bad back", "back problem", "back pain")),
    ("Health affects some physical tasks (resident-stated)", ("long-term sick", "long term sick", "health condition", "ongoing health", "chronic pain", "mobility", "on my feet all day", "standing for long")),
    ("Transport difficulties", ("no car", "can't drive", "cant drive", "no transport", "rely on buses", "public transport", "getting to work")),
    ("Childcare responsibilities", ("childcare", "children to look after", "look after my kids", "school run", "single parent", "young children")),
    ("Caring responsibilities", ("caring for", "carer for", "look after my mum", "look after my dad", "care for a relative")),
    ("Limited formal qualifications", ("no qualifications", "left school with nothing", "no gcses", "without qualifications")),
    ("Gap in recent employment history", ("been out of work", "gap in my cv", "not worked for", "haven't worked for", "havent worked for", "out of work for")),
    ("Low confidence about returning to work", ("lost my confidence", "no confidence", "lack confidence", "nervous about", "anxious about going back", "worried about interviews")),
    ("Limited digital confidence", ("not good with computers", "no computer", "struggle online", "can't use a computer", "cant use a computer", "no internet")),
    ("Would value help with reading, writing or maths", ("struggle with reading", "struggle with writing", "trouble with maths", "poor literacy", "poor numeracy")),
    ("English language support may help", ("english is not my first", "english isn't my first", "esol", "english as a second language")),
    ("Age-related concerns about finding work", ("too old", "my age", "ageism", "older worker")),
]

# Goals. Canonical label -> trigger phrases.
_GOAL_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Return to work", ("back into work", "back to work", "return to work", "get back to work", "get into work", "find a job", "find work", "get a job", "want to work", "want a job")),
    ("Retrain for a new sector", ("retrain", "change career", "new career", "career change", "different line of work", "switch careers")),
    ("Gain a qualification", ("get qualified", "gain a qualification", "get a qualification", "a qualification in")),
    ("Explore self-employment", ("start my own business", "be my own boss", "become self-employed", "set up on my own")),
    ("Find flexible or part-time work", ("part-time work", "part time work", "flexible work", "flexible hours", "work around")),
    ("Progress to a better-paid role", ("better paid", "better job", "progress", "promotion", "earn more")),
]

# Training interests. Canonical label -> trigger phrases.
_TRAINING_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Digital skills", ("digital skills", "computer course", "it course", "learn computers", "online skills", "basic it")),
    ("Forklift / warehouse certificate", ("forklift", "counterbalance", "warehouse certificate")),
    ("Driving / HGV licence", ("hgv licence", "lgv licence", "learn to drive", "driving lessons", "cpc")),
    ("Construction (CSCS)", ("cscs", "construction card")),
    ("Care certificate", ("care certificate", "nvq in care", "health and social care course")),
    ("Customer service training", ("customer service course", "customer service qualification")),
    ("English or maths (functional skills)", ("functional skills", "english course", "maths course", "improve my english", "improve my maths")),
    ("First aid certificate", ("first aid course", "first aid certificate")),
    ("Food hygiene certificate", ("food hygiene",)),
]

# Support preferences. Canonical label -> trigger phrases.
_PREF_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Face-to-face support", ("face to face", "face-to-face", "in person", "meet someone")),
    ("Remote or phone support", ("over the phone", "by phone", "online support", "remote support", "video call", "from home")),
    ("Support local to Bolton", ("near me", "close to home", "local to me", "in bolton", "in my area")),
    ("One-to-one support", ("one to one", "one-to-one", "1 to 1", "1-2-1", "121 support")),
    ("Group or peer support", ("group support", "meet other people", "peer support", "with others")),
    ("Flexible timing (evenings/weekends)", ("evenings", "weekends", "around my childcare", "around school", "outside work hours")),
]

# Concrete support needs. Canonical label -> trigger phrases.
_SUPPORT_NEED_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Help updating a CV", ("cv", "curriculum vitae", "resume")),
    ("Interview preparation", ("interview", "interviews")),
    ("Help searching and applying for jobs", ("job search", "applying for jobs", "application form", "find vacancies", "where to apply")),
    ("Confidence building", ("build my confidence", "confidence", "self-esteem")),
    ("Money or benefits guidance", ("universal credit", "benefits advice", "money worries", "financial", "budgeting", "debt")),
    ("Help arranging childcare", ("childcare support", "help with childcare")),
    ("Travel or transport support", ("help with transport", "travel costs", "bus pass")),
    ("Workplace adjustments", ("reasonable adjustments", "workplace adjustments", "adjustments at work", "adapted role")),
]

_WORD_RE = re.compile(r"[a-z0-9']+")


def _contains(haystack: str, phrase: str) -> bool:
    """Whole-token containment so 'car' does not match inside 'care'."""
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", haystack))


def _negated_near(text: str, phrase: str, window: int = 4) -> bool:
    """True if a negation token sits just before ``phrase`` (word window)."""
    idx = text.find(phrase)
    if idx == -1:
        return False
    prefix = text[:idx]
    preceding = _WORD_RE.findall(prefix)[-window:]
    chunk = " ".join(preceding)
    return any(neg in chunk or chunk.endswith(neg) for neg in _NEGATORS)


def _is_future_context(text: str, phrase: str, window: int = 5) -> bool:
    """True if ``phrase`` is preceded by an aspiration marker (want to learn X)."""
    idx = text.find(phrase)
    if idx == -1:
        return False
    prefix = text[max(0, idx - 60):idx]
    return any(marker in prefix for marker in _FUTURE_MARKERS)


# "lost my job", "lost my warehouse job", "lost my part-time job", etc. — the
# noun phrase between "my" and "job" must stay short so "lost my confidence"
# never matches.
_LOST_JOB_RE = re.compile(r"\blost\s+(?:my|the|his|her)\s+(?:[\w-]+\s+){0,3}job\b")


def _detect_status(text: str) -> EmploymentStatus:
    if _LOST_JOB_RE.search(text):
        return "unemployed"
    for status, phrases in _STATUS_RULES:
        for phrase in phrases:
            if _contains(text, phrase):
                return status
    return "unknown"


def _collect_aliases(text: str, aliases: dict[str, tuple[str, ...]], *, gate_future: bool, gate_negation: bool) -> list[str]:
    found: list[str] = []
    for label, phrases in aliases.items():
        for phrase in phrases:
            if not _contains(text, phrase):
                continue
            if gate_future and _is_future_context(text, phrase):
                continue
            if gate_negation and _negated_near(text, phrase):
                continue
            found.append(label)
            break
    return found


def _collect_rules(text: str, rules: list[tuple[str, tuple[str, ...]]]) -> list[str]:
    found: list[str] = []
    for label, phrases in rules:
        if any(_contains(text, phrase) for phrase in phrases):
            found.append(label)
    return found


def _deterministic(request: AssessmentRequest) -> ResidentAssessment:
    text = request.text.lower()
    profile = request.profile

    # Self-declared profile status is authoritative over text guessing.
    status = profile.employment_status or _detect_status(text)

    experience = _collect_aliases(text, _EXPERIENCE_ALIASES, gate_future=True, gate_negation=False)
    skills = _collect_aliases(text, _SKILL_ALIASES, gate_future=False, gate_negation=True)
    barriers = _collect_rules(text, _BARRIER_RULES)
    goals = _collect_rules(text, _GOAL_RULES)
    training = _collect_rules(text, _TRAINING_RULES)
    prefs = _collect_rules(text, _PREF_RULES)
    needs = _collect_rules(text, _SUPPORT_NEED_RULES)

    # A self-declared health/disability support need is practical, not clinical.
    if profile.has_health_condition_or_disability and not any("Health affects" in b for b in barriers):
        barriers.append("Health or disability support need (resident-stated)")
    if profile.digital_confidence == "low" and "Limited digital confidence" not in barriers:
        barriers.append("Limited digital confidence")

    assessment = ResidentAssessment(
        employment_status=status,
        experience=experience,
        skills=skills,
        goals=goals,
        barriers=barriers,
        support_needs=needs,
        training_interests=training,
        support_preferences=prefs,
        provider="deterministic",
    )
    _apply_clarification(assessment)
    assessment.confidence = _coverage(assessment)
    assessment.disclaimers = _base_disclaimers()
    return assessment


def _coverage(a: ResidentAssessment) -> float:
    signals = [
        a.employment_status != "unknown",
        bool(a.experience),
        bool(a.skills),
        bool(a.goals),
        bool(a.barriers),
        bool(a.support_needs),
        bool(a.training_interests),
        bool(a.support_preferences),
    ]
    return round(sum(signals) / len(signals), 2)


def _apply_clarification(a: ResidentAssessment) -> None:
    """Ask a single plain question only when there is too little to help."""
    too_thin = (
        a.employment_status == "unknown"
        and not a.experience
        and not a.skills
        and not a.goals
    )
    if too_thin:
        a.clarification_required = True
        a.clarifying_question = (
            "To point you in the right direction, could you tell me a little about "
            "the kind of work you've done before and what you'd like to do next?"
        )
    else:
        a.clarification_required = False
        a.clarifying_question = None


def _base_disclaimers() -> list[str]:
    return [
        "This is an automated summary of what you told us, to review with an adviser.",
        "It does not assess medical fitness for work or decide eligibility for any service.",
    ]


# ---------------------------------------------------------------------------
# Optional LLM sanitisation
# ---------------------------------------------------------------------------

_LIST_FIELDS = {
    "experience": 40,
    "skills": 40,
    "goals": 20,
    "barriers": 20,
    "support_needs": 20,
    "training_interests": 20,
    "support_preferences": 20,
}
_VALID_STATUSES = {
    "unemployed",
    "employed",
    "self_employed",
    "economically_inactive",
    "student",
    "retired",
    "unknown",
}


def _clean_item(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        safe = check_text(stripped)
    except ValueError:
        return None
    return safe_excerpt(safe, limit=120)


def _sanitise_llm(raw: dict, fallback: ResidentAssessment) -> ResidentAssessment | None:
    """Coerce an unvalidated model dict into a safe ResidentAssessment.

    Returns ``None`` if the payload cannot be trusted, so the caller keeps the
    deterministic result.
    """
    status = raw.get("employment_status")
    if status not in _VALID_STATUSES:
        status = fallback.employment_status

    cleaned: dict[str, list[str]] = {}
    for field, cap in _LIST_FIELDS.items():
        items = raw.get(field, [])
        if not isinstance(items, list):
            items = []
        out: list[str] = []
        for item in items:
            safe = _clean_item(item)
            if safe and safe not in out:
                out.append(safe)
            if len(out) >= cap:
                break
        cleaned[field] = out

    clarify = bool(raw.get("clarification_required", False))
    question = raw.get("clarifying_question")
    question = _clean_item(question) if question else None

    assessment = ResidentAssessment(
        employment_status=status,
        experience=cleaned["experience"],
        skills=cleaned["skills"],
        goals=cleaned["goals"],
        barriers=cleaned["barriers"],
        support_needs=cleaned["support_needs"],
        training_interests=cleaned["training_interests"],
        support_preferences=cleaned["support_preferences"],
        clarification_required=clarify,
        clarifying_question=question,
        provider="compatible",
    )
    if clarify and not assessment.clarifying_question:
        _apply_clarification(assessment)
    assessment.confidence = _coverage(assessment)
    assessment.disclaimers = _base_disclaimers() + [
        "An optional language model helped structure this summary; every item was checked against the resident's words."
    ]
    return assessment


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def assess(request: AssessmentRequest, settings: Settings) -> ResidentAssessment:
    """Produce a bounded structured assessment.

    Deterministic extraction is always computed as the safe baseline. If the
    optional provider is configured and returns a usable payload, the sanitised
    LLM result is returned instead; otherwise the deterministic result stands.
    """
    deterministic = _deterministic(request)

    if settings.llm_provider != "compatible":
        return deterministic

    raw = run_llm_assessment(request.text, request.profile.model_dump(), settings)
    if not raw:
        fallback = deterministic.model_copy(deep=True)
        fallback.disclaimers = deterministic.disclaimers + [
            "The optional language model was unavailable, so a local extractor produced this summary."
        ]
        return fallback

    sanitised = _sanitise_llm(raw, deterministic)
    return sanitised or deterministic
