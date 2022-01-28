# pyright: strict
from logging import Logger
from typing import Iterable, List, NamedTuple, Optional, Dict, Union
from typing_extensions import Literal, TypedDict, NotRequired
from dataclasses import dataclass

from httpx import Response


class Engine:
    categories: Optional[List[str]]
    paging = False
    time_range_support = False
    supported_languages: List[str]
    language_aliases: Dict[str, str]
    about: 'About'

    def __init__(self, logger: Logger) -> None:
        self.logger = logger


class About(TypedDict, total=False):
    website: str
    wikidata_id: Optional[str]
    official_api_documentation: Optional[str]
    use_official_api: bool
    require_api_key: bool
    results: Literal["HTML", "JSON"]
    language: NotRequired[str]


class OnlineEngine(Engine):
    def request(self, query: str, ctx: 'QueryContext') -> 'OnlineRequest':
        raise NotImplementedError()

    def response(self, response: Response) -> List['Result']:
        raise NotImplementedError()


class QueryContext(NamedTuple):
    category: str
    """current category"""
    safesearch: Literal[0, 1, 2]
    """desired content safety (normal, moderate, strict)"""
    time_range: Optional[Literal['day', 'week', 'month', 'year']]
    """current time range (if any)"""
    pageno: int
    """current page number"""
    language: str
    """specific language code like ``en_US``, or ``all`` if unspecified"""


@dataclass
class OnlineRequest:
    url: str
    """requested URL"""
    method: Literal['GET', 'POST'] = 'GET'
    """HTTP request method"""
    headers: Optional[Dict[str, str]] = None
    """HTTP headers"""
    data: Optional[Dict[str, str]] = None
    """data to be sent as the HTTP body"""
    cookies: Optional[Dict[str, str]] = None
    """HTTP cookies"""
    verify: bool = True
    """Assert that the TLS certificate is valid"""
    allow_redirects: bool = True
    """follow redirects"""
    max_redirects: Optional[int] = None
    """maximum redirects, hard limit"""
    soft_max_redirects: Optional[int] = None
    """maximum redirects, soft limit. Record an error but don't stop the engine"""
    raise_for_httperror: bool = True
    """raise an exception if the HTTP code of response is >= 300"""

    def set_header(self, name: str, value: str):
        if self.headers is None:
            self.headers = {}
        self.headers[name] = value


Result = Union['StandardResult', 'InfoBox']


@dataclass
class StandardResult:
    url: str
    title: str
    content: str = ''


@dataclass
class InfoBox(StandardResult):
    img_src: Optional[str] = None
    links: Iterable['Link'] = ()


class Link(TypedDict):
    title: str
    url: str
