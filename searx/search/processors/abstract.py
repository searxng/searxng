# SPDX-License-Identifier: AGPL-3.0-or-later
"""Abstract base classes for all engine processors."""

import typing as t

import logging
import threading
from abc import abstractmethod, ABC
from timeit import default_timer

from searx import get_setting
from searx import logger
from searx.engines import engines
from searx.network import get_time_for_thread, get_network
from searx.metrics import histogram_observe, counter_inc, count_exception, count_error
from searx.exceptions import SearxEngineAccessDeniedException
from searx.utils import get_engine_from_settings

if t.TYPE_CHECKING:
    import types
    from searx.enginelib import Engine
    from searx.search.models import SearchQuery
    from searx.results import ResultContainer
    from searx.result_types import Result, LegacyResult  # pyright: ignore[reportPrivateLocalImportUsage]


logger = logger.getChild("searx.search.processor")
SUSPENDED_STATUS: dict[int | str, "SuspendedStatus"] = {}


class RequestParams(t.TypedDict):
    """Basic quantity of the Request parameters of all engine types."""

    query: str
    """Search term, stripped of search syntax arguments."""

    category: str
    """Current category, like ``general``.

    .. hint::

       This field is deprecated, don't use it in further implementations.

    This field is currently *arbitrarily* filled with the name of "one""
    category (the name of the first category of the engine). In practice,
    however, it is not clear what this "one" category should be; in principle,
    multiple categories can also be activated in a search.
    """

    pageno: int
    """Current page number, where the first page is ``1``."""

    safesearch: t.Literal[0, 1, 2]
    """Safe-Search filter (0:normal, 1:moderate, 2:strict)."""

    time_range: t.Literal["day", "week", "month", "year"] | None
    """Time-range filter."""

    engine_data: dict[str, str]
    """Allows the transfer of (engine specific) data to the next request of the
    client.  In the case of the ``online`` engines, this data is delivered to
    the client via the HTML ``<form>`` in response.

    If the client then sends this form back to the server with the next request,
    this data will be available.

    This makes it possible to carry data from one request to the next without a
    session context, but this feature (is fragile) and should only be used in
    exceptional cases. See also :ref:`engine_data`."""

    searxng_locale: str
    """Language / locale filter from the search request, a string like 'all',
    'en', 'en-US', 'zh-HK' .. and others, for more details see
    :py:obj:`searx.locales`."""


class SuspendedStatus:
    """Class to handle suspend state."""

    def __init__(self):
        self.lock: threading.Lock = threading.Lock()
        self.continuous_errors: int = 0
        self.suspend_end_time: float = 0
        self.suspend_reason: str = ""

    @property
    def is_suspended(self):
        return self.suspend_end_time >= default_timer()

    def suspend(self, suspended_time: int | None, suspend_reason: str):
        with self.lock:
            # update continuous_errors / suspend_end_time
            self.continuous_errors += 1
            if suspended_time is None:
                max_ban: int = get_setting("search.max_ban_time_on_fail")
                ban_fail: int = get_setting("search.ban_time_on_fail")
                suspended_time = min(max_ban, ban_fail)

            self.suspend_end_time = default_timer() + suspended_time
            self.suspend_reason = suspend_reason
            logger.debug("Suspend for %i seconds", suspended_time)

    def resume(self):
        with self.lock:
            # reset the suspend variables
            self.continuous_errors = 0
            self.suspend_end_time = 0
            self.suspend_reason = ""


