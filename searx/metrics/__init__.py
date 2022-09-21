# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring

import math
import contextlib
from timeit import default_timer

from typing import Dict, List, Optional, Any
from typing_extensions import TypedDict

from searx.engines import engines
from .models import Histogram, HistogramStorage, CounterStorage, VoidHistogram, VoidCounterStorage
from .error_recorder import count_error, count_exception, errors_per_engines

__all__ = [
    "initialize",
    "get_engines_metrics",
    "get_engine_errors",
    "count_error",
    "count_exception",
]


HISTOGRAM_STORAGE: Optional[HistogramStorage] = None
COUNTER_STORAGE: Optional[CounterStorage] = None


# We do not have a usage of this context manager
#
# @contextlib.contextmanager
# def histogram_observe_time(*args):
#     h = histogram_storage.get(*args)
#     before = default_timer()
#     yield before
#     duration = default_timer() - before
#     if h:
#         h.observe(duration)
#     else:
#         raise ValueError("histogram " + repr((*args,)) + " doesn't not exist")


def initialize(engine_names=None, enabled=True):
    """
    Initialize metrics
    """

    global COUNTER_STORAGE, HISTOGRAM_STORAGE  # pylint: disable=global-statement

    if enabled:
        COUNTER_STORAGE = CounterStorage()
        HISTOGRAM_STORAGE = HistogramStorage()
    else:
        COUNTER_STORAGE = VoidCounterStorage()
        HISTOGRAM_STORAGE = HistogramStorage(histogram_class=VoidHistogram)

    # max_timeout = max of all the engine.timeout
    max_timeout = 2
    for engine_name in engine_names or engines:
        if engine_name in engines:
            max_timeout = max(max_timeout, engines[engine_name].timeout)

    # histogram configuration
    histogram_width = 0.1
    histogram_size = int(1.5 * max_timeout / histogram_width)

    # engines
    for engine_name in engine_names or engines:
        # search count
        COUNTER_STORAGE.configure('engine', engine_name, 'search', 'count', 'sent')
        COUNTER_STORAGE.configure('engine', engine_name, 'search', 'count', 'successful')
        # global counter of errors
        COUNTER_STORAGE.configure('engine', engine_name, 'search', 'count', 'error')
        # score of the engine
        COUNTER_STORAGE.configure('engine', engine_name, 'score')
        # result count per requests
        HISTOGRAM_STORAGE.configure(1, 100, 'engine', engine_name, 'result', 'count')
        # time doing HTTP requests
        HISTOGRAM_STORAGE.configure(histogram_width, histogram_size, 'engine', engine_name, 'time', 'http')
        # total time
        # .time.request and ...response times may overlap .time.http time.
        HISTOGRAM_STORAGE.configure(histogram_width, histogram_size, 'engine', engine_name, 'time', 'total')


class EngineError(TypedDict):
    """Describe an engine error. To do : check the types"""

    filename: str
    function: str
    line_no: int
    code: str
    exception_classname: str
    log_message: str
    log_parameters: List[str]
    secondary: bool
    percentage: int


def get_engine_errors(engline_name_list) -> Dict[str, List[EngineError]]:
    result = {}
    engine_names = list(errors_per_engines.keys())
    engine_names.sort()
    for engine_name in engine_names:
        if engine_name not in engline_name_list:
            continue

        error_stats = errors_per_engines[engine_name]
        sent_search_count = max(COUNTER_STORAGE.get('engine', engine_name, 'search', 'count', 'sent'), 1)
        sorted_context_count_list = sorted(error_stats.items(), key=lambda context_count: context_count[1])
        r = []
        for context, count in sorted_context_count_list:
            percentage = round(20 * count / sent_search_count) * 5
            r.append(
                {
                    'filename': context.filename,
                    'function': context.function,
                    'line_no': context.line_no,
                    'code': context.code,
                    'exception_classname': context.exception_classname,
                    'log_message': context.log_message,
                    'log_parameters': context.log_parameters,
                    'secondary': context.secondary,
                    'percentage': percentage,
                }
            )
        result[engine_name] = sorted(r, reverse=True, key=lambda d: d['percentage'])
    return result


class EngineReliability(TypedDict):
    """Describe the engine reliability. To do: update the checker field type"""

    reliability: int
    errors: List[EngineError]
    checker: Optional[Any]


