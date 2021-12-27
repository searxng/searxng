# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Shared testing code."""

# pylint: disable=missing-function-docstring

import sys
import os
import subprocess
import traceback
import pathlib

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

        # The Flask app is started by Flask.run(...), don't enable Flask's debug
        # mode, the debugger from Flask will cause wired process model, where
        # the server never dies.  Further read:
        #
        # - debug mode: https://flask.palletsprojects.com/quickstart/#debug-mode
        # - Flask.run(..): https://flask.palletsprojects.com/api/#flask.Flask.run

        os.environ['SEARXNG_DEBUG'] = '0'

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
    for test in tests:
        with Browser('firefox', headless=True, profile_preferences={'intl.accept_languages': 'en'}) as browser:
            test(browser)


def main():
    test_layer = SearxRobotLayer()
    try:
        test_layer.setUp()
        run_robot_tests([getattr(test_webapp, x) for x in dir(test_webapp) if x.startswith('test_')])
    except Exception:  # pylint: disable=broad-except
        print('Error occured: {0}'.format(traceback.format_exc()))
        sys.exit(1)
    finally:
        test_layer.tearDown()


if __name__ == '__main__':
    main()
