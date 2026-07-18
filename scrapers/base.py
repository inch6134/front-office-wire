from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class Job:
    id: str
    title: str
    organization: str
    location: str
    url: str
    description: str
    posted_at: None
    source: str


def build_session(
    retries: int = 3, backoff: float = 0.5, timeout: int = 30
) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {"User-Agent": "FrontOfficeWireBot/1.0 (+https://github.com/)"}
    )
    session._default_timeout = timeout
    return session


class BaseScraper(ABC):
    def __init__(self, name: str, url: str, **kwargs):
        self.name = name
        self.url = url
        self.session = build_session()

    def get(self, url: str, **kwargs) -> requests.Response:
        timeout = kwargs.pop("timeout", self.session._default_timeout)
        response = self.session.get(url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response

    def post(self, url: str, **kwargs) -> requests.Response:
        timeout = kwargs.pop("timeout", self.session._default_timeout)
        response = self.session.post(url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response

    @abstractmethod
    def fetch_jobs(self) -> list[Job]:
        raise NotImplementedError
