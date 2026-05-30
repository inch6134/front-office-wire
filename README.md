# Front Office Wire

Automatically monitors software engineering, data engineering, and analytics job openings across professional sports organizations. Sends consolidated email notifications when new matching roles are posted.

## What it does

- Scrapes job boards across NBA, NFL, MLB, NHL, MLS teams and league offices
- Filters for software/data/analytics engineering roles using keyword matching
- Deduplicates using SQLite so you never receive the same job twice
- Sends a single email per run listing all new matches

## Supported ATS platforms

| Type | API | Notes |
|------|-----|-------|
| `greenhouse` | Public REST API | Preferred - most reliable |
| `lever` | Public REST API | Preferred |
| `workday` | URL-based API | Pagination handled automatically |
| `teamworkonline` | HTML scraping | Sports-specific aggregator |
| `generic` | HTML scraping | Fallback for unlisted ATS |

## Setup

### 1. Clone and install

```bash
git clone https://github.com/inch6134/front-office-wire
cd front-office-wire
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your email credentials
```

**SMTP (Gmail example):**

```
EMAIL_BACKEND=smtp
EMAIL_TO=you@example.com
EMAIL_FROM=you@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your_app_password   # Google App Password, not your login password
```

### 3. Run locally

```bash
python main.py
```

First run will create `front-office-wire.db` and send an email if any matching jobs are found. Subsequent runs skip already-seen jobs.

## Adding a new source

Open `config/sources.yaml` and add an entry:

**Greenhouse:**

```yaml
- name: Sacramento Kings
  type: greenhouse
  url: https://boards.greenhouse.io/sacramentokings
  params:
    token: sacramentokings
```

To find the token: open the team's careers page, view source, and search for `greenhouse.io`. The token is the slug in the URL.

**Lever:**

```yaml
- name: Seattle Sounders
  type: lever
  url: https://jobs.lever.co/soundersfc
  params:
    company: soundersfc
```

**Workday:**

```yaml
- name: New York Yankees
  type: workday
  url: https://yankees.wd5.myworkdayjobs.com/en-US/yankees_careers
```

The scraper auto-detects company, version, and jobboard from the URL.

**Generic HTML fallback:**

```yaml
- name: Some Team
  type: generic
  url: https://www.someteam.com/careers
```

## Adding a new scraper type

1. Create `scrapers/yourtype.py` extending `BaseScraper`
2. Implement `fetch_jobs(self) -> list[Job]`
3. Register it in `scrapers/registry.py`:

```python
from .yourtype import YourTypeScraper

_REGISTRY: dict[str, type[BaseScraper]] = {
    ...
    "yourtype": YourTypeScraper,
}
```

4. Add sources to `config/sources.yaml` with `type: yourtype`

## Modifying keyword filters

Edit `filters/keywords.py`. `DEFAULT_POSITIVE` and `DEFAULT_NEGATIVE` are plain lists of strings. Matching is case-insensitive word-boundary regex.

## GitHub Actions deployment

1. Push to GitHub
2. Add secrets under **Settings > Secrets and variables > Actions**:
   - All variables from `.env.example` (skip ones you don't use)
3. The workflow runs every 6 hours on a schedule
4. Trigger manually anytime from the **Actions** tab

The SQLite database is persisted between runs via Actions cache.

## Project structure

```
sports_jobs/
├── scrapers/
│   ├── base.py           # Job dataclass + BaseScraper + HTTP session
│   ├── greenhouse.py     # Greenhouse public API
│   ├── lever.py          # Lever public API
│   ├── workday.py        # Workday API
│   ├── teamworkonline.py # TeamWork Online HTML scraper
│   ├── generic.py        # Generic HTML fallback
│   └── registry.py       # Scraper factory
├── filters/
│   └── keywords.py       # Positive/negative keyword filtering
├── notifications/
│   ├── emailer.py        # SMTP sending
│   └── templates.py      # Plain text + HTML email templates
├── database/
│   ├── db.py             # SQLite operations
│   └── schema.sql        # Table definitions
├── config/
│   └── sources.yaml      # All job sources
├── utils/
│   ├── hashing.py        # Job ID generation
│   ├── logging.py        # JSON + text structured logging
│   └── normalization.py  # Field cleanup helpers
├── main.py               # Entry point
├── requirements.txt
├── .env.example
└── .github/workflows/jobs.yml
```

## Environment variables reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMAIL_BACKEND` | No | `smtp` | `smtp` |
| `EMAIL_TO` | Yes | - | Notification recipient |
| `EMAIL_FROM` | Yes | - | Sender address |
| `SMTP_HOST` | Yes | - | e.g. `smtp.gmail.com` |
| `SMTP_PORT` | Yes | `587` | |
| `SMTP_USER` | Yes | - | |
| `SMTP_PASSWORD` | Yes | - | App password for Gmail |
| `SOURCES_CONFIG` | No | `config/sources.yaml` | |
| `DB_PATH` | No | `front_office_wire.db` | |
| `LOG_LEVEL` | No | `INFO` | `DEBUG/INFO/WARNING/ERROR` |
| `LOG_FORMAT` | No | `text` | `text` or `json` |
