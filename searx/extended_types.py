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

__all__ = ["SXNG_Request", "sxng_request", "SXNG_Response"]

import typing
from urllib.parse import urlsplit

import flask
from curl_cffi.requests import Response as CurlResponse

if typing.TYPE_CHECKING:
    import searx.preferences
    import searx.results
    from searx.search.processors import OnlineParamTypes, OnlineDictParams, OnlineCurrenciesParams


class SXNG_Request(flask.Request):
    """SearXNG extends the class :py:obj:`flask.Request` with properties from
    *this* class definition, see type cast :py:obj:`sxng_request`.
    """

    user_plugins: list[str]
    """list of searx.plugins.Plugin.id (the id of the plugins)"""

    preferences: "searx.preferences.Preferences"
    """The preferences of the request."""

    errors: list[str]
    """A list of errors (translated text) added by :py:obj:`searx.webapp` in
    case of errors."""
    # request.form is of type werkzeug.datastructures.ImmutableMultiDict
    # form: dict[str, str]

    start_time: float
    """Start time of the request, :py:obj:`timeit.default_timer` added by
    :py:obj:`searx.webapp` to calculate the total time of the request."""

    render_time: float
    """Duration of the rendering, calculated and added by
    :py:obj:`searx.webapp`."""

    timings: list["searx.results.Timing"]
    """A list of :py:obj:`searx.results.Timing` of the engines, calculatid in
    and hold by :py:obj:`searx.results.ResultContainer.timings`."""

    remote_addr: str


#: A replacement for :py:obj:`flask.request` with type cast :py:`SXNG_Request`.
sxng_request = typing.cast(SXNG_Request, flask.request)


class SXNG_URL(str):
    """String URL"""

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
    def url(self) -> SXNG_URL:  # type: ignore[override]
        return SXNG_URL(self._url)

    @url.setter
    def url(self, value: str) -> None:
        self._url = str(value or "")
