import logging

from bs4 import BeautifulSoup

from .base import BaseScraper, Job
from utils.hashing import make_job_id
from utils.normalization import normalize_location

logger = logging.getLogger(__name__)

DEFAULT_JOB_SELECTORS = [
    "li.job-listing",
    "div.job-listing",
    "tr.job",
    "article.job",
    ".careers-list li",
    ".job-results li",
    ".position-list li",
    "table.jobs tbody tr",
]

DEFAULT_LINK_SELECTORS = ["a.job-link", "a.position-link", "h2 a", "h3 a", "td a", "a"]


class GenericScraper(BaseScraper):
    def __init__(self, name: str, url: str, **kwargs):
        super().__init__(name, url, **kwargs)
        params = kwargs.get("params", {})
        self.selectors: list[str] = params.get("selectors", DEFAULT_JOB_SELECTORS)
        self.base_url = self._derive_base(url)

    def _derive_base(self, url: str) -> str:
        from urllib.parse import urlparse

        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"

    def fetch_jobs(self) -> list[Job]:
        logger.info(
            "Fetching generic HTML jobs", extra={"source": self.name, "url": self.url}
        )
        response = self.get(self.url)
        logger.info(
            "Generic page fetched",
            extra={
                "status": response.status_code,
                "content_length": len(response.text),
            },
        )
        soup = BeautifulSoup(response.text, "html.parser")

        cards = []
        for selector in self.selectors:
            cards = soup.select(selector)
            if cards:
                break

        if not cards:
            logger.warning(
                "No job cards found with generic scraper",
            )
            return []

        jobs: list[Job] = []
        for card in cards:
            try:
                job = self._parse_card(card)
                if job:
                    jobs.append(job)
            except Exception as exc:
                logger.warning(
                    "Failed to parse generic card",
                    extra={"error": str(exc)},
                )

        logger.info("Raw jobs fetched", extra={"count": len(jobs)})
        return jobs

    def _parse_card(self, card) -> Job | None:
        link_el = None
        for sel in DEFAULT_LINK_SELECTORS:
            link_el = card.select_one(sel)
            if link_el:
                break

        if not link_el:
            return None

        href = link_el.get("href", "")
        if not href or href == "#":
            return None

        job_url = href if href.startswith("http") else f"{self.base_url}{href}"
        title = link_el.get_text(strip=True)

        loc_el = card.select_one(".location, [class*='location'], [class*='city']")
        location = normalize_location(loc_el.get_text(strip=True) if loc_el else "")

        return Job(
            id=make_job_id(job_url),
            title=title,
            organization=self.name,
            location=location,
            url=job_url,
            description="",
            posted_at=None,
            source="generic",
        )
