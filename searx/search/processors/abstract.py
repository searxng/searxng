# SPDX-License-Identifier: AGPL-3.0-or-later

import threading
from abc import abstractmethod, ABC
from time import time

from searx import logger
from searx.engines import settings
from searx.network import get_time_for_thread
from searx.metrology.error_recorder import record_exception, record_error
from searx.exceptions import SearxEngineAccessDeniedException


logger = logger.getChild('searx.search.processor')


class EngineProcessor(ABC):

    __slots__ = 'engine', 'engine_name', 'suspend_end_time', 'suspend_reason', 'continuous_errors', 'lock'

    def __init__(self, engine, engine_name):
        self.engine = engine
        self.engine_name = engine_name
        self.suspend_end_time = 0
        self.suspend_reason = None
        self.continuous_errors = 0
        self.lock = threading.RLock()

    @property
    def is_suspended(self):
        return self.suspend_end_time >= time()

    def _suspend(self, suspended_time, suspend_reason):
        with self.lock:
            # update continuous_errors / suspend_end_time
            self.continuous_errors += 1
            if suspended_time is None:
                suspended_time = min(settings['search']['max_ban_time_on_fail'],
                                     self.continuous_errors * settings['search']['ban_time_on_fail'])
            self.suspend_end_time = time() + suspended_time
            self.suspend_reason = suspend_reason
        logger.debug('Suspend engine for %i seconds', suspended_time)

    def _resume(self):
        with self.lock:
            # reset the suspend variables
            self.continuous_errors = 0
            self.suspend_end_time = 0
            self.suspend_reason = None

    def handle_exception(self, result_container, reason, exception, suspend=False):
        # update result_container
        result_container.add_unresponsive_engine(self.engine_name, reason or str(exception))
        # metrics
        with self.lock:
            self.engine.stats['errors'] += 1
        if exception:
            record_exception(self.engine_name, exception)
        else:
            record_error(self.engine_name, reason)
        # suspend the engine ?
        if suspend:
            suspended_time = None
            if isinstance(exception, SearxEngineAccessDeniedException):
                suspended_time = exception.suspended_time
            self._suspend(suspended_time, reason or str(exception))  # pylint: disable=no-member

    def _extend_container_basic(self, result_container, start_time, search_results):
        # update result_container
        result_container.extend(self.engine_name, search_results)
        engine_time = time() - start_time
        page_load_time = get_time_for_thread()
        result_container.add_timing(self.engine_name, engine_time, page_load_time)
        # metrics
        with self.lock:
            self.engine.stats['engine_time'] += engine_time
            self.engine.stats['engine_time_count'] += 1
            # update stats with the total HTTP time
            if page_load_time is not None and 'page_load_time' in self.engine.stats:
                self.engine.stats['page_load_time'] += page_load_time
                self.engine.stats['page_load_count'] += 1

    def extend_container(self, result_container, start_time, search_results):
        if getattr(threading.current_thread(), '_timeout', False):
            # the main thread is not waiting anymore
            self.handle_exception(result_container, 'Timeout', None)
        else:
            # check if the engine accepted the request
            if search_results is not None:
                self._extend_container_basic(result_container, start_time, search_results)
            self._resume()

    def get_params(self, search_query, engine_category):
        # skip suspended engines
        if self.is_suspended:
            logger.debug('Engine currently suspended: %s', self.engine_name)
            return None

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
        else:
            return tests

    def get_default_tests(self):
        return {}
