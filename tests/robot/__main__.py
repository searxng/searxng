# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name
"""Shared testing code."""

import sys
import os
import subprocess
import traceback
import pathlib
import shutil

from selenium.webdriver.firefox.options import Options as FirefoxOptions
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


def run_robot_tests(tests):
    print('Running {0} tests'.format(len(tests)))
    print(f'{shutil.which("geckodriver")}')
    print(f'{shutil.which("firefox")}')

    js_errors = []
    for test in tests:
        options = FirefoxOptions()
        options.enable_bidi = True
        with Browser(
            'firefox', headless=True, options=options, profile_preferences={'intl.accept_languages': 'en'}
        ) as browser:
            errors = []
            browser.driver.script.add_javascript_error_handler(errors.append)
            browser.driver.script.add_console_message_handler(
                lambda entry: errors.append(entry) if entry.level == 'error' else None
            )
            test(browser)
            for err in errors:
                js_errors.append(f'{test.__name__}: {err.text}')

    if js_errors:
        raise AssertionError('JavaScript errors in the browser console:\n  ' + '\n  '.join(js_errors))


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
