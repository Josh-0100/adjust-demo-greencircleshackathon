import re
import unicodedata

from .models import AnalyseRequest, Safety

NHS_URGENT = "https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/"


def normalise(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold().replace("’", "'")


def input_text(request: AnalyseRequest) -> str:
    return "\n".join([request.description, request.role, request.constraints,
                      *request.answers.model_dump().values()])


def safety_check(text: str) -> Safety:
    text = normalise(text)
    # High-recall prototype rules, not clinical triage. Only explicit negations of
    # danger are removed; a generic 'not' must never hide 'not breathing'.
    text = re.sub(r"\b(?:no|not in|without) immediate danger\b", "", text)
    text = re.sub(r"\bno (?:current )?(?:suicidal thoughts|self[- ]harm|risk of harm)\b", "", text)
    emergency = [r"\bimmediate (?:danger|risk of harm)\b", r"\bnot breathing\b", r"\b(?:can't|cannot|unable to) breathe\b", r"\bunconscious\b",
                 r"\b(?:cannot|can't|unable to) (?:keep .*?safe|stay safe)\b",
                 r"\b(?:kill|killing|hurt|harming) (?:myself|himself|herself|themselves)\b",
                 r"\b(?:suicid\w*|overdose\w*|severe bleeding)\b", r"\b(?:trapped|crushed) (?:in|under|by)\b",
                 r"\b(?:wants?|plans?|threatens?) to (?:die|end (?:their|his|her|my) life)\b",
                 r"\b(?:gas leak|uncontrolled fire|electric shock)\b"]
    if any(re.search(pattern, text) for pattern in emergency):
        return Safety(level="emergency", title="Pause. Immediate safety comes first.",
                      message="If someone is in immediate danger, their life is at risk, or you cannot keep them safe, call 999 or go to A&E now.",
                      actions=["Use your workplace emergency procedure and seek immediate professional help.",
                               "Do not use an adjustment plan to assess whether someone is safe or fit for work."],
                      official_url=NHS_URGENT)
    if re.search(r"\b(?:mental health crisis|urgent mental health|self[- ]harm|panic attack right now)\b", text):
        return Safety(level="urgent", title="Get urgent professional support first",
                      message="For urgent mental health help in England, call NHS 111 and select the mental health option, or seek an urgent GP appointment. If life is at risk or someone cannot be kept safe, call 999.",
                      actions=["Pause the normal adjustment workflow until immediate support needs are addressed."], official_url=NHS_URGENT)
    return Safety()
