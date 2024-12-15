# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations for a favicon proxy"""

from __future__ import annotations

from typing import Callable

import importlib
import base64
import pathlib
import urllib.parse

import flask
from httpx import HTTPError
import msgspec

from searx import get_setting

from searx.webutils import new_hmac, is_hmac_of
from searx.exceptions import SearxEngineResponseException
from searx.extended_types import sxng_request

from .resolvers import DEFAULT_RESOLVER_MAP
from . import cache

DEFAULT_FAVICON_URL = {}
CFG: FaviconProxyConfig = None  # type: ignore


def init(cfg: FaviconProxyConfig):
    global CFG  # pylint: disable=global-statement
    CFG = cfg


def _initial_resolver_map():
    d = {}
    name: str = get_setting("search.favicon_resolver", None)  # type: ignore
    if name:
        func = DEFAULT_RESOLVER_MAP.get(name)
        if func:
            d = {name: f"searx.favicons.resolvers.{func.__name__}"}
    return d


class FaviconProxyConfig(msgspec.Struct):
    """Configuration of the favicon proxy."""

    max_age: int = 60 * 60 * 24 * 7  # seven days
    """HTTP header Cache-Control_ ``max-age``

    .. _Cache-Control: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    """

    secret_key: str = get_setting("server.secret_key")  # type: ignore
    """By default, the value from :ref:`server.secret_key <settings server>`
    setting is used."""

    resolver_timeout: int = get_setting("outgoing.request_timeout")  # type: ignore
    """Timeout which the resolvers should not exceed, is usually passed to the
    outgoing request of the resolver.  By default, the value from
    :ref:`outgoing.request_timeout <settings outgoing>` setting is used."""

    resolver_map: dict[str, str] = msgspec.field(default_factory=_initial_resolver_map)
    """The resolver_map is a key / value dictionary where the key is the name of
    the resolver and the value is the fully qualifying name (fqn) of resolver's
    function (the callable).  The resolvers from the python module
    :py:obj:`searx.favicons.resolver` are available by default."""

    def get_resolver(self, name: str) -> Callable | None:
        """Returns the callable object (function) of the resolver with the
        ``name``.  If no resolver is registered for the ``name``, ``None`` is
        returned.
        """
        fqn = self.resolver_map.get(name)
        if fqn is None:
            return None
        mod_name, _, func_name = fqn.rpartition('.')
        mod = importlib.import_module(mod_name)
        func = getattr(mod, func_name)
        if func is None:
            raise ValueError(f"resolver {fqn} is not implemented")
        return func

    favicon_path: str = get_setting("ui.static_path") + "/themes/{theme}/img/empty_favicon.svg"  # type: ignore
    favicon_mime_type: str = "image/svg+xml"

    def favicon(self, **replacements):
        """Returns pathname and mimetype of the default favicon."""
        return (
            pathlib.Path(self.favicon_path.format(**replacements)),
            self.favicon_mime_type,
        )

    def favicon_data_url(self, **replacements):
        """Returns data image URL of the default favicon."""

        cache_key = ", ".join(f"{x}:{replacements[x]}" for x in sorted(list(replacements.keys()), key=str))
        data_url = DEFAULT_FAVICON_URL.get(cache_key)
        if data_url is not None:
            return data_url

        fav, mimetype = CFG.favicon(**replacements)
        # hint: encoding utf-8 limits favicons to be a SVG image
        with fav.open("r", encoding="utf-8") as f:
            data_url = f.read()

        data_url = urllib.parse.quote(data_url)
        data_url = f"data:{mimetype};utf8,{data_url}"
        DEFAULT_FAVICON_URL[cache_key] = data_url
        return data_url


