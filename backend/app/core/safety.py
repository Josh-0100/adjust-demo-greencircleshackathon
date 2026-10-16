import re

from fastapi import HTTPException

INJECTION_PATTERNS = [
    r"\bignore\s+(?:all\s+)?(?:previous|prior|system)\s+(?:instructions|prompts)",
    r"\b(?:reveal|print|expose|show)\s+(?:the\s+)?(?:system\s+prompt|api\s+key|secrets?|credentials?)",
    r"\b(?:system|developer)\s*(?:message|prompt)\s*:",
    r"<\|(?:im_start|system|assistant|developer)",
    r"\b(?:override|bypass)\s+(?:the\s+)?(?:safety|guardrails|instructions|policy)",
]


def check_text(value: str) -> str:
    if any(re.search(pattern, value, re.IGNORECASE) for pattern in INJECTION_PATTERNS):
        raise HTTPException(status_code=422, detail="This text includes instructions that could alter the AI workflow. Remove embedded instructions and submit factual information only.")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
        raise HTTPException(status_code=422, detail="Control characters are not accepted.")
    return value.strip()


def safe_excerpt(text: str, limit: int = 320) -> str:
    return " ".join(text.split())[:limit]

