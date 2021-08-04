# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Shared testing code."""

# pylint: disable=missing-function-docstring

import os
import subprocess
import traceback

from os.path import dirname, join, abspath, realpath

from splinter import Browser
import aiounittest


class SearxTestLayer:
    """Base layer for non-robot tests."""

    __name__ = 'SearxTestLayer'

    @classmethod
    def setUp(cls):
        pass

    @classmethod
    def tearDown(cls):
        pass

    @classmethod
    def testSetUp(cls):
        pass

    @classmethod
    def testTearDown(cls):
        pass


class SearxRobotLayer():
    """Searx Robot Test Layer"""

    def setUp(self):
        os.setpgrp()  # create new process group, become its leader

        # get program paths
        webapp = join(abspath(dirname(realpath(__file__))), 'webapp.py')
        exe = 'python'

        # The Flask app is started by Flask.run(...), don't enable Flask's debug
        # mode, the debugger from Flask will cause wired process model, where
        # the server never dies.  Further read:
        #
        # - debug mode: https://flask.palletsprojects.com/quickstart/#debug-mode
        # - Flask.run(..): https://flask.palletsprojects.com/api/#flask.Flask.run

        os.environ['SEARX_DEBUG'] = '0'

        # set robot settings path
        os.environ['SEARX_SETTINGS_PATH'] = abspath(
            dirname(__file__) + '/settings_robot.yml')

        # run the server
        self.server = subprocess.Popen(  # pylint: disable=consider-using-with
            [exe, webapp],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        if hasattr(self.server.stdout, 'read1'):
            print(self.server.stdout.read1(1024).decode())

    def tearDown(self):
        os.kill(self.server.pid, 9)
        # remove previously set environment variable
        del os.environ['SEARX_SETTINGS_PATH']


# SEARXROBOTLAYER = SearxRobotLayer()
def run_robot_tests(tests):
    print('Running {0} tests'.format(len(tests)))
    for test in tests:
        with Browser('firefox', headless=True, profile_preferences={'intl.accept_languages': 'en'}) as browser:
            test(browser)


class SearxTestCase(aiounittest.AsyncTestCase):
    """Base test case for non-robot tests."""

    layer = SearxTestLayer

    def setattr4test(self, obj, attr, value):
        """
        setattr(obj, attr, value)
        but reset to the previous value in the cleanup.
        """
        previous_value = getattr(obj, attr)

        def cleanup_patch():
            setattr(obj, attr, previous_value)
        self.addCleanup(cleanup_patch)
        setattr(obj, attr, value)


if __name__ == '__main__':
    import sys
    # test cases
    from tests import robot

    base_dir = abspath(join(dirname(__file__), '../tests'))
    if sys.argv[1] == 'robot':
        test_layer = SearxRobotLayer()
        errors = False
        try:
            test_layer.setUp()
            run_robot_tests([getattr(robot, x) for x in dir(robot) if x.startswith('test_')])
        except Exception:  # pylint: disable=broad-except
            errors = True
            print('Error occured: {0}'.format(traceback.format_exc()))
        test_layer.tearDown()
        sys.exit(1 if errors else 0)
