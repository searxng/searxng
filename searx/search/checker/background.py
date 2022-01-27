# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring
# pyright: strict

import json
import random
import time
import threading
import os
import signal
from typing import Dict, Union, List, Any, Tuple
from typing_extensions import TypedDict, Literal

from searx import logger, settings, searx_debug
from searx.exceptions import SearxSettingsException
from searx.search.processors import PROCESSORS
from searx.search.checker import Checker
from searx.shared import schedule, storage


CHECKER_RESULT = 'CHECKER_RESULT'
running = threading.Lock()


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


def _get_every():
    every = settings.get('checker', {}).get('scheduling', {}).get('every', (300, 1800))
    return _get_interval(every, 'checker.scheduling.every is not a int or list')


def get_result() -> CheckerResult:
    serialized_result = storage.get_str(CHECKER_RESULT)
    if serialized_result is not None:
        return json.loads(serialized_result)
    return {'status': 'unknown'}


def _set_result(result: CheckerResult):
    storage.set_str(CHECKER_RESULT, json.dumps(result))


def _timestamp():
    return int(time.time() / 3600) * 3600


def run():
    if not running.acquire(blocking=False):  # pylint: disable=consider-using-with
        return
    try:
        logger.info('Starting checker')
        result: CheckerOk = {'status': 'ok', 'engines': {}, 'timestamp': _timestamp()}
        for name, processor in PROCESSORS.items():
            logger.debug('Checking %s engine', name)
            checker = Checker(processor)
            checker.run()
            if checker.test_results.succesfull:
                result['engines'][name] = {'success': True}
            else:
                result['engines'][name] = {'success': False, 'errors': checker.test_results.errors}

        _set_result(result)
        logger.info('Check done')
    except Exception:  # pylint: disable=broad-except
        _set_result({'status': 'error', 'timestamp': _timestamp()})
        logger.exception('Error while running the checker')
    finally:
        running.release()


def _run_with_delay():
    every = _get_every()
    delay = random.randint(0, every[1] - every[0])
    logger.debug('Start checker in %i seconds', delay)
    time.sleep(delay)
    run()


def _start_scheduling():
    every = _get_every()
    if schedule(every[0], _run_with_delay):
        run()


def _signal_handler(_signum: int, _frame: Any):
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()


def initialize():
    if hasattr(signal, 'SIGUSR1'):
        # Windows doesn't support SIGUSR1
        logger.info('Send SIGUSR1 signal to pid %i to start the checker', os.getpid())
        signal.signal(signal.SIGUSR1, _signal_handler)

    # disabled by default
    _set_result({'status': 'disabled'})

    # special case when debug is activate
    if searx_debug and settings.get('checker', {}).get('off_when_debug', True):
        logger.info('debug mode: checker is disabled')
        return

    # check value of checker.scheduling.every now
    scheduling = settings.get('checker', {}).get('scheduling', None)
    if scheduling is None or not scheduling:
        logger.info('Checker scheduler is disabled')
        return

    #
    _set_result({'status': 'unknown'})

    start_after = scheduling.get('start_after', (300, 1800))
    start_after = _get_interval(start_after, 'checker.scheduling.start_after is not a int or list')
    delay = random.randint(start_after[0], start_after[1])
    logger.info('Start checker in %i seconds', delay)
    t = threading.Timer(delay, _start_scheduling)
    t.daemon = True
    t.start()
