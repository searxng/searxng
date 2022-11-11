# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring
# pyright: basic

import json
import time
import threading
import os
import signal
from typing import Dict, Union, List, Any, Tuple, Optional
from typing_extensions import TypedDict, Literal

import redis.exceptions

from searx import logger, settings, searx_debug
from searx.redisdb import client as get_redis_client
from searx.exceptions import SearxSettingsException
from searx.search.processors import PROCESSORS
from searx.search.checker import Checker
from searx.search.checker.scheduler import scheduler_function


REDIS_RESULT_KEY = 'SearXNG_checker_result'
REDIS_LOCK_KEY = 'SearXNG_checker_lock'


CheckerResult = Union['CheckerOk', 'CheckerErr', 'CheckerOther']


class CheckerOk(TypedDict):
    """Checking the engines succeeded"""

    status: Literal['ok']
    engines: Dict[str, 'EngineResult']
    timestamp: int


class CheckerErr(TypedDict):
    """Checking the engines failed"""

    status: Literal['error']
    timestamp: int


class CheckerOther(TypedDict):
    """The status is unknown or disabled"""

    status: Literal['unknown', 'disabled']


EngineResult = Union['EngineOk', 'EngineErr']


class EngineOk(TypedDict):
    """Checking the engine succeeded"""

    success: Literal[True]


class EngineErr(TypedDict):
    """Checking the engine failed"""

    success: Literal[False]
    errors: Dict[str, List[str]]


def _get_interval(every: Any, error_msg: str) -> Tuple[int, int]:
    if isinstance(every, int):
        return (every, every)

    if (
        not isinstance(every, (tuple, list))
        or len(every) != 2  # type: ignore
        or not isinstance(every[0], int)
        or not isinstance(every[1], int)
    ):
        raise SearxSettingsException(error_msg, None)
    return (every[0], every[1])


def get_result() -> CheckerResult:
    client = get_redis_client()
    if client is None:
        # without Redis, the checker is disabled
        return {'status': 'disabled'}
    serialized_result: Optional[bytes] = client.get(REDIS_RESULT_KEY)
    if serialized_result is None:
        # the Redis key does not exist
        return {'status': 'unknown'}
    return json.loads(serialized_result)


def _set_result(result: CheckerResult):
    client = get_redis_client()
    if client is None:
        # without Redis, the function does nothing
        return
    client.set(REDIS_RESULT_KEY, json.dumps(result))


def _timestamp():
    return int(time.time() / 3600) * 3600


def run():
    try:
        # use a Redis lock to make sure there is no checker running at the same time
        # (this should not happen, this is a safety measure)
        with get_redis_client().lock(REDIS_LOCK_KEY, blocking_timeout=60, timeout=3600):
            logger.info('Starting checker')
            result: CheckerOk = {'status': 'ok', 'engines': {}, 'timestamp': _timestamp()}
            for name, processor in PROCESSORS.items():
                logger.debug('Checking %s engine', name)
                checker = Checker(processor)
                checker.run()
                if checker.test_results.successful:
                    result['engines'][name] = {'success': True}
                else:
                    result['engines'][name] = {'success': False, 'errors': checker.test_results.errors}

            _set_result(result)
            logger.info('Check done')
    except redis.exceptions.LockError:
        _set_result({'status': 'error', 'timestamp': _timestamp()})
        logger.exception('Error while running the checker')
    except Exception:  # pylint: disable=broad-except
        _set_result({'status': 'error', 'timestamp': _timestamp()})
        logger.exception('Error while running the checker')


def _signal_handler(_signum: int, _frame: Any):
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()


def initialize():
    if hasattr(signal, 'SIGUSR1'):
        # Windows doesn't support SIGUSR1
        logger.info('Send SIGUSR1 signal to pid %i to start the checker', os.getpid())
        signal.signal(signal.SIGUSR1, _signal_handler)

    # special case when debug is activate
    if searx_debug and settings['checker']['off_when_debug']:
        logger.info('debug mode: checker is disabled')
        return

    # check value of checker.scheduling.every now
    scheduling = settings['checker']['scheduling']
    if scheduling is None or not scheduling:
        logger.info('Checker scheduler is disabled')
        return

    # make sure there is a Redis connection
    if get_redis_client() is None:
        logger.error('The checker requires Redis')
        return

    # start the background scheduler
    every_range = _get_interval(scheduling.get('every', (300, 1800)), 'checker.scheduling.every is not a int or list')
    start_after_range = _get_interval(
        scheduling.get('start_after', (300, 1800)), 'checker.scheduling.start_after is not a int or list'
    )
    t = threading.Thread(
        target=scheduler_function,
        args=(start_after_range[0], start_after_range[1], every_range[0], every_range[1], run),
        name='checker_scheduler',
    )
    t.daemon = True
    t.start()
