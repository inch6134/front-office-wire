"""
Workday scraper using the Workday URL pattern

Workday career page URLs follow the pattern:
    https://{company}.wd{n}.myworkdayjobs.com/en-US/{jobboard}

The API endpoint:
    POST https://{company}.wd{n}.myworkdayjobs.com/wday/cxs/{company}/{jobboard}/jobs

Source config requires either:
  - params.company + params.jobboard + params.version  (explicit)
  - or a parseable URL (auto-detected)
"""
import logging
import re
from typing import Any

from .base import BaseScraper, Job
from utils.hashing import make_job_id
from utils.normalization import normalize_location

logger = logging.getLogger(__name__)

_URL_RE = re.compile(
    r"https?://(?P<company>[^.]+)\.(?P<version>wd\d+)\.myworkdayjobs\.com"
    r"(?:/[^/]+)?/(?P<jobboard>[^/?#]+)"
)


class WorkdayScraper(BaseScraper):
    def __init__(self, name: str, url: str, **kwargs):
        super().__init__(name, url, **kwargs)
        params = kwargs.get("params", {})

        company = params.get("company")
        jobboard = params.get("jobboard")
        version = params.get("version", "wd5")

        if not (company and jobboard):
            m = _URL_RE.match(url)
            if not m:
                raise ValueError(f"Cannot parse Workday URL: {url}")
            company = m.group("company")
            version = m.group("version")
            jobboard = m.group("jobboard")

        self.api_url = (
            f"https://{company}.{version}.myworkdayjobs.com"
            f"/wday/cxs/{company}/{jobboard}/jobs"
        )

    def fetch_jobs(self) -> list[Job]:
        logger.info("Fetching Workday jobs", extra={"source": self.name, "url": self.api_url})

        payload = {"limit": 20, "offset": 0, "searchText": "", "appliedFacets": {}}
        all_jobs: list[dict[str, Any]] = []
        offset = 0

        while True:
            payload["offset"] = offset
            data = self.post(self.api_url, json=payload).json()
            postings = data.get("jobPostings", [])
            all_jobs.extend(postings)
            total = data.get("total", 0)
            offset += len(postings)
            if offset >= total or not postings:
                break

        logger.info("Raw jobs fetched", extra={"source": self.name, "count": len(all_jobs)})

        base = self.api_url.split("/wday/")[0]
        jobs = []
        for raw in all_jobs:
            try:
                jobs.append(self._parse(raw, base))
            except Exception as exc:
                logger.warning(
                    "Failed to parse Workday job",
                    extra={"source": self.name, "error": str(exc)},
                )
        return jobs

    def _parse(self, raw: dict[str, Any], base_url: str) -> Job:
        path = raw.get("externalPath", "")
        job_url = f"{base_url}{path}" if path else base_url
        location_nodes = raw.get("locationsText", raw.get("locations", ""))
        if isinstance(location_nodes, list):
            location = normalize_location(", ".join(location_nodes))
        else:
            location = normalize_location(str(location_nodes))

        return Job(
            id=make_job_id(job_url),
            title=raw.get("title", "").strip(),
            organization=self.name,
            location=location,
            url=job_url,
            description=raw.get("jobDescription", "")[:500],
            posted_at=raw.get("postedOn"),
            source="workday",
        )
