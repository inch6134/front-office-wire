import logging

from bs4 import BeautifulSoup

from .base import BaseScraper, Job
from utils.hashing import make_job_id
from utils.normalization import normalize_location

logger = logging.getLogger(__name__)

BASE_URL = "https://www.teamworkonline.com"
MAX_PAGES = 50


class TeamWorkOnlineScraper(BaseScraper):
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
            logger.info(
                "TeamWork Online page fetched",
                extra={
                    "source": self.name,
                    "page": page,
                    "status": response.status_code,
                    "content_length": len(response.text),
                },
            )
            soup = BeautifulSoup(response.text, "html.parser")

            cards = soup.select("div.organization-portal__job")

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

            next_link = soup.select_one("a[rel='next']")
            if not next_link:
                break
            page += 1
            if page > MAX_PAGES:
                logger.warning(
                    "Hit page cap", extra={"source": self.name, "pages": MAX_PAGES}
                )
                break

        logger.info("Raw jobs fetched", extra={"source": self.name, "count": len(jobs)})
        return jobs

    def _parse_card(self, card) -> Job | None:
        title_el = card.select_one("h3.organization-portal__job-title a")
        href = title_el.get("href", "")
        job_url = href if href.startswith("http") else f"{BASE_URL}{href}"
        title = title_el.get_text(strip=True)

        org_el = card.select_one("p.organization-portal__job-category")
        organization = org_el.get_text(strip=True) if org_el else self.name

        loc_el = card.select_one("p.organization-portal__job-location")
        raw_location = (
            loc_el.get_text(strip=True).replace(" · ", ", ") if loc_el else ""
        )
        location = normalize_location(raw_location)

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
