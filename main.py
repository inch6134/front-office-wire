import logging
import os
import sys
import argparse
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()

from utils.logging import setup_logging
from scrapers.registry import get_scraper
from filters.keywords import JobFilter
from database.db import JobDatabase
from notifications.emailer import send_notifications

setup_logging()
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument(
    "--source",
    nargs="+",
    help="Scrape only the specified source. May be provided multiple times.",
)
parser.add_argument(
    "--level",
    default="INFO",
    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    help="Set log level. Options include: DEBUG | INFO | WARNING | ERROR",
)
parser.add_argument(
    "--format",
    default="TEXT",
    choices=["TEXT", "JSON"],
    help="Set log format. Options include: TEXT | JSON",
)


def load_sources(config_path: Path, args: argparse.Namespace) -> list[dict]:
    with config_path.open() as f:
        sources = yaml.safe_load(f).get("sources", [])
        sources = [
            source
            for source in sources
            if not args.source or source["name"] in args.source
        ]
        return sources


def run() -> None:
    config_path = Path(os.getenv("SOURCES_CONFIG", "config/sources.yaml"))
    db_path = Path(os.getenv("DB_PATH", "front_office_wire.db"))
    args = parser.parse_args()

    sources = load_sources(config_path, args)
    if args.level or args.format:
        setup_logging(args.level, args.format)

    job_filter = JobFilter()

    all_new_jobs = []

    with JobDatabase(db_path) as db:
        for source in sources:
            name = source.get("name", "unknown")
            try:
                scraper = get_scraper(source)
                raw_jobs = scraper.fetch_jobs()

                filtered = job_filter.filter(raw_jobs)
                new_jobs = db.filter_new(filtered)

                if new_jobs:
                    db.mark_seen_bulk(new_jobs)
                    all_new_jobs.extend(new_jobs)
                    logger.info(
                        "New jobs found",
                        extra={"count": len(new_jobs)},
                    )
                else:
                    logger.info(
                        "No new jobs",
                    )

            except Exception as exc:
                logger.error(
                    "Scraper failed",
                    extra={"source": name, "error": str(exc)},
                    exc_info=True,
                )
                # Continue to next source; do not crash the run

    if all_new_jobs:
        logger.info("Sending notification", extra={"total_new_jobs": len(all_new_jobs)})
        send_notifications(all_new_jobs)
    else:
        logger.info("Run complete - no new jobs to notify about")


if __name__ == "__main__":
    run()
