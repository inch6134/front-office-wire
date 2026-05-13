"""
Email templates for job notification emails.
Renders both plain-text and HTML versions from the same job list.
"""
from scrapers.base import Job


def render_text(jobs: list[Job]) -> str:
    lines = [
        f"New Sports Tech Jobs ({len(jobs)})",
        "=" * 40,
        "",
    ]
    for job in jobs:
        lines += [
            f"{job.organization} - {job.title}",
            f"Location: {job.location or 'Not specified'}",
            f"Link: {job.url}",
            "",
        ]
    lines.append("---")
    lines.append("You are receiving this because you subscribed to sports tech job alerts.")
    return "\n".join(lines)


def render_html(jobs: list[Job]) -> str:
    job_rows = "\n".join(_job_block(job) for job in jobs)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>New Sports Tech Jobs</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #f5f5f5; margin: 0; padding: 24px; color: #111; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #fff;
                  border-radius: 8px; padding: 32px; }}
    h1 {{ font-size: 20px; margin: 0 0 24px; }}
    .job {{ border-left: 3px solid #0057b8; padding: 12px 16px;
             margin-bottom: 16px; background: #f9f9f9; border-radius: 0 4px 4px 0; }}
    .job-title {{ font-size: 16px; font-weight: 600; margin: 0 0 4px; }}
    .job-org {{ font-size: 13px; color: #555; margin: 0 0 4px; }}
    .job-location {{ font-size: 13px; color: #555; margin: 0 0 8px; }}
    .apply-link {{ display: inline-block; font-size: 13px; color: #0057b8;
                   text-decoration: none; font-weight: 500; }}
    .apply-link:hover {{ text-decoration: underline; }}
    .footer {{ margin-top: 32px; font-size: 12px; color: #999; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>New Sports Tech Jobs ({len(jobs)})</h1>
    {job_rows}
    <div class="footer">
      You are receiving this because you subscribed to sports tech job alerts.
    </div>
  </div>
</body>
</html>"""


def _job_block(job: Job) -> str:
    location = job.location or "Location not specified"
    return f"""    <div class="job">
      <div class="job-title">{_escape(job.title)}</div>
      <div class="job-org">{_escape(job.organization)}</div>
      <div class="job-location">{_escape(location)}</div>
      <a class="apply-link" href="{_escape(job.url)}" target="_blank">Apply &rarr;</a>
    </div>"""


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )
