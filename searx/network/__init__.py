# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
# pylint: disable=redefined-outer-name
# ^^ because there is the raise_for_httperror function and the raise_for_httperror parameter.
"""HTTP for SearXNG.

In httpx and similar libraries, a client (also named session) contains a pool of HTTP connections.
The client reuses these HTTP connections and automatically recreates them when the server at the other
end closes the connections. Whatever the library, each client uses only one proxy (eventually none) and only
one local IP address.

SearXNG's primary use case is an engine sending one (or more) outgoing HTTP request(s). The admin can configure
an engine to use multiple proxies and/or IP addresses:  SearXNG sends the outgoing HTTP requests through these
different proxies/IP addresses ( = HTTP clients ) on a rotational basis.

In addition, when SearXNG runs an engine request, there is a hard timeout: the engine runtime must not exceed
a defined value.

Moreover, an engine can ask SearXNG to retry a failed HTTP request.

However, we want to keep the engine codes simple and keep the complexity either in the configuration or the
core component components (here, in this module).

To answer the above requirements, the `searx.network` module introduces three components:
* HTTPClient and TorHTTPClient are two classes that wrap one or multiple httpx.Client
* NetworkManager, a set of named Network. Each Network
    * holds the configuration defined in settings.yml
    * creates NetworkContext fed with an HTTPClient (or TorHTTPClient).
      This is where the rotation between the proxies and IP addresses happens.
* NetworkContext to provide a runtime context for the engines. The constructor needs a global timeout
  and an HTTPClient factory. NetworkContext is an abstract class with three implementations,
  one for each retry policy.

It is only possible to send an HTTP request with a NetworkContext
(otherwise, SearXNG raises a NetworkContextNotFound exception).
Two helpers set a NetworkContext for the current thread:

* The decorator `@networkcontext_decorator`, the intended usage is an external script (see searxng_extra)
* The context manager `networkcontext_manager`, for the generic use case.

Inside the thread, the caller can use `searx.network.get`, `searx.network.post` and similar functions without
caring about the HTTP client. However, if the caller creates a new thread, it must initialize a new NetworkContext.
A NetworkContext is most probably thread-safe, but this has not been tested.

The overall architecture:
* searx.network.network.NETWORKS contains all the networks.
    The method `NetworkManager.get(network_name)` returns an initialized Network.
* searx.network.network.Network defines a network (a set of proxies, local IP address, etc...).
    They are defined in settings.yml.
    The method `Network.get_context()` creates a new NetworkContext.
* searx.network.context contains three different implementations of NetworkContext. One for each retry policy.
* searx.network.client.HTTPClient and searx.network.client.TorHTTPClient implement wrappers around httpx.Client.
"""
import threading
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional, Union

import httpx

from searx.network.client import NOTSET, _NotSetClass
from searx.network.context import NetworkContext, P, R
from searx.network.network import NETWORKS
from searx.network.raise_for_httperror import raise_for_httperror

__all__ = [
    "NETWORKS",
    "NetworkContextNotFound",
    "networkcontext_manager",
    "networkcontext_decorator",
    "raise_for_httperror",
    "request",
    "get",
    "options",
    "head",
    "post",
    "put",
    "patch",
    "delete",
]


_THREADLOCAL = threading.local()
"""Thread-local that contains only one field: network_context."""

_NETWORK_CONTEXT_KEY = 'network_context'
"""Key to access _THREADLOCAL"""

DEFAULT_MAX_REDIRECTS = httpx._config.DEFAULT_MAX_REDIRECTS  # pylint: disable=protected-access


class NetworkContextNotFound(Exception):
    """A NetworkContext is expected to exist for the current thread.

    Use searx.network.networkcontext_manager or searx.network.networkcontext_decorator
    to set a NetworkContext
    """


@contextmanager
def networkcontext_manager(
    network_name: Optional[str] = None, timeout: Optional[float] = None, start_time: Optional[float] = None
):
    """Context manager to set a NetworkContext for the current thread

    The timeout is for the whole function and is infinite by default (None).
    The timeout is counted from the current time or start_time if different from None.

    Example of usage:

    ```python
    from time import sleep
    from searx.network import networkcontext_manager, get

    def search(query):
        # the timeout is automatically set to 2.0 seconds (the remaining time for the NetworkContext)
        # 2.0 because the timeout for the NetworkContext is 3.0 and one second has elllapsed with sleep(1.0)
        auckland_time = get("http://worldtimeapi.org/api/timezone/Pacific/Auckland").json()
        # the timeout is automatically set to 2.0 - (runtime of the previous HTTP request)
        ip_time = get("http://worldtimeapi.org/api/ip").json()
        return auckland_time, ip_time

    # "worldtimeapi" is network defined in settings.yml
    # network_context.call might call multiple times the search function,
    # however the timeout will be respected.
    with networkcontext_manager('worldtimeapi', timeout=3.0) as network_context:
        sleep(1.0)
        auckland_time, ip_time = network_context.call(search(query))
        print("Auckland time: ", auckland_time["datetime"])
        print("My time: ", ip_time["datetime"])
        print("HTTP runtime:", network_context.get_http_runtime())
    ```
    """
    network = NETWORKS.get(network_name)
    network_context = network.get_context(timeout=timeout, start_time=start_time)
    setattr(_THREADLOCAL, _NETWORK_CONTEXT_KEY, network_context)
    try:
        yield network_context
    finally:
        delattr(_THREADLOCAL, _NETWORK_CONTEXT_KEY)
        del network_context


def networkcontext_decorator(
    network_name: Optional[str] = None, timeout: Optional[float] = None, start_time: Optional[float] = None
):
    """Set the NetworkContext, then call the wrapped function using searx.network.context.NetworkContext.call

    The timeout is for the whole function and is infinite by default (None).
    The timeout is counted from the current time or start_time if different from None

    Intended usage: to provide a NetworkContext for scripts in searxng_extra.

    Example of usage:

    ```python
    from time import sleep
    from searx import network

    @network.networkcontext_decorator(timeout=3.0)
    def main()
        sleep(1.0)
        # the timeout is automatically set to 2.0 (the remaining time for the NetworkContext).
        my_ip = network.get("https://ifconfig.me/ip").text
        print(my_ip)

    if __name__ == '__main__':
        main()
    ```
    """

    def func_outer(func: Callable[P, R]):
        @wraps(func)
        def func_inner(*args: P.args, **kwargs: P.kwargs) -> R:
            with networkcontext_manager(network_name, timeout, start_time) as network_context:
                return network_context.call(func, *args, **kwargs)

        return func_inner

    return func_outer


def request(
    method: str,
    url: str,
    params: Optional[httpx._types.QueryParamTypes] = None,
    content: Optional[httpx._types.RequestContent] = None,
    data: Optional[httpx._types.RequestData] = None,
    files: Optional[httpx._types.RequestFiles] = None,
    json: Optional[Any] = None,
    headers: Optional[httpx._types.HeaderTypes] = None,
    cookies: Optional[httpx._types.CookieTypes] = None,
    auth: Optional[httpx._types.AuthTypes] = None,
    timeout: httpx._types.TimeoutTypes = None,
    allow_redirects: bool = False,
    max_redirects: Union[_NotSetClass, int] = NOTSET,
    verify: Union[_NotSetClass, httpx._types.VerifyTypes] = NOTSET,
    raise_for_httperror: bool = False,
) -> httpx.Response:
    """Similar to httpx.request ( https://www.python-httpx.org/api/ ) with some differences:

    * proxies:
        it is not available and has to be defined in the Network configuration (in settings.yml)
    * cert:
        it is not available and is always None.
    * trust_env:
        it is not available and is always True.
    * timeout:
        the implementation uses the lowest timeout between this parameter and remaining time for the NetworkContext.
    * allow_redirects:
        it replaces the follow_redirects parameter to be compatible with the requests API.
    * raise_for_httperror:
        when True, this function calls searx.network.raise_for_httperror.raise_for_httperror.

    Some parameters from httpx.Client ( https://www.python-httpx.org/api/#client) are available:

    * max_redirects:
        Set to None to use the value from the Network configuration.
        The maximum number of redirect responses that should be followed.
    * verify:
        Set to None to use the value from the Network configuration.
    * limits:
        it has to be defined in the Network configuration (in settings.yml)
    * default_encoding:
        this parameter is not available and is always "utf-8".

    This function requires a NetworkContext provided by either networkcontext_decorator or networkcontext_manager.

    The implementation uses one or more httpx.Client
    """
    # pylint: disable=too-many-arguments
    network_context: Optional[NetworkContext] = getattr(_THREADLOCAL, _NETWORK_CONTEXT_KEY, None)
    if network_context is None:
        raise NetworkContextNotFound()
    http_client = network_context._get_http_client()  # pylint: disable=protected-access
    return http_client.request(
        method,
        url,
        params=params,
        content=content,
        data=data,
        files=files,
        json=json,
        headers=headers,
        cookies=cookies,
        auth=auth,
        timeout=timeout,
        allow_redirects=allow_redirects,
        max_redirects=max_redirects,
        verify=verify,
        raise_for_httperror=raise_for_httperror,
    )


def get(
    url: str,
    params: Optional[httpx._types.QueryParamTypes] = None,
    headers: Optional[httpx._types.HeaderTypes] = None,
    cookies: Optional[httpx._types.CookieTypes] = None,
    auth: Optional[httpx._types.AuthTypes] = None,
    allow_redirects: bool = True,
    max_redirects: Union[_NotSetClass, int] = NOTSET,
    verify: Union[_NotSetClass, httpx._types.VerifyTypes] = NOTSET,
    timeout: httpx._types.TimeoutTypes = None,
    raise_for_httperror: bool = False,
) -> httpx.Response:
    """Similar to httpx.get, see the request method for the details.

    allow_redirects is by default True (httpx default value is False).
    """
    # pylint: disable=too-many-arguments
    return request(
        "GET",
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        allow_redirects=allow_redirects,
        max_redirects=max_redirects,
        verify=verify,
        timeout=timeout,
        raise_for_httperror=raise_for_httperror,
    )


def options(
    url: str,
    params: Optional[httpx._types.QueryParamTypes] = None,
    headers: Optional[httpx._types.HeaderTypes] = None,
    cookies: Optional[httpx._types.CookieTypes] = None,
    auth: Optional[httpx._types.AuthTypes] = None,
    allow_redirects: bool = False,
    max_redirects: Union[_NotSetClass, int] = NOTSET,
    verify: Union[_NotSetClass, httpx._types.VerifyTypes] = NOTSET,
    timeout: httpx._types.TimeoutTypes = None,
    raise_for_httperror: bool = False,
) -> httpx.Response:
    """Similar to httpx.options, see the request method for the details."""
    # pylint: disable=too-many-arguments
    return request(
        "OPTIONS",
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        allow_redirects=allow_redirects,
        max_redirects=max_redirects,
        verify=verify,
        timeout=timeout,
        raise_for_httperror=raise_for_httperror,
    )


def head(
    url: str,
    params: Optional[httpx._types.QueryParamTypes] = None,
    headers: Optional[httpx._types.HeaderTypes] = None,
    cookies: Optional[httpx._types.CookieTypes] = None,
    auth: Optional[httpx._types.AuthTypes] = None,
    allow_redirects: bool = False,
    max_redirects: Union[_NotSetClass, int] = NOTSET,
    verify: Union[_NotSetClass, httpx._types.VerifyTypes] = NOTSET,
    timeout: httpx._types.TimeoutTypes = None,
    raise_for_httperror: bool = False,
) -> httpx.Response:
    """Similar to httpx.head, see the request method for the details."""
    # pylint: disable=too-many-arguments
    return request(
        "HEAD",
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        allow_redirects=allow_redirects,
        max_redirects=max_redirects,
        verify=verify,
        timeout=timeout,
        raise_for_httperror=raise_for_httperror,
    )


def post(
    url: str,
    content: Optional[httpx._types.RequestContent] = None,
    data: Optional[httpx._types.RequestData] = None,
    files: Optional[httpx._types.RequestFiles] = None,
    json: Optional[Any] = None,
    params: Optional[httpx._types.QueryParamTypes] = None,
    headers: Optional[httpx._types.HeaderTypes] = None,
    cookies: Optional[httpx._types.CookieTypes] = None,
    auth: Optional[httpx._types.AuthTypes] = None,
    allow_redirects: bool = False,
    max_redirects: Union[_NotSetClass, int] = NOTSET,
    verify: Union[_NotSetClass, httpx._types.VerifyTypes] = NOTSET,
    timeout: httpx._types.TimeoutTypes = None,
    raise_for_httperror: bool = False,
) -> httpx.Response:
    """Similar to httpx.post, see the request method for the details."""
    # pylint: disable=too-many-arguments
    return request(
        "POST",
        url,
        content=content,
        data=data,
        files=files,
        json=json,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        allow_redirects=allow_redirects,
        max_redirects=max_redirects,
        verify=verify,
        timeout=timeout,
        raise_for_httperror=raise_for_httperror,
    )


def put(
    url: str,
    content: Optional[httpx._types.RequestContent] = None,
    data: Optional[httpx._types.RequestData] = None,
    files: Optional[httpx._types.RequestFiles] = None,
    json: Optional[Any] = None,
    params: Optional[httpx._types.QueryParamTypes] = None,
    headers: Optional[httpx._types.HeaderTypes] = None,
    cookies: Optional[httpx._types.CookieTypes] = None,
    auth: Optional[httpx._types.AuthTypes] = None,
    allow_redirects: bool = False,
    max_redirects: Union[_NotSetClass, int] = NOTSET,
    verify: Union[_NotSetClass, httpx._types.VerifyTypes] = NOTSET,
    timeout: httpx._types.TimeoutTypes = None,
    raise_for_httperror: bool = False,
) -> httpx.Response:
    """Similar to httpx.put, see the request method for the details."""
    # pylint: disable=too-many-arguments
    return request(
        "PUT",
        url,
        content=content,
        data=data,
        files=files,
        json=json,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        allow_redirects=allow_redirects,
        max_redirects=max_redirects,
        verify=verify,
        timeout=timeout,
        raise_for_httperror=raise_for_httperror,
    )


def patch(
    url: str,
    content: Optional[httpx._types.RequestContent] = None,
    data: Optional[httpx._types.RequestData] = None,
    files: Optional[httpx._types.RequestFiles] = None,
    json: Optional[Any] = None,
    params: Optional[httpx._types.QueryParamTypes] = None,
    headers: Optional[httpx._types.HeaderTypes] = None,
    cookies: Optional[httpx._types.CookieTypes] = None,
    auth: Optional[httpx._types.AuthTypes] = None,
    allow_redirects: bool = False,
    max_redirects: Union[_NotSetClass, int] = NOTSET,
    verify: Union[_NotSetClass, httpx._types.VerifyTypes] = NOTSET,
    timeout: httpx._types.TimeoutTypes = None,
    raise_for_httperror: bool = False,
) -> httpx.Response:
    """Similar to httpx.patch, see the request method for the details."""
    # pylint: disable=too-many-arguments
    return request(
        "PATCH",
        url,
        content=content,
        data=data,
        files=files,
        json=json,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        allow_redirects=allow_redirects,
        max_redirects=max_redirects,
        verify=verify,
        timeout=timeout,
        raise_for_httperror=raise_for_httperror,
    )


def delete(
    url: str,
    params: Optional[httpx._types.QueryParamTypes] = None,
    headers: Optional[httpx._types.HeaderTypes] = None,
    cookies: Optional[httpx._types.CookieTypes] = None,
    auth: Optional[httpx._types.AuthTypes] = None,
    allow_redirects: bool = False,
    max_redirects: Union[_NotSetClass, int] = NOTSET,
    verify: Union[_NotSetClass, httpx._types.VerifyTypes] = NOTSET,
    timeout: httpx._types.TimeoutTypes = None,
    raise_for_httperror: bool = False,
) -> httpx.Response:
    """Similar to httpx.delete, see the request method for the details."""
    # pylint: disable=too-many-arguments
    return request(
        "DELETE",
        url,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        allow_redirects=allow_redirects,
        max_redirects=max_redirects,
        verify=verify,
        timeout=timeout,
        raise_for_httperror=raise_for_httperror,
    )
