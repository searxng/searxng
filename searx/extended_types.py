# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module implements the type extensions applied by SearXNG.

- :py:obj:`flask.request` is replaced by :py:obj:`sxng_request`
- :py:obj:`flask.Request` is replaced by :py:obj:`SXNG_Request`
- :py:obj:`curl_cffi.requests.Response` is replaced by :py:obj:`SXNG_Response`

----

.. py:attribute:: sxng_request
   :type: SXNG_Request

   A replacement for :py:obj:`flask.request` with type cast :py:obj:`SXNG_Request`.

.. autoclass:: SXNG_Request
   :members:

.. autoclass:: SXNG_Response
   :members:

"""

# pylint: disable=invalid-name

__all__ = ["CIHeaders", "SXNG_Request", "SXNG_Response", "sxng_request"]

from collections.abc import Callable, Generator, Iterable, Iterator, MutableMapping
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from functools import wraps
from timeit import default_timer
from typing import TYPE_CHECKING, Any, ParamSpec, Self, TypeVar, overload
from urllib.parse import urlsplit

import flask
from curl_cffi.requests import Response as CurlResponse
from lxml import html
from werkzeug.datastructures import Authorization

if TYPE_CHECKING:
    import searx.results
    from searx.preferences import Preferences
    from searx.search.processors import OnlineCurrenciesParams, OnlineDictParams, OnlineParamTypes

FuncParam = ParamSpec("FuncParam")
_T = TypeVar("_T")


@dataclass
class SXNG_Request:
    """Everything SearXNG is allowed to know about one request."""

    # Previously a `flask.Request` subclass with extra properties
    # common request properties:
    form: MutableMapping[str, str] = field(default_factory=dict[str, str])
    args: MutableMapping[str, str] = field(default_factory=dict[str, str])
    headers: MutableMapping[str, str] = field(default_factory=dict[str, str])  # keys lower-cased
    cookies: MutableMapping[str, str] = field(default_factory=dict[str, str])
    remote_addr: str = ""
    path: str = ""
    # SXNG_Request extras:
    user_plugins: list[str] = field(default_factory=list)
    _preferences: "Preferences | None" = field(default=None, init=False, repr=False)
    errors: list[str] = field(default_factory=list)
    start_time: float = field(default_factory=default_timer)
    render_time: float = 0.0
    timings: list["searx.results.Timing"] = field(default_factory=list)
    # flask derived properties:
    scheme: str = "http"
    host: str = ""  # netloc incl. port, e.g. "localhost:8888"
    query_string: bytes | str = b""  # werkzeug exposes query_string as bytes
    method: str = "GET"
    endpoint: str | None = ""  # flask routing name; webapp.render() reads it;

    @property
    def host_url(self) -> str:
        return f"{self.scheme}://{self.host}"

    @property
    def base_url(self) -> str:
        return self.host_url + self.path

    @property
    def full_path(self) -> str:
        if not self.query_string:
            return self.path
        if isinstance(self.query_string, bytes):
            return f"{self.path}?" + self.query_string.decode("utf-8")
        return f"{self.path}?{self.query_string}"

    @property
    def preferences(self) -> "Preferences":
        if self._preferences is None:
            raise AttributeError("Preferences is required but has not been assigned a value")
        return self._preferences

    @preferences.setter
    def preferences(self, value: "Preferences"):
        self._preferences = value

    @property
    def url(self) -> str:
        return self.host_url + self.full_path

    @property
    def authorization(self) -> Authorization | None:
        """Parsed ``Authorization`` header, compatible with Flask's request API."""
        return Authorization.from_header(self.headers.get("authorization"))

    @property
    def user_agent(self) -> str:
        return self.headers.get("user-agent", "")

    @user_agent.setter
    def user_agent(self, value: str):
        self.headers["user-agent"] = value

    def header(self, name: str) -> str | None:
        """Case-insensitive header lookup (werkzeug.Headers semantics)."""
        return self.headers.get(name.lower())

    @classmethod
    def from_flask_request(cls, r: flask.Request) -> Self:
        return cls(
            form=r.form,
            args=r.args,
            headers=CIHeaders(r.headers.items()),
            cookies=r.cookies,
            remote_addr=r.remote_addr or "",
            path=r.path,
            scheme=r.scheme,
            host=r.host,  # werkzeug host == netloc (host:port)
            query_string=r.query_string,
            method=r.method,
            endpoint=r.endpoint,
        )


