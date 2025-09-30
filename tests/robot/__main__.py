# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name
"""Shared testing code."""

import sys
import os
import subprocess
import traceback
import pathlib
import shutil

from splinter import Browser

import tests as zhensa_tests
from tests.robot import test_webapp


class SearxRobotLayer:
    """Searx Robot Test Layer"""

    def setUp(self):
        os.setpgrp()  # create new process group, become its leader

        tests_path = pathlib.Path(zhensa_tests.__file__).resolve().parent

        # get program paths
        webapp = str(tests_path.parent / 'zhensa' / 'webapp.py')
        exe = 'python'

        # set robot settings path
        os.environ['ZHENSA_SETTINGS_PATH'] = str(tests_path / 'robot' / 'settings_robot.yml')

        # run the server
        self.server = subprocess.Popen(  # pylint: disable=consider-using-with
            [exe, webapp], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if hasattr(self.server.stdout, 'read1'):
            print(self.server.stdout.read1(1024).decode())

    def tearDown(self):
        os.kill(self.server.pid, 9)
        # remove previously set environment variable
        del os.environ['ZHENSA_SETTINGS_PATH']


def run_robot_tests(tests):
    print('Running {0} tests'.format(len(tests)))
    print(f'{shutil.which("geckodriver")}')
    print(f'{shutil.which("firefox")}')

    for test in tests:
        with Browser('firefox', headless=True, profile_preferences={'intl.accept_languages': 'en'}) as browser:
            test(browser)


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