def favicon_proxy():
    """REST API of SearXNG's favicon proxy service

    ::

        /favicon_proxy?authority=<...>&h=<...>

    ``authority``:
      Domain name :rfc:`3986` / see :py:obj:`favicon_url`

    ``h``:
      HMAC :rfc:`2104`, build up from the :ref:`server.secret_key <settings
      server>` setting.

    """
    authority = sxng_request.args.get('authority')

    # malformed request or RFC 3986 authority
    if not authority or "/" in authority:
        return '', 400

    # malformed request / does not have authorisation
    if not is_hmac_of(
        CFG.secret_key,
        authority.encode(),
        sxng_request.args.get('h', ''),
    ):
        return '', 400

    resolver = sxng_request.preferences.get_value('favicon_resolver')  # type: ignore
    # if resolver is empty or not valid, just return HTTP 400.
    if not resolver or resolver not in CFG.resolver_map.keys():
        return "", 400

    data, mime = search_favicon(resolver, authority)

    if data is not None and mime is not None:
        resp = flask.Response(data, mimetype=mime)  # type: ignore
        resp.headers['Cache-Control'] = f"max-age={CFG.max_age}"
        return resp

    # return default favicon from static path
    theme = sxng_request.preferences.get_value("theme")  # type: ignore
    fav, mimetype = CFG.favicon(theme=theme)
    return flask.send_from_directory(fav.parent, fav.name, mimetype=mimetype)


def search_favicon(resolver: str, authority: str) -> tuple[None | bytes, None | str]:
    """Sends the request to the favicon resolver and returns a tuple for the
    favicon.  The tuple consists of ``(data, mime)``, if the resolver has not
    determined a favicon, both values are ``None``.

    ``data``:
      Binary data of the favicon.

    ``mime``:
      Mime type of the favicon.

    """

    data, mime = (None, None)

    func = CFG.get_resolver(resolver)
    if func is None:
        return data, mime

    # to avoid superfluous requests to the resolver, first look in the cache
    data_mime = cache.CACHE(resolver, authority)
    if data_mime is not None:
        return data_mime

    try:
        data, mime = func(authority, timeout=CFG.resolver_timeout)
        if data is None or mime is None:
            data, mime = (None, None)

    except (HTTPError, SearxEngineResponseException):
        pass

    cache.CACHE.set(resolver, authority, mime, data)
    return data, mime


def favicon_url(authority: str) -> str:
    """Function to generate the image URL used for favicons in SearXNG's result
    lists.  The ``authority`` argument (aka netloc / :rfc:`3986`) is usually a
    (sub-) domain name.  This function is used in the HTML (jinja) templates.

    .. code:: html

       <div class="favicon">
          <img src="{{ favicon_url(result.parsed_url.netloc) }}">
       </div>

    The returned URL is a route to :py:obj:`favicon_proxy` REST API.

    If the favicon is already in the cache, the returned URL is a `data URL`_
    (something like ``data:image/png;base64,...``).  By generating a data url from
    the :py:obj:`.cache.FaviconCache`, additional HTTP roundtripps via the
    :py:obj:`favicon_proxy` are saved.  However, it must also be borne in mind
    that data urls are not cached in the client (web browser).

    .. _data URL: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URLs

    """

    resolver = sxng_request.preferences.get_value('favicon_resolver')  # type: ignore
    # if resolver is empty or not valid, just return nothing.
    if not resolver or resolver not in CFG.resolver_map.keys():
        return ""

    data_mime = cache.CACHE(resolver, authority)

    if data_mime == (None, None):
        # we have already checked, the resolver does not have a favicon
        theme = sxng_request.preferences.get_value("theme")  # type: ignore
        return CFG.favicon_data_url(theme=theme)

    if data_mime is not None:
        data, mime = data_mime
        return f"data:{mime};base64,{str(base64.b64encode(data), 'utf-8')}"  # type: ignore

    h = new_hmac(CFG.secret_key, authority.encode())
    proxy_url = flask.url_for('favicon_proxy')
    query = urllib.parse.urlencode({"authority": authority, "h": h})
    return f"{proxy_url}?{query}"
