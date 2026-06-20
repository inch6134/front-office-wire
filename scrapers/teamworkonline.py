"""
TeamWork Online scraper.

TeamWork Online is a sports-industry-specific job board.

Team-specific:
    https://www.teamworkonline.com/baseball-jobs/orioles-jobs/baltimore-orioles-jobs

In sport-level mode, each job card includes the organization name.
In team-specific mode, self.name is used as the organization fallback.
"""
import logging

from bs4 import BeautifulSoup

from .base import BaseScraper, Job
from utils.hashing import make_job_id
from utils.normalization import normalize_location

logger = logging.getLogger(__name__)

BASE_URL = "https://www.teamworkonline.com"
MAX_PAGES = 50


class TeamWorkOnlineScraper(BaseScraper):
    def __init__(self, name: str, url: str, **kwargs):
        super().__init__(name, url, **kwargs)

    def fetch_jobs(self) -> list[Job]:
        logger.info(
            "Fetching TeamWork Online jobs",
            extra={"source": self.name, "url": self.url},
        )
        jobs: list[Job] = []
        page = 1

        while True:
            params = {"page": page} if page > 1 else {}
            response = self.get(self.url, params=params)
            soup = BeautifulSoup(response.text, "html.parser")

            cards = (
                soup.select("li.jobs__list-item")
                or soup.select("div.job-listing")
                or soup.select("article.job")
                or soup.select("li[class*='job']")
            )

            if not cards:
                if page == 1:
                    logger.warning(
                        "No job cards found; TeamWork Online page structure may have changed",
                        extra={"source": self.name, "url": self.url},
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

            next_link = soup.select_one("a[rel='next'], a.pagination__next, .next a")
            if not next_link:
                break
            page += 1
            if page > MAX_PAGES:
                logger.warning("Hit page cap", extra={"source": self.name, "pages": MAX_PAGES})
                break

        logger.info("Raw jobs fetched", extra={"source": self.name, "count": len(jobs)})
        return jobs

    def _parse_card(self, card) -> Job | None:
        link_el = card.select_one("a")
        if not link_el:
            return None

        href = link_el.get("href", "")
        if not href or href == "#":
            return None

        job_url = href if href.startswith("http") else f"{BASE_URL}{href}"

        title_el = (
            card.select_one("h2")
            or card.select_one("h3")
            or card.select_one(".jobs__title")
            or card.select_one(".job-title")
        )
        title = title_el.get_text(strip=True) if title_el else link_el.get_text(strip=True)

        org_el = (
            card.select_one(".jobs__organization")
            or card.select_one(".organization")
            or card.select_one(".company")
        )
        organization = org_el.get_text(strip=True) if org_el else self.name

        loc_el = (
            card.select_one(".jobs__location")
            or card.select_one(".location")
            or card.select_one("[class*='location']")
        )
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
