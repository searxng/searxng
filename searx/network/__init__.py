# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring, global-statement

import asyncio
import threading
import concurrent.futures
from queue import SimpleQueue
from types import MethodType
from timeit import default_timer
from typing import Iterable, Tuple

import httpx
import anyio

from .network import get_network, initialize, check_network_configuration  # pylint:disable=cyclic-import
from .client import get_loop
from .raise_for_httperror import raise_for_httperror


THREADLOCAL = threading.local()
"""Thread-local data is data for thread specific values."""


def reset_time_for_thread():
    THREADLOCAL.total_time = 0


def get_time_for_thread():
    """returns thread's total time or None"""
    return THREADLOCAL.__dict__.get('total_time')


def set_timeout_for_thread(timeout, start_time=None):
    THREADLOCAL.timeout = timeout
    THREADLOCAL.start_time = start_time


def set_context_network_name(network_name):
    THREADLOCAL.network = get_network(network_name)


def get_context_network():
    """If set return thread's network.

    If unset, return value from :py:obj:`get_network`.
    """
    return THREADLOCAL.__dict__.get('network') or get_network()


def request(method, url, **kwargs):
    """same as requests/requests/api.py request(...)"""
    time_before_request = default_timer()

    # timeout (httpx)
    if 'timeout' in kwargs:
        timeout = kwargs['timeout']
    else:
        timeout = getattr(THREADLOCAL, 'timeout', None)
        if timeout is not None:
            kwargs['timeout'] = timeout

    # 2 minutes timeout for the requests without timeout
    timeout = timeout or 120

    # ajdust actual timeout
    timeout += 0.2  # overhead
    start_time = getattr(THREADLOCAL, 'start_time', time_before_request)
    if start_time:
        timeout -= default_timer() - start_time

    # raise_for_error
    check_for_httperror = True
    if 'raise_for_httperror' in kwargs:
        check_for_httperror = kwargs['raise_for_httperror']
        del kwargs['raise_for_httperror']

    # requests compatibility
    if isinstance(url, bytes):
        url = url.decode()

    # network
    network = get_context_network()

    # do request
    future = asyncio.run_coroutine_threadsafe(network.request(method, url, **kwargs), get_loop())
    try:
        response = future.result(timeout)
    except concurrent.futures.TimeoutError as e:
        raise httpx.TimeoutException('Timeout', request=None) from e

    # requests compatibility
    # see also https://www.python-httpx.org/compatibility/#checking-for-4xx5xx-responses
    response.ok = not response.is_error

    # update total_time.
    # See get_time_for_thread() and reset_time_for_thread()
    if hasattr(THREADLOCAL, 'total_time'):
        time_after_request = default_timer()
        THREADLOCAL.total_time += time_after_request - time_before_request

    # raise an exception
    if check_for_httperror:
        raise_for_httperror(response)

    return response


def get(url, **kwargs):
    kwargs.setdefault('allow_redirects', True)
    return request('get', url, **kwargs)


def options(url, **kwargs):
    kwargs.setdefault('allow_redirects', True)
    return request('options', url, **kwargs)


def head(url, **kwargs):
    kwargs.setdefault('allow_redirects', False)
    return request('head', url, **kwargs)


def post(url, data=None, **kwargs):
    return request('post', url, data=data, **kwargs)


def put(url, data=None, **kwargs):
    return request('put', url, data=data, **kwargs)


def patch(url, data=None, **kwargs):
    return request('patch', url, data=data, **kwargs)


def delete(url, **kwargs):
    return request('delete', url, **kwargs)


async def stream_chunk_to_queue(network, queue, method, url, **kwargs):
    try:
        async with await network.stream(method, url, **kwargs) as response:
            queue.put(response)
            # aiter_raw: access the raw bytes on the response without applying any HTTP content decoding
            # https://www.python-httpx.org/quickstart/#streaming-responses
            async for chunk in response.aiter_raw(65536):
                if len(chunk) > 0:
                    queue.put(chunk)
    except (httpx.StreamClosed, anyio.ClosedResourceError):
        # the response was queued before the exception.
        # the exception was raised on aiter_raw.
        # we do nothing here: in the finally block, None will be queued
        # so stream(method, url, **kwargs) generator can stop
        pass
    except Exception as e:  # pylint: disable=broad-except
        # broad except to avoid this scenario:
        # exception in network.stream(method, url, **kwargs)
        # -> the exception is not catch here
        # -> queue None (in finally)
        # -> the function below steam(method, url, **kwargs) has nothing to return
        queue.put(e)
    finally:
        queue.put(None)


def _stream_generator(method, url, **kwargs):
    queue = SimpleQueue()
    network = get_context_network()
    future = asyncio.run_coroutine_threadsafe(stream_chunk_to_queue(network, queue, method, url, **kwargs), get_loop())

    # yield chunks
    obj_or_exception = queue.get()
    while obj_or_exception is not None:
        if isinstance(obj_or_exception, Exception):
            raise obj_or_exception
        yield obj_or_exception
        obj_or_exception = queue.get()
    future.result()


def _close_response_method(self):
    asyncio.run_coroutine_threadsafe(self.aclose(), get_loop())
    # reach the end of _self.generator ( _stream_generator ) to an avoid memory leak.
    # it makes sure that :
    # * the httpx response is closed (see the stream_chunk_to_queue function)
    # * to call future.result() in _stream_generator
    for _ in self._generator:  # pylint: disable=protected-access
        continue


def stream(method, url, **kwargs) -> Tuple[httpx.Response, Iterable[bytes]]:
    """Replace httpx.stream.

    Usage:
    response, stream = poolrequests.stream(...)
    for chunk in stream:
        ...

    httpx.Client.stream requires to write the httpx.HTTPTransport version of the
    the httpx.AsyncHTTPTransport declared above.
    """
    generator = _stream_generator(method, url, **kwargs)

    # yield response
    response = next(generator)  # pylint: disable=stop-iteration-return
    if isinstance(response, Exception):
        raise response

    response._generator = generator  # pylint: disable=protected-access
    response.close = MethodType(_close_response_method, response)

    return response, generator
