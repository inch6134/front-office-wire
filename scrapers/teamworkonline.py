"""
TeamWork Online scraper.

TeamWork Online is a sports-industry-specific job board.
They paginate via query params: ?page=N

Job listings are returned as HTML cards. This scraper targets:
    https://www.teamworkonline.com/jobs-in-sports
"""
import logging
import re

from bs4 import BeautifulSoup

from .base import BaseScraper, Job
from utils.hashing import make_job_id
from utils.normalization import normalize_location

logger = logging.getLogger(__name__)

BASE_URL = "https://www.teamworkonline.com"
JOBS_URL = f"{BASE_URL}/jobs-in-sports"


class TeamWorkOnlineScraper(BaseScraper):
    def __init__(self, name: str, url: str, **kwargs):
        super().__init__(name, url, **kwargs)

    def fetch_jobs(self) -> list[Job]:
        logger.info("Fetching TeamWork Online jobs", extra={"source": self.name})
        jobs: list[Job] = []
        page = 1

        while True:
            params = {"page": page} if page > 1 else {}
            response = self.get(JOBS_URL, params=params)
            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select("li.jobs__list-item, div.job-listing, article.job")

            if not cards:
                # Try a broader selector on first page to detect structure changes
                if page == 1:
                    logger.warning(
                        "No job cards found on TeamWork Online; page structure may have changed",
                        extra={"source": self.name},
                    )
                break

            for card in cards:
                try:
                    job = self._parse_card(card)
                    if job:
                        jobs.append(job)
                except Exception as exc:
                    logger.warning(
                        "Failed to parse TeamWork Online card",
                        extra={"source": self.name, "error": str(exc)},
                    )

            # Stop if no next-page link
            next_link = soup.select_one("a[rel='next'], a.pagination__next")
            if not next_link:
                break
            page += 1
            if page > 25:  # hard cap
                break

        logger.info("Raw jobs fetched", extra={"source": self.name, "count": len(jobs)})
        return jobs

    def _parse_card(self, card) -> Job | None:
        link_el = card.select_one("a")
        if not link_el:
            return None

        href = link_el.get("href", "")
        job_url = href if href.startswith("http") else f"{BASE_URL}{href}"
        title_el = card.select_one("h2, h3, .job-title, .jobs__title")
        title = (title_el.get_text(strip=True) if title_el else link_el.get_text(strip=True))

        org_el = card.select_one(".organization, .company, .jobs__organization")
        organization = org_el.get_text(strip=True) if org_el else self.name

        loc_el = card.select_one(".location, .jobs__location")
        location = normalize_location(loc_el.get_text(strip=True) if loc_el else "")

        return Job(
            id=make_job_id(job_url),
            title=title,
            organization=organization,
            location=location,
            url=job_url,
            description="",
            posted_at=None,
            source="teamworkonline",
        )
