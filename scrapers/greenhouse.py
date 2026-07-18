import logging
from typing import Any

from .base import BaseScraper, Job
from utils.hashing import make_job_id
from utils.normalization import normalize_location

logger = logging.getLogger(__name__)

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"


class GreenhouseScraper(BaseScraper):
    def __init__(self, name: str, url: str, token: str, **kwargs):
        super().__init__(name, url, **kwargs)
        self.token = token

    def fetch_jobs(self) -> list[Job]:
        api_url = GREENHOUSE_API.format(token=self.token)
        logger.info(
            "Fetching Greenhouse jobs", extra={"source": self.name, "url": api_url}
        )

        data = self.get(api_url, params={"content": "true"}).json()
        raw_jobs: list[dict[str, Any]] = data.get("jobs", [])
        logger.info("Raw jobs fetched", extra={"count": len(raw_jobs)})

        jobs = []
        for raw in raw_jobs:
            try:
                jobs.append(self._parse(raw))
            except Exception as exc:
                logger.warning(
                    "Failed to parse Greenhouse job",
                    extra={
                        "job": raw.get("id"),
                        "error": str(exc),
                    },
                )
        return jobs

    def _parse(self, raw: dict[str, Any]) -> Job:
        job_id = str(raw["id"])
        title = raw.get("title", "").strip()
        job_url = raw.get("absolute_url", "")

        offices = raw.get("offices", [])
        location = normalize_location(
            offices[0].get("name", "")
            if offices
            else raw.get("location", {}).get("name", "")
        )

        description = ""
        content = raw.get("content", "")
        if content:
            # content is HTML; strip for storage, keep full for display
            description = content[:500]

        return Job(
            id=make_job_id(job_url or job_id),
            title=title,
            organization=self.name,
            location=location,
            url=job_url,
            description=description,
            posted_at=raw.get("updated_at"),
            source="greenhouse",
        )
