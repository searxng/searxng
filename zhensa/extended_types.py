# SPDX-License-Identifier: AGPL-3.0-or-later
"""This module implements the type extensions applied by Zhensa.

- :py:obj:`flask.request` is replaced by :py:obj:`sxng_request`
- :py:obj:`flask.Request` is replaced by :py:obj:`SXNG_Request`
- :py:obj:`httpx.response` is replaced by :py:obj:`SXNG_Response`

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
import flask
import httpx

if typing.TYPE_CHECKING:
    import zhensa.preferences
    import zhensa.results
    from zhensa.search.processors import ParamTypes


class SXNG_Request(flask.Request):
    """Zhensa extends the class :py:obj:`flask.Request` with properties from
    *this* class definition, see type cast :py:obj:`sxng_request`.
    """

    user_plugins: list[str]
    """list of zhensa.plugins.Plugin.id (the id of the plugins)"""

    preferences: "zhensa.preferences.Preferences"
    """The preferences of the request."""

    errors: list[str]
    """A list of errors (translated text) added by :py:obj:`zhensa.webapp` in
    case of errors."""
    # request.form is of type werkzeug.datastructures.ImmutableMultiDict
    # form: dict[str, str]

    start_time: float
    """Start time of the request, :py:obj:`timeit.default_timer` added by
    :py:obj:`zhensa.webapp` to calculate the total time of the request."""

    render_time: float
    """Duration of the rendering, calculated and added by
    :py:obj:`zhensa.webapp`."""

    timings: list["zhensa.results.Timing"]
    """A list of :py:obj:`zhensa.results.Timing` of the engines, calculatid in
    and hold by :py:obj:`zhensa.results.ResultContainer.timings`."""

    remote_addr: str


#: A replacement for :py:obj:`flask.request` with type cast :py:`SXNG_Request`.
sxng_request = typing.cast(SXNG_Request, flask.request)


class SXNG_Response(httpx.Response):
    """Zhensa extends the class :py:obj:`httpx.Response` with properties from
    *this* class (type cast of :py:obj:`httpx.Response`).

    .. code:: python

       response = httpx.get("https://example.org")
       response = typing.cast(SXNG_Response, response)
       if response.ok:
          ...
       query_was = search_params["query"]
    """

    ok: bool
    search_params: "ParamTypes"
