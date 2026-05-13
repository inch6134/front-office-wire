"""
Light normalization helpers for job fields.
Keeps scrapers clean by centralizing string cleanup here.
"""
import re

_WHITESPACE_RE = re.compile(r"\s+")
_REMOTE_RE = re.compile(r"\bremote\b", re.IGNORECASE)


def normalize_location(raw: str) -> str:
    if not raw:
        return ""
    cleaned = _WHITESPACE_RE.sub(" ", raw).strip()
    # Normalize "Remote, US" -> "Remote"
    if _REMOTE_RE.search(cleaned) and len(cleaned) > 10:
        return "Remote"
    return cleaned


def normalize_title(raw: str) -> str:
    return _WHITESPACE_RE.sub(" ", raw).strip()
