CREATE TABLE IF NOT EXISTS jobs (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    organization TEXT NOT NULL,
    url          TEXT NOT NULL,
    first_seen   TIMESTAMP NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_jobs_first_seen ON jobs(first_seen);
