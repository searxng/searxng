# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring

import typing
import math
import contextlib
from timeit import default_timer
from operator import itemgetter

from searx.engines import engines
from .models import HistogramStorage, CounterStorage, VoidHistogram, VoidCounterStorage
from .error_recorder import count_error, count_exception, errors_per_engines

__all__ = [
    "initialize",
    "get_engines_stats",
    "get_engine_errors",
    "histogram",
    "histogram_observe",
    "histogram_observe_time",
    "counter",
    "counter_inc",
    "counter_add",
    "count_error",
    "count_exception",
]


ENDPOINTS = {'search'}


histogram_storage: typing.Optional[HistogramStorage] = None
counter_storage: typing.Optional[CounterStorage] = None


@contextlib.contextmanager
def histogram_observe_time(*args):
    h = histogram_storage.get(*args)
    before = default_timer()
    yield before
    duration = default_timer() - before
    if h:
        h.observe(duration)
    else:
        raise ValueError("histogram " + repr((*args,)) + " doesn't not exist")


def histogram_observe(duration, *args):
    histogram_storage.get(*args).observe(duration)


def histogram(*args, raise_on_not_found=True):
    h = histogram_storage.get(*args)
    if raise_on_not_found and h is None:
        raise ValueError("histogram " + repr((*args,)) + " doesn't not exist")
    return h


def counter_inc(*args):
    counter_storage.add(1, *args)


def counter_add(value, *args):
    counter_storage.add(value, *args)


def counter(*args):
    return counter_storage.get(*args)


def initialize(engine_names=None, enabled=True):
    """
    Initialize metrics
    """
    global counter_storage, histogram_storage  # pylint: disable=global-statement

    if enabled:
        counter_storage = CounterStorage()
        histogram_storage = HistogramStorage()
    else:
        counter_storage = VoidCounterStorage()
        histogram_storage = HistogramStorage(histogram_class=VoidHistogram)

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
        counter_storage.configure('engine', engine_name, 'search', 'count', 'sent')
        counter_storage.configure('engine', engine_name, 'search', 'count', 'successful')
        # global counter of errors
        counter_storage.configure('engine', engine_name, 'search', 'count', 'error')
        # score of the engine
        counter_storage.configure('engine', engine_name, 'score')
        # result count per requests
        histogram_storage.configure(1, 100, 'engine', engine_name, 'result', 'count')
        # time doing HTTP requests
        histogram_storage.configure(histogram_width, histogram_size, 'engine', engine_name, 'time', 'http')
        # total time
        # .time.request and ...response times may overlap .time.http time.
        histogram_storage.configure(histogram_width, histogram_size, 'engine', engine_name, 'time', 'total')


def get_engine_errors(engline_name_list):
    result = {}
    engine_names = list(errors_per_engines.keys())
    engine_names.sort()
    for engine_name in engine_names:
        if engine_name not in engline_name_list:
            continue

        error_stats = errors_per_engines[engine_name]
        sent_search_count = max(counter('engine', engine_name, 'search', 'count', 'sent'), 1)
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


def get_reliabilities(engline_name_list, checker_results):
    reliabilities = {}

    engine_errors = get_engine_errors(engline_name_list)

    for engine_name in engline_name_list:
        checker_result = checker_results.get(engine_name, {})
        checker_success = checker_result.get('success', True)
        errors = engine_errors.get(engine_name) or []
        if counter('engine', engine_name, 'search', 'count', 'sent') == 0:
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


def get_engines_stats(engine_name_list):
    assert counter_storage is not None
    assert histogram_storage is not None

    list_time = []
    max_time_total = max_result_count = None

    for engine_name in engine_name_list:

        sent_count = counter('engine', engine_name, 'search', 'count', 'sent')
        if sent_count == 0:
            continue

        result_count = histogram('engine', engine_name, 'result', 'count').percentage(50)
        result_count_sum = histogram('engine', engine_name, 'result', 'count').sum
        successful_count = counter('engine', engine_name, 'search', 'count', 'successful')

        time_total = histogram('engine', engine_name, 'time', 'total').percentage(50)
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
            score = counter('engine', engine_name, 'score')

            stats['score'] = score
            stats['score_per_result'] = score / float(result_count_sum)

        time_http = histogram('engine', engine_name, 'time', 'http').percentage(50)
        time_http_p80 = time_http_p95 = 0

        if time_http is not None:

            time_http_p80 = histogram('engine', engine_name, 'time', 'http').percentage(80)
            time_http_p95 = histogram('engine', engine_name, 'time', 'http').percentage(95)

            stats['http'] = round(time_http, 1)
            stats['http_p80'] = round(time_http_p80, 1)
            stats['http_p95'] = round(time_http_p95, 1)

        if time_total is not None:

            time_total_p80 = histogram('engine', engine_name, 'time', 'total').percentage(80)
            time_total_p95 = histogram('engine', engine_name, 'time', 'total').percentage(95)

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