def get_reliabilities(engline_name_list, checker_results) -> Dict[str, EngineReliability]:
    reliabilities = {}

    engine_errors = get_engine_errors(engline_name_list)

    for engine_name in engline_name_list:
        checker_result = checker_results.get(engine_name, {})
        checker_success = checker_result.get('success', True)
        errors = engine_errors.get(engine_name) or []
        if COUNTER_STORAGE.get('engine', engine_name, 'search', 'count', 'sent') == 0:
            # no request
            reliablity = None
        elif checker_success and not errors:
            reliablity = 100
        elif 'simple' in checker_result.get('errors', {}):
            # the basic (simple) test doesn't work: the engine is broken accoding to the checker
            # even if there is no exception
            reliablity = 0
        else:
            # pylint: disable=consider-using-generator
            reliablity = 100 - sum([error['percentage'] for error in errors if not error.get('secondary')])

        reliabilities[engine_name] = {
            'reliablity': reliablity,
            'errors': errors,
            'checker': checker_results.get(engine_name, {}).get('errors', {}),
        }
    return reliabilities


class EngineStat(TypedDict):
    """Metrics for one engine. To do: check the types"""

    name: str
    total: Optional[float]
    total_p80: Optional[float]
    totla_p95: Optional[float]
    http: Optional[float]
    http_p80: Optional[float]
    http_p95: Optional[float]
    processing: Optional[float]
    processing_p80: Optional[float]
    processing_p95: Optional[float]
    score: float
    score_per_result: float
    result_count: int


class EngineStatResult(TypedDict):
    """result of the get_engines_metrics function"""

    time: List[EngineStat]
    """List of engine stat"""

    max_time: float
    """Maximum response time for all the engines"""

    max_result_count: int
    """Maximum number of result for all the engines"""


def get_engines_metrics(engine_name_list) -> EngineStatResult:
    assert COUNTER_STORAGE is not None
    assert HISTOGRAM_STORAGE is not None

    list_time = []
    max_time_total = max_result_count = None

    for engine_name in engine_name_list:

        sent_count = COUNTER_STORAGE.get('engine', engine_name, 'search', 'count', 'sent')
        if sent_count == 0:
            continue

        result_count = HISTOGRAM_STORAGE.get('engine', engine_name, 'result', 'count').percentile(50)
        result_count_sum = HISTOGRAM_STORAGE.get('engine', engine_name, 'result', 'count').sum
        successful_count = COUNTER_STORAGE.get('engine', engine_name, 'search', 'count', 'successful')

        time_total = HISTOGRAM_STORAGE.get('engine', engine_name, 'time', 'total').percentile(50)
        max_time_total = max(time_total or 0, max_time_total or 0)
        max_result_count = max(result_count or 0, max_result_count or 0)

        stats = {
            'name': engine_name,
            'total': None,
            'total_p80': None,
            'total_p95': None,
            'http': None,
            'http_p80': None,
            'http_p95': None,
            'processing': None,
            'processing_p80': None,
            'processing_p95': None,
            'score': 0,
            'score_per_result': 0,
            'result_count': result_count,
        }

        if successful_count and result_count_sum:
            score = COUNTER_STORAGE.get('engine', engine_name, 'score')

            stats['score'] = score
            stats['score_per_result'] = score / float(result_count_sum)

        time_http = HISTOGRAM_STORAGE.get('engine', engine_name, 'time', 'http').percentile(50)
        time_http_p80 = time_http_p95 = 0

        if time_http is not None:

            time_http_p80 = HISTOGRAM_STORAGE.get('engine', engine_name, 'time', 'http').percentile(80)
            time_http_p95 = HISTOGRAM_STORAGE.get('engine', engine_name, 'time', 'http').percentile(95)

            stats['http'] = round(time_http, 1)
            stats['http_p80'] = round(time_http_p80, 1)
            stats['http_p95'] = round(time_http_p95, 1)

        if time_total is not None:

            time_total_p80 = HISTOGRAM_STORAGE.get('engine', engine_name, 'time', 'total').percentile(80)
            time_total_p95 = HISTOGRAM_STORAGE.get('engine', engine_name, 'time', 'total').percentile(95)

            stats['total'] = round(time_total, 1)
            stats['total_p80'] = round(time_total_p80, 1)
            stats['total_p95'] = round(time_total_p95, 1)

            stats['processing'] = round(time_total - (time_http or 0), 1)
            stats['processing_p80'] = round(time_total_p80 - time_http_p80, 1)
            stats['processing_p95'] = round(time_total_p95 - time_http_p95, 1)

        list_time.append(stats)

    return {
        'time': list_time,
        'max_time': math.ceil(max_time_total or 0),
        'max_result_count': math.ceil(max_result_count or 0),
    }
