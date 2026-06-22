"""
Scraper registry.

Maps source `type` strings from sources.yaml to scraper classes.
Instantiates scrapers from raw config dicts.
"""

import logging
from typing import Any

from .base import BaseScraper
from .greenhouse import GreenhouseScraper
from .lever import LeverScraper
from .workday import WorkdayScraper
from .teamworkonline import TeamWorkOnlineScraper
from .generic import GenericScraper

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, type[BaseScraper]] = {
    "greenhouse": GreenhouseScraper,
    "lever": LeverScraper,
    "workday": WorkdayScraper,
    "teamworkonline": TeamWorkOnlineScraper,
    "generic": GenericScraper,
}


def get_scraper(source: dict[str, Any]) -> BaseScraper:
    """Instantiate a scraper from a sources.yaml entry."""
    source_type = source.get("type", "generic").lower()
    cls = _REGISTRY.get(source_type)
    if cls is None:
        raise ValueError(
            f"Unknown scraper type: {source_type!r}. Valid types: {list(_REGISTRY)}"
        )

    name = source["name"]
    url = source["url"]
    params = source.get("params", {})

    kwargs: dict[str, Any] = {"params": params}

    if source_type == "greenhouse":
        token = params.get("token")
        if not token:
            raise ValueError(f"Greenhouse source {name!r} requires params.token")
        kwargs["token"] = token
    elif source_type == "lever":
        company = params.get("company")
        if not company:
            raise ValueError(f"Lever source {name!r} requires params.company")
        kwargs["company"] = company

    return cls(name=name, url=url, **kwargs)


def list_types() -> list[str]:
    return list(_REGISTRY)
