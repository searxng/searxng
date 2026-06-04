# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name
"""Shared testing code."""

import sys
import os
import subprocess
import traceback
import pathlib
import shutil

from time import sleep

from splinter import Browser

import tests as searx_tests
from tests.robot import test_webapp


class SearxRobotLayer:
    """Searx Robot Test Layer"""

    def setUp(self):
        os.setpgrp()  # create new process group, become its leader

        tests_path = pathlib.Path(searx_tests.__file__).resolve().parent

        # get program paths
        webapp = str(tests_path.parent / 'searx' / 'webapp.py')
        exe = 'python'

        # set robot settings path
        os.environ['SEARXNG_SETTINGS_PATH'] = str(tests_path / 'robot' / 'settings_robot.yml')

        # run the server
        self.server = subprocess.Popen(  # pylint: disable=consider-using-with
            [exe, webapp], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if hasattr(self.server.stdout, 'read1'):
            print(self.server.stdout.read1(1024).decode())

    def tearDown(self):
        os.kill(self.server.pid, 9)
        # remove previously set environment variable
        del os.environ['SEARXNG_SETTINGS_PATH']


def _format_log_entry(entry):
    """Build a readable one-line message from a BiDi log entry."""
    level = getattr(entry, 'level', None) or '?'
    text = getattr(entry, 'text', None) or repr(entry)
    return '[{0}] {1}'.format(level, text)


def _collect_browser_errors(browser):
    """Register WebDriver BiDi handlers that collect JavaScript errors and
    error-level console messages emitted by the browser.

    The returned list is filled asynchronously while the test interacts with
    the page, so it must be inspected only after the test has finished.
    """
    errors = []

    script = browser.driver.script
    script.add_javascript_error_handler(lambda entry: errors.append(_format_log_entry(entry)))

    def on_console_message(entry):
        if getattr(entry, 'level', None) == 'error':
            errors.append(_format_log_entry(entry))

    script.add_console_message_handler(on_console_message)
    return errors


def run_robot_tests(tests):
    print('Running {0} tests'.format(len(tests)))
    print(f'{shutil.which("geckodriver")}')
    print(f'{shutil.which("firefox")}')

    failures = []
    for test in tests:
        # 'webSocketUrl' enables the WebDriver BiDi protocol, which lets us
        # subscribe to the browser's log entries (see _collect_browser_errors).
        with Browser(
            'firefox',
            headless=True,
            profile_preferences={'intl.accept_languages': 'en'},
            capabilities={'webSocketUrl': True},
        ) as browser:
            errors = _collect_browser_errors(browser)
            test(browser)
            # give the asynchronous BiDi log events a moment to be delivered
            sleep(1)
            if errors:
                failures.append((test.__name__, errors))

    if failures:
        report = ['JavaScript errors were detected in the browser console:']
        for name, errors in failures:
            report.append('  {0}:'.format(name))
            report.extend('    - {0}'.format(error) for error in errors)
        raise AssertionError('\n'.join(report))


def main():
    test_layer = SearxRobotLayer()
    try:
        test_layer.setUp()
        run_robot_tests([getattr(test_webapp, x) for x in dir(test_webapp) if x.startswith('test_')])
    except Exception:  # pylint: disable=broad-except
        print('Error occurred: {0}'.format(traceback.format_exc()))
        sys.exit(1)
    finally:
        test_layer.tearDown()


if __name__ == '__main__':
    main()