class CIHeaders(MutableMapping[str, str]):
    """Case-insensitive headers"""

    def __init__(self, pairs: Iterable[tuple[str, str]] = ()) -> None:
        self._d: dict[str, str] = {}
        for key, value in pairs:
            normalized_key = self._normalize_key(key)
            self._d.setdefault(normalized_key, value)

    @overload
    def get(self, key: str, default: None = None, /) -> str | None: ...

    @overload
    def get(self, key: str, default: str, /) -> str: ...

    @overload
    def get(self, key: str, default: _T, /) -> str | _T: ...

    def get(self, key: str, default: str | _T | None = None) -> str | _T | None:
        return self._d.get(self._normalize_key(key), default)

    def _normalize_key(self, key: str) -> str:
        if not isinstance(key, str):
            raise TypeError(f"Keys must be strings, got {type(key).__name__}")
        return key.lower()

    def __getitem__(self, key: str) -> str:
        return self._d[self._normalize_key(key)]

    def __setitem__(self, key: str, value: str) -> None:
        self._d[self._normalize_key(key)] = value

    def __delitem__(self, key: str) -> None:
        del self._d[self._normalize_key(key)]

    def __iter__(self) -> Iterator[str]:
        return iter(self._d)

    def __len__(self) -> int:
        return len(self._d)


_current: ContextVar[SXNG_Request | None] = ContextVar("sxng_request", default=None)


@contextmanager
def request_scope(req: SXNG_Request) -> Generator[None, Any, None]:
    token = _current.set(req)
    try:
        yield
    finally:
        _current.reset(token)


def current_request() -> SXNG_Request:
    req = _current.get()
    if req is None:
        raise RuntimeError("no active request context — enter request_scope() first")
    return req


def has_request() -> bool:
    return _current.get() is not None


def set_request(req: SXNG_Request) -> Token[SXNG_Request | None]:
    return _current.set(req)


def reset_request(token: Token[SXNG_Request | None]) -> None:
    _current.reset(token)


def bind_request_context(fn: Callable[FuncParam, _T], req: SXNG_Request | None = None) -> Callable[FuncParam, _T]:
    """Wrap fn so it runs with the current request context, in any thread.

    Framework-free equivalent of flask.copy_current_request_context: capture
    the request at wrap time (main thread), re-enter its scope at call time
    (worker thread).
    """
    _req = req if req is not None else current_request()

    @wraps(fn)
    def wrapper(*args: FuncParam.args, **kwargs: FuncParam.kwargs) -> _T:
        with request_scope(_req):
            return fn(*args, **kwargs)

    return wrapper


class _RequestProxy:
    """Module-level stand-in for the old ``typing.cast(SXNG_Request, flask.request)``."""

    def __getattr__(self, name: str):
        return getattr(current_request(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(current_request(), name, value)

    def __delattr__(self, name: str) -> None:
        delattr(current_request(), name)

    def _get_current_object(self) -> "SXNG_Request":
        """werkzeug LocalProxy compat: there is no indirection to unwrap."""
        return current_request()


# Keep the historical name/import path so every plugin keeps working untouched.
if TYPE_CHECKING:
    sxng_request: SXNG_Request = ...  # type: ignore[assignment]
else:
    sxng_request = _RequestProxy()


class SXNG_URL(str):
    """String URL"""

    @property
    def base_url(self) -> str | None:
        parts = urlsplit(self)
        return f"{parts.scheme}://{parts.netloc}"

    @property
    def host(self) -> str | None:
        return urlsplit(self).hostname

    @property
    def path(self) -> str:
        return urlsplit(self).path


class SXNG_Response(CurlResponse):
    """SearXNG extends :py:obj:`curl_cffi.requests.Response` with properties from
    *this* class (type cast of the curl_cffi response).

    .. code:: python

       response = typing.cast(SXNG_Response, response)
       if response.ok:
          ...
       query_was = search_params["query"]
    """

    search_params: "OnlineParamTypes | OnlineDictParams | OnlineCurrenciesParams"
    _url: str = ""

    @property
    def url(self) -> SXNG_URL:
        return SXNG_URL(self._url)

    @url.setter
    def url(self, value: str) -> None:
        self._url = str(value or "")

    def html(self) -> html.HtmlElement:
        """Parses the result into a HTML document via :py:obj:`lxml.html`."""

        return html.fromstring(self.text)
