# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring
"""Lame scheduler which use Redis as a source of truth:
* the Redis key SearXNG_checker_next_call_ts contains the next time the embedded checker should run.
* to avoid lock, a unique Redis script reads and updates the Redis key SearXNG_checker_next_call_ts.
* this Redis script returns a list of two elements:
   * the first one is a boolean. If True, the embedded checker must run now in this worker.
   * the second element is the delay in second to wait before the next call to the Redis script.

This scheduler is not generic on purpose: if more feature are required, a dedicate scheduler must be used
(= a better scheduler should not use the web workers)
"""

import logging
import time
import importlib
from typing import Callable

from searx.redisdb import client as get_redis_client
from searx.redislib import lua_script_storage


logger = logging.getLogger('searx.search.checker')


def scheduler_function(start_after_from: int, start_after_to: int, every_from: int, every_to: int, callback: Callable):
    """Run the checker periodically. The function never returns.

    Parameters:
    * start_after_from and start_after_to: when to call "callback" for the first on the Redis instance
    * every_from and every_to: after the first call, how often to call "callback"

    There is no issue:
    * to call this function is multiple workers
    * to kill workers at any time as long there is one at least one worker
    """
    scheduler_now_script = importlib.resources.read_text(__package__, "scheduler.lua")
    while True:
        # ask the Redis script what to do
        # the script says
        # * if the checker must run now.
        # * how to long to way before calling the script again (it can be call earlier, but not later).
        script = lua_script_storage(get_redis_client(), scheduler_now_script)
        call_now, wait_time = script(args=[start_after_from, start_after_to, every_from, every_to])

        # does the worker run the checker now?
        if call_now:
            # run the checker
            try:
                callback()
            except Exception:  # pylint: disable=broad-except
                logger.exception("Error calling the embedded checker")
            # only worker display the wait_time
            logger.info("Next call to the checker in %s seconds", wait_time)
        # wait until the next call
        time.sleep(wait_time)
