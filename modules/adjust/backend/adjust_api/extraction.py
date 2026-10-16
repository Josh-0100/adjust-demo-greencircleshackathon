import re

from .models import AnalyseRequest, Analysis, Question
from .safety import normalise

# Topics describe work demands, never diagnoses or eligibility.
TOPICS = {
    "manual": r"\b(?:lift\w*|carrying|carry|manual handling|pushing|pulling|loads?)\b",
    "desk": r"\b(?:desk|screen|computer|workstation|keyboard|sitting|seated)\b",
    "stress": r"\b(?:anxiet\w*|anxious|stress\w*|overwhelm\w*|panic|workload|deadlines?)\b",
    "sensory": r"\b(?:noise|noisy|bright|lighting|sensory|distractions?)\b",
    "communication": r"\b(?:hearing|deaf|communication|phone calls?|instructions?)\b",
    "mobility": r"\b(?:stairs|walking|standing|wheelchair|mobility|step-free)\b",
    "fatigue": r"\b(?:fatigue|tired\w*|exhaust\w*|energy|breaks?)\b",
    "concentration": r"\b(?:concentrat\w*|focus\w*|memory|remember\w*)\b",
}
TASKS = [
    ("lifting", r"\b(?:lift\w*|manual handling)\b"), ("picking", r"\bpick\w*\b"),
    ("carrying", r"\b(?:carry\w*|carrying)\b"), ("packing", r"\bpack\w*\b"),
    ("computer work", r"\b(?:computer|screen|keyboard|data entry)\b"),
    ("customer calls", r"\b(?:calls?|telephone|phone)\b"),
    ("meetings", r"\bmeetings?\b"), ("standing", r"\bstanding\b"),
    ("walking", r"\bwalking\b"), ("driving", r"\bdriv(?:e|ing)\b"),
    ("reading instructions", r"\b(?:reading|instructions?)\b"),
    ("meeting deadlines", r"\bdeadlines?\b"),
    ("diving", r"\bdiving\b"),
]
ROLE = re.compile(r"\b(warehouse (?:picker|worker|operative)s?|office (?:employee|worker|administrator)s?|administrators?|receptionists?|drivers?|cleaners?|retail (?:assistant|worker)s?|customer service (?:adviser|advisor|agent)s?|nurses?|engineers?|teachers?|chefs?|kitchen (?:worker|assistant)s?)\b", re.I)
BARRIER = re.compile(r"\b(?:struggl\w*|difficult\w*|cannot|can't|unable|hard to|pain\w*|anxiet\w*|anxious|overwhelm\w*|fatigue|tired|distress\w*|stress\w*|barriers?|discomfort|distract\w*|hard of hearing)\b", re.I)
LIMITATION = re.compile(r"\b(?:pain|anxiet\w*|anxious|fatigue|exhaustion|discomfort|hard of hearing|limited mobility)\b", re.I)


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]


def positive_mention(match: re.Match, text: str) -> bool:
    """Handle simple explicit negation; this is not general language understanding."""
    prefix = normalise(text[max(0, match.start() - 60):match.start()])
    prefix = re.split(r"\b(?:but|however|although)\b|[.;\n]", prefix)[-1]
    # 'not able to lift' is a relevant demand, not absence of a lifting task.
    if re.search(r"\bnot (?:able|easy|possible) to\s*$", prefix):
        return True
    return not re.search(r"\b(?:no|without|denies?|not|doesn't|isn't)\s+(?:\w+\s+){0,3}$", prefix)


def extract(request: AnalyseRequest) -> Analysis:
    # Employer constraints are kept separate so 'no budget for a lifting aid'
    # cannot create a reported lifting barrier.
    text = "\n".join([request.description, request.role, request.answers.role,
                       request.answers.tasks, request.answers.barriers])
    lowered = normalise(text)
    role_match = ROLE.search(text)
    role = request.answers.role or request.role or (role_match.group(0) if role_match else None)
    tasks = [label for label, pattern in TASKS if re.search(pattern, lowered)]
    if request.answers.tasks:
        tasks = list(dict.fromkeys(tasks + [request.answers.tasks]))
    barriers = [s for s in sentences(request.description)
                if any(positive_mention(m, s) for m in BARRIER.finditer(s))][:5]
    if request.answers.barriers:
        barriers = [request.answers.barriers] + barriers[:4]
    limitations = list(dict.fromkeys(m.group(0) for m in LIMITATION.finditer(text) if positive_mention(m, text)))
    constraints = [s for s in [request.constraints, request.answers.constraints] if s]
    constraints += [s for s in sentences(request.description)
                    if re.search(r"\b(?:budget|cannot afford|can't afford|limited space|small team|no spare|no dedicated|tight space)\b", normalise(s))]
    missing = []
    if not role:
        missing.append("role")
    if not tasks:
        missing.append("tasks")
    if not barriers:
        missing.append("barriers")
    scenarios = [name for name, pattern in TOPICS.items()
                 if any(positive_mention(m, lowered) for m in re.finditer(pattern, lowered))] if barriers else []
    return Analysis(role=role, tasks=tasks, barriers=barriers, reported_limitations=limitations,
                    constraints=list(dict.fromkeys(constraints)), missing_information=missing,
                    clarification_required=bool(missing), scenarios=scenarios)


def questions_for(analysis: Analysis) -> list[Question]:
    questions = {
        "role": Question(id="role", question="What is the employee's job role?", hint="A job title is enough. Leave out names.", required=True),
        "tasks": Question(id="tasks", question="Which tasks are part of their work?", hint="For example: moving stock, computer work, customer calls.", required=True),
        "barriers": Question(id="barriers", question="Which parts of the work are difficult?", hint="Describe the task or environment and what gets in the way. No diagnosis is needed.", required=True),
    }
    required = [questions[id_] for id_ in analysis.missing_information]
    if not analysis.constraints:
        required.append(Question(id="constraints", question="Are there practical constraints to consider?", hint="Optional: team cover, space, working patterns or budget."))
    required.append(Question(id="employee_view", question="What has the employee said would help?", hint="Optional. It is fine if you have not discussed this yet."))
    return required
