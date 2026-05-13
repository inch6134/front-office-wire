"""
SQLite persistence layer.

Single responsibility: track which job IDs have been seen so we never
send duplicate notifications.
"""
import logging
import sqlite3
from pathlib import Path

from scrapers.base import Job

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path("front_office_wire.db")


class JobDatabase:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        schema = Path(__file__).parent / "schema.sql"
        self._conn.executescript(schema.read_text())
        self._conn.commit()

    def is_seen(self, job_id: str) -> bool:
        cur = self._conn.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,))
        return cur.fetchone() is not None

    def mark_seen(self, job: Job) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO jobs (id, title, organization, url, first_seen)
            VALUES (?, ?, ?, ?, datetime('now'))
            """,
            (job.id, job.title, job.organization, job.url),
        )
        self._conn.commit()

    def filter_new(self, jobs: list[Job]) -> list[Job]:
        """Return only jobs not yet in the database."""
        new = [j for j in jobs if not self.is_seen(j.id)]
        logger.info(
            "Deduplication applied",
            extra={"total": len(jobs), "new": len(new), "seen": len(jobs) - len(new)},
        )
        return new

    def mark_seen_bulk(self, jobs: list[Job]) -> None:
        for job in jobs:
            self.mark_seen(job)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
