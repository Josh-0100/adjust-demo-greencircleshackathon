"""Module-local input safety.

Kept inside the module so Bolton Connect validates untrusted text the same way
whether it runs standalone or inside the CivicForge core. Mirrors the core
`check_text` contract (prompt-injection + control-character screening) without
importing shared code, preserving independence.
"""
from __future__ import annotations

import re

INJECTION_PATTERNS = [
    r"\bignore\s+(?:all\s+)?(?:previous|prior|system)\s+(?:instructions|prompts)",
    r"\b(?:reveal|print|expose|show)\s+(?:the\s+)?(?:system\s+prompt|api\s+key|secrets?|credentials?)",
    r"\b(?:system|developer)\s*(?:message|prompt)\s*:",
    r"<\|(?:im_start|system|assistant|developer)",
    r"\b(?:override|bypass)\s+(?:the\s+)?(?:safety|guardrails|instructions|policy)",
]


class UnsafeTextError(ValueError):
    """Raised when text contains embedded instructions or control characters.

    Route handlers translate this into HTTP 422; the core package stays free of
    any web-framework dependency.
    """


def check_text(value: str) -> str:
    if any(re.search(pattern, value, re.IGNORECASE) for pattern in INJECTION_PATTERNS):
        raise UnsafeTextError(
            "This text includes instructions that could alter the AI workflow. "
            "Remove embedded instructions and submit factual information only."
        )
    if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
        raise UnsafeTextError("Control characters are not accepted.")
    return value.strip()


def safe_excerpt(text: str, limit: int = 320) -> str:
    return " ".join(text.split())[:limit]
