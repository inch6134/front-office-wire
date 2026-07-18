import logging
from typing import Any

from .base import BaseScraper, Job
from utils.hashing import make_job_id
from utils.normalization import normalize_location

logger = logging.getLogger(__name__)

LEVER_API = "https://api.lever.co/v0/postings/{company}"


class LeverScraper(BaseScraper):
    def __init__(self, name: str, url: str, company: str, **kwargs):
        super().__init__(name, url, **kwargs)
        self.company = company

    def fetch_jobs(self) -> list[Job]:
        api_url = LEVER_API.format(company=self.company)
        logger.info("Fetching Lever jobs", extra={"source": self.name, "url": api_url})

        raw_jobs: list[dict[str, Any]] = self.get(
            api_url, params={"mode": "json"}
        ).json()
        logger.info("Raw jobs fetched", extra={"count": len(raw_jobs)})

        jobs = []
        for raw in raw_jobs:
            try:
                jobs.append(self._parse(raw))
            except Exception as exc:
                logger.warning(
                    "Failed to parse Lever job",
                    extra={
                        "job": raw.get("id"),
                        "error": str(exc),
                    },
                )
        return jobs

    def _parse(self, raw: dict[str, Any]) -> Job:
        job_url = raw.get("hostedUrl", raw.get("applyUrl", ""))
        categories = raw.get("categories", {})
        location = normalize_location(categories.get("location", ""))

        lists = raw.get("lists", [])
        description_parts = [item.get("content", "") for item in lists]
        description = " ".join(description_parts)[:500]

        return Job(
            id=make_job_id(job_url or raw.get("id", "")),
            title=raw.get("text", "").strip(),
            organization=self.name,
            location=location,
            url=job_url,
            description=description,
            posted_at=str(raw["createdAt"]) if raw.get("createdAt") else None,
            source="lever",
        )