class EngineProcessor(ABC):
    """Base classes used for all types of request processors."""

    engine_type: str

    def __init__(self, engine: "Engine|types.ModuleType"):
        self.engine: "Engine" = engine  # pyright: ignore[reportAttributeAccessIssue]
        self.logger: logging.Logger = engines[engine.name].logger
        key = get_network(self.engine.name)
        key = id(key) if key else self.engine.name
        self.suspended_status: SuspendedStatus = SUSPENDED_STATUS.setdefault(key, SuspendedStatus())

    def initialize(self, callback: t.Callable[["EngineProcessor", bool], bool]):
        """Initialization of *this* :py:obj:`EngineProcessor`.

        If processor's engine has an ``init`` method, it is called first.
        Engine's ``init`` method is executed in a thread, meaning that the
        *registration* (the ``callback``) may occur later and is not already
        established by the return from this registration method.

        Registration only takes place if the ``init`` method is not available or
        is successfully run through.
        """

        if not hasattr(self.engine, "init"):
            callback(self, True)
            return

        if not callable(self.engine.init):
            logger.error("Engine's init method isn't a callable (is of type: %s).", type(self.engine.init))
            callback(self, False)
            return

        def __init_processor_thread():
            eng_ok = self.init_engine()
            callback(self, eng_ok)

        # set up and start a thread
        threading.Thread(target=__init_processor_thread, daemon=True).start()

    def init_engine(self) -> bool:
        eng_setting = get_engine_from_settings(self.engine.name)
        init_ok: bool | None = False
        try:
            init_ok = self.engine.init(eng_setting)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Init method of engine %s failed due to an exception.", self.engine.name)
            init_ok = False
        # In older engines, None is returned from the init method, which is
        # equivalent to indicating that the initialization was successful.
        if init_ok is None:
            init_ok = True
        return init_ok

    def handle_exception(
        self,
        result_container: "ResultContainer",
        exception_or_message: BaseException | str,
        suspend: bool = False,
    ):
        # update result_container
        if isinstance(exception_or_message, BaseException):
            exception_class = exception_or_message.__class__
            module_name = getattr(exception_class, '__module__', 'builtins')
            module_name = '' if module_name == 'builtins' else module_name + '.'
            error_message = module_name + exception_class.__qualname__
        else:
            error_message = exception_or_message
        result_container.add_unresponsive_engine(self.engine.name, error_message)
        # metrics
        counter_inc('engine', self.engine.name, 'search', 'count', 'error')
        if isinstance(exception_or_message, BaseException):
            count_exception(self.engine.name, exception_or_message)
        else:
            count_error(self.engine.name, exception_or_message)
        # suspend the engine ?
        if suspend:
            suspended_time = None
            if isinstance(exception_or_message, SearxEngineAccessDeniedException):
                suspended_time = exception_or_message.suspended_time
            self.suspended_status.suspend(suspended_time, error_message)  # pylint: disable=no-member

    def _extend_container_basic(
        self,
        result_container: "ResultContainer",
        start_time: float,
        search_results: "list[Result | LegacyResult]",
    ):
        # update result_container
        result_container.extend(self.engine.name, search_results)
        engine_time = default_timer() - start_time
        page_load_time = get_time_for_thread()
        result_container.add_timing(self.engine.name, engine_time, page_load_time)
        # metrics
        counter_inc('engine', self.engine.name, 'search', 'count', 'successful')
        histogram_observe(engine_time, 'engine', self.engine.name, 'time', 'total')
        if page_load_time is not None:
            histogram_observe(page_load_time, 'engine', self.engine.name, 'time', 'http')

    def extend_container(
        self,
        result_container: "ResultContainer",
        start_time: float,
        search_results: "list[Result | LegacyResult]|None",
    ):
        if getattr(threading.current_thread(), '_timeout', False):
            # the main thread is not waiting anymore
            self.handle_exception(result_container, 'timeout', False)
        else:
            # check if the engine accepted the request
            if search_results is not None:
                self._extend_container_basic(result_container, start_time, search_results)
            self.suspended_status.resume()

    def extend_container_if_suspended(self, result_container: "ResultContainer") -> bool:
        if self.suspended_status.is_suspended:
            result_container.add_unresponsive_engine(
                self.engine.name, self.suspended_status.suspend_reason, suspended=True
            )
            return True
        return False

    def get_params(self, search_query: "SearchQuery", engine_category: str) -> RequestParams | None:
        """Returns a dictionary with the :ref:`request parameters <engine
        request arguments>` (:py:obj:`RequestParams`), if the search condition
        is not supported by the engine, ``None`` is returned:

        - *time range* filter in search conditions, but the engine does not have
           a corresponding filter
        - page number > 1 when engine does not support paging
        - page number > ``max_page``

        """
        # if paging is not supported, skip
        if search_query.pageno > 1 and not self.engine.paging:
            return None

        # if max page is reached, skip
        max_page = self.engine.max_page or get_setting("search.max_page")
        if max_page and max_page < search_query.pageno:
            return None

        # if time_range is not supported, skip
        if search_query.time_range and not self.engine.time_range_support:
            return None

        params: RequestParams = {
            "query": search_query.query,
            "category": engine_category,
            "pageno": search_query.pageno,
            "safesearch": search_query.safesearch,
            "time_range": search_query.time_range,
            "engine_data": search_query.engine_data.get(self.engine.name, {}),
            "searxng_locale": search_query.lang,
        }

        # params["language"] is deprecated --> use params["searxng_locale"]
        #
        # Conditions related to engine's traits are implemented in engine.traits
        # module. Don't do "locale" decisions here in the abstract layer of the
        # search processor, just pass the value from user's choice unchanged to
        # the engine request.

        if hasattr(self.engine, "language") and self.engine.language:
            params["language"] = self.engine.language  # pyright: ignore[reportGeneralTypeIssues]
        else:
            params["language"] = search_query.lang  # pyright: ignore[reportGeneralTypeIssues]

        return params

    @abstractmethod
    def search(
        self,
        query: str,
        params: RequestParams,
        result_container: "ResultContainer",
        start_time: float,
        timeout_limit: float,
    ):
        pass

    def get_tests(self):
        # deprecated!
        return {}

    def get_default_tests(self):
        # deprecated!
        return {}
