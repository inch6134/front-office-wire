import logging
import re
from typing import Any

from .base import BaseScraper, Job
from utils.hashing import make_job_id
from utils.normalization import normalize_location

logger = logging.getLogger(__name__)

# company.wd5.myworkdayjobs.com/[locale/]jobboard
_JOBS_RE = re.compile(
    r"https?://(?P<company>[^.]+)\.(?P<version>wd\d+)\.myworkdayjobs\.com"
    r"(?:/[^/]+)?/(?P<jobboard>[^/?#]+)"
)

# wd1.myworkdaysite.com/[locale/]recruiting/company/jobboard
_SITE_RE = re.compile(
    r"https?://(?P<version>wd\d+)\.myworkdaysite\.com"
    r"(?:/[^/]+)?/recruiting/(?P<company>[^/?#]+)/(?P<jobboard>[^/?#]+)"
)


def _parse_url(url: str) -> tuple[str, str, str]:
    m = _JOBS_RE.match(url)
    if m:
        company = m.group("company")
        version = m.group("version")
        jobboard = m.group("jobboard")
        host = f"{company}.{version}.myworkdayjobs.com"
        return host, company, jobboard

    m = _SITE_RE.match(url)
    if m:
        version = m.group("version")
        company = m.group("company")
        jobboard = m.group("jobboard")
        host = f"{version}.myworkdaysite.com"
        return host, company, jobboard

    raise ValueError(f"Unrecognized Workday URL structure: {url}")


class WorkdayScraper(BaseScraper):
    def __init__(self, name: str, url: str, **kwargs):
        super().__init__(name, url, **kwargs)
        params = kwargs.get("params", {})

        if params.get("company") and params.get("jobboard"):
            company = params["company"]
            jobboard = params["jobboard"]
            version = params.get("version", "wd5")
            # Determine host: if url contains myworkdaysite, use that pattern
            if "myworkdaysite.com" in url:
                m = _SITE_RE.match(url)
                host = (
                    f"{m.group('version')}.myworkdaysite.com"
                    if m
                    else f"{version}.myworkdaysite.com"
                )
            else:
                host = f"{company}.{version}.myworkdayjobs.com"
        else:
            host, company, jobboard = _parse_url(url)

        self.api_url = f"https://{host}/wday/cxs/{company}/{jobboard}/jobs"
        m = _JOBS_RE.match(url)
        if m:
            self._job_url_base = f"https://{host}/en-US/{jobboard}"
        else:
            self._job_url_base = f"https://{host}/recruiting/{company}/{jobboard}"

    def fetch_jobs(self) -> list[Job]:
        logger.info(
            "Fetching Workday jobs", extra={"source": self.name, "url": self.api_url}
        )

        payload: dict[str, Any] = {
            "limit": 20,
            "offset": 0,
            "searchText": "",
            "appliedFacets": {},
        }
        all_postings: list[dict[str, Any]] = []
        offset = 0

        while True:
            payload["offset"] = offset
            data = self.post(self.api_url, json=payload).json()
            postings = data.get("jobPostings", [])
            all_postings.extend(postings)
            total = data.get("total", 0)
            offset += len(postings)
            if not postings or offset >= total:
                break

        logger.info("Raw jobs fetched", extra={"count": len(all_postings)})

        jobs = []
        for raw in all_postings:
            try:
                jobs.append(self._parse(raw))
            except Exception as exc:
                logger.warning(
                    "Failed to parse Workday job",
                    extra={"error": str(exc)},
                )
        return jobs

    def _parse(self, raw: dict[str, Any]) -> Job:
        path = raw.get("externalPath", "")
        job_url = f"{self._job_url_base}{path}" if path else self._job_url_base

        locations = raw.get("locationsText", raw.get("locations", ""))
        if isinstance(locations, list):
            location = normalize_location(", ".join(locations))
        else:
            location = normalize_location(str(locations))

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
