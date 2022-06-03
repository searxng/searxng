# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint

"""Abstract base classes for engine request processores.

"""

import threading
from abc import abstractmethod, ABC
from timeit import default_timer
from typing import Dict, Union

from searx import settings, logger
from searx.engines import engines
from searx.network import get_time_for_thread, get_network
from searx.metrics import histogram_observe, counter_inc, count_exception, count_error
from searx.exceptions import SearxEngineAccessDeniedException, SearxEngineResponseException
from searx.utils import get_engine_from_settings

logger = logger.getChild('searx.search.processor')
SUSPENDED_STATUS: Dict[Union[int, str], 'SuspendedStatus'] = {}


class SuspendedStatus:
    """Class to handle suspend state."""

    __slots__ = 'suspend_end_time', 'suspend_reason', 'continuous_errors', 'lock'

    def __init__(self):
        self.lock = threading.Lock()
        self.continuous_errors = 0
        self.suspend_end_time = 0
        self.suspend_reason = None

    @property
    def is_suspended(self):
        return self.suspend_end_time >= default_timer()

    def suspend(self, suspended_time, suspend_reason):
        with self.lock:
            # update continuous_errors / suspend_end_time
            self.continuous_errors += 1
            if suspended_time is None:
                suspended_time = min(
                    settings['search']['max_ban_time_on_fail'],
                    self.continuous_errors * settings['search']['ban_time_on_fail'],
                )
            self.suspend_end_time = default_timer() + suspended_time
            self.suspend_reason = suspend_reason
            logger.debug('Suspend for %i seconds', suspended_time)

    def resume(self):
        with self.lock:
            # reset the suspend variables
            self.continuous_errors = 0
            self.suspend_end_time = 0
            self.suspend_reason = None


class EngineProcessor(ABC):
    """Base classes used for all types of reqest processores."""

    __slots__ = 'engine', 'engine_name', 'lock', 'suspended_status', 'logger'

    def __init__(self, engine, engine_name: str):
        self.engine = engine
        self.engine_name = engine_name
        self.logger = engines[engine_name].logger
        key = get_network(self.engine_name)
        key = id(key) if key else self.engine_name
        self.suspended_status = SUSPENDED_STATUS.setdefault(key, SuspendedStatus())

    def initialize(self):
        try:
            self.engine.init(get_engine_from_settings(self.engine_name))
        except SearxEngineResponseException as exc:
            self.logger.warn('Fail to initialize // %s', exc)
        except Exception:  # pylint: disable=broad-except
            self.logger.exception('Fail to initialize')
        else:
            self.logger.debug('Initialized')

    @property
    def has_initialize_function(self):
        return hasattr(self.engine, 'init')

    def handle_exception(self, result_container, exception_or_message, suspend=False):
        # update result_container
        if isinstance(exception_or_message, BaseException):
            exception_class = exception_or_message.__class__
            module_name = getattr(exception_class, '__module__', 'builtins')
            module_name = '' if module_name == 'builtins' else module_name + '.'
            error_message = module_name + exception_class.__qualname__
        else:
            error_message = exception_or_message
        result_container.add_unresponsive_engine(self.engine_name, error_message)
        # metrics
        counter_inc('engine', self.engine_name, 'search', 'count', 'error')
        if isinstance(exception_or_message, BaseException):
            count_exception(self.engine_name, exception_or_message)
        else:
            count_error(self.engine_name, exception_or_message)
        # suspend the engine ?
        if suspend:
            suspended_time = None
            if isinstance(exception_or_message, SearxEngineAccessDeniedException):
                suspended_time = exception_or_message.suspended_time
            self.suspended_status.suspend(suspended_time, error_message)  # pylint: disable=no-member

    def _extend_container_basic(self, result_container, start_time, search_results):
        # update result_container
        result_container.extend(self.engine_name, search_results)
        engine_time = default_timer() - start_time
        page_load_time = get_time_for_thread()
        result_container.add_timing(self.engine_name, engine_time, page_load_time)
        # metrics
        counter_inc('engine', self.engine_name, 'search', 'count', 'successful')
        histogram_observe(engine_time, 'engine', self.engine_name, 'time', 'total')
        if page_load_time is not None:
            histogram_observe(page_load_time, 'engine', self.engine_name, 'time', 'http')

    def extend_container(self, result_container, start_time, search_results):
        if getattr(threading.current_thread(), '_timeout', False):
            # the main thread is not waiting anymore
            self.handle_exception(result_container, 'timeout', None)
        else:
            # check if the engine accepted the request
            if search_results is not None:
                self._extend_container_basic(result_container, start_time, search_results)
            self.suspended_status.resume()

    def extend_container_if_suspended(self, result_container):
        if self.suspended_status.is_suspended:
            result_container.add_unresponsive_engine(
                self.engine_name, self.suspended_status.suspend_reason, suspended=True
            )
            return True
        return False

    def get_params(self, search_query, engine_category):
        # if paging is not supported, skip
        if search_query.pageno > 1 and not self.engine.paging:
            return None

        # if time_range is not supported, skip
        if search_query.time_range and not self.engine.time_range_support:
            return None

        params = {}
        params['category'] = engine_category
        params['pageno'] = search_query.pageno
        params['safesearch'] = search_query.safesearch
        params['time_range'] = search_query.time_range
        params['engine_data'] = search_query.engine_data.get(self.engine_name, {})

        if hasattr(self.engine, 'language') and self.engine.language:
            params['language'] = self.engine.language
        else:
            params['language'] = search_query.lang
        return params

    @abstractmethod
    def search(self, query, params, result_container, start_time, timeout_limit):
        pass

    def get_tests(self):
        tests = getattr(self.engine, 'tests', None)
        if tests is None:
            tests = getattr(self.engine, 'additional_tests', {})
            tests.update(self.get_default_tests())
        return tests

    def get_default_tests(self):
        return {}
