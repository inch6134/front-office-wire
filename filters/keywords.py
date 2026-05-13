"""
Keyword-based job filter.

Positive keywords:  job must match at least one
Negative keywords:  job is excluded if it matches any

Matching is against the job title (primary) and description (secondary).
All matching is case-insensitive.
"""
import logging
import re
from typing import Sequence

from scrapers.base import Job

logger = logging.getLogger(__name__)

DEFAULT_POSITIVE: list[str] = [
    "software engineer",
    "software developer",
    "data engineer",
    "analytics engineer",
    "analytics",
    "basketball systems",
    "baseball systems",
    "football systems",
    "hockey systems",
    "full stack",
    "fullstack",
    "frontend",
    "front end",
    "backend",
    "back end",
    "platform engineer",
    "site reliability",
    "infrastructure engineer",
    "systems developer",
    "systems engineer",
]

DEFAULT_NEGATIVE: list[str] = [
    "sales",
    "ticket",
    "marketing",
    "sponsorship",
    "social media",
    "intern athletic trainer",
    "athletic trainer",
    "physical therapist",
    "account executive",
    "account manager",
    "broadcast",
    "media relations",
    "community relations",
    "human resources",
    "facility",
    "food and beverage",
    "concessions",
    "game day",
    "gameday",
    "administrative assistant",
    "receptionist",
]


def _compile(keywords: Sequence[str]) -> list[re.Pattern]:
    return [re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE) for kw in keywords]


class JobFilter:
    def __init__(
        self,
        positive: list[str] | None = None,
        negative: list[str] | None = None,
    ):
        self._positive = _compile(positive if positive is not None else DEFAULT_POSITIVE)
        self._negative = _compile(negative if negative is not None else DEFAULT_NEGATIVE)

    def matches(self, job: Job) -> bool:
        text = f"{job.title} {job.description}"
        if any(p.search(text) for p in self._negative):
            return False
        return any(p.search(text) for p in self._positive)

    def filter(self, jobs: list[Job]) -> list[Job]:
        matched = [j for j in jobs if self.matches(j)]
        logger.info(
            "Keyword filter applied",
            extra={"total": len(jobs), "matched": len(matched), "dropped": len(jobs) - len(matched)},
        )
        return matched
