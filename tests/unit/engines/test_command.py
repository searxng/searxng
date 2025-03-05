# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

from searx.engines import command as command_engine
from searx.result_types import KeyValue

from tests import SearxTestCase


class TestCommandEngine(SearxTestCase):

    def test_basic_seq_command_engine(self):
        ls_engine = command_engine
        ls_engine.command = ['seq', '{{QUERY}}']
        ls_engine.delimiter = {'chars': ' ', 'keys': ['number']}
        expected_results = [
            KeyValue(kvmap={'number': 1}),
            KeyValue(kvmap={'number': 2}),
            KeyValue(kvmap={'number': 3}),
            KeyValue(kvmap={'number': 4}),
            KeyValue(kvmap={'number': 5}),
        ]
        results = ls_engine.search('5', {'pageno': 1})
        for i, expected in enumerate(expected_results):
            self.assertEqual(results[i].kvmap["number"], str(expected.kvmap["number"]))

    def test_delimiter_parsing(self):
        searx_logs = '''DEBUG:searx.webapp:static directory is /home/n/p/searx/searx/static
DEBUG:searx.webapp:templates directory is /home/n/p/searx/searx/templates
DEBUG:searx.engines:soundcloud engine: Starting background initialization
DEBUG:searx.engines:wolframalpha engine: Starting background initialization
DEBUG:searx.engines:locate engine: Starting background initialization
DEBUG:searx.engines:regex search in files engine: Starting background initialization
DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): www.wolframalpha.com
DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): soundcloud.com
DEBUG:searx.engines:find engine: Starting background initialization
DEBUG:searx.engines:pattern search in files engine: Starting background initialization
DEBUG:searx.webapp:starting webserver on 127.0.0.1:8888
WARNING:werkzeug: * Debugger is active!
INFO:werkzeug: * Debugger PIN: 299-578-362'''
        echo_engine = command_engine
        echo_engine.command = ['echo', searx_logs]
        echo_engine.delimiter = {'chars': ':', 'keys': ['level', 'component', 'message']}

        page1 = [
            {
                'component': 'searx.webapp',
                'message': 'static directory is /home/n/p/searx/searx/static',
                'level': 'DEBUG',
            },
            {
                'component': 'searx.webapp',
                'message': 'templates directory is /home/n/p/searx/searx/templates',
                'level': 'DEBUG',
            },
            {
                'component': 'searx.engines',
                'message': 'soundcloud engine: Starting background initialization',
                'level': 'DEBUG',
            },
            {
                'component': 'searx.engines',
                'message': 'wolframalpha engine: Starting background initialization',
                'level': 'DEBUG',
            },
            {
                'component': 'searx.engines',
                'message': 'locate engine: Starting background initialization',
                'level': 'DEBUG',
            },
            {
                'component': 'searx.engines',
                'message': 'regex search in files engine: Starting background initialization',
                'level': 'DEBUG',
            },
            {
                'component': 'urllib3.connectionpool',
                'message': 'Starting new HTTPS connection (1): www.wolframalpha.com',
                'level': 'DEBUG',
            },
            {
                'component': 'urllib3.connectionpool',
                'message': 'Starting new HTTPS connection (1): soundcloud.com',
                'level': 'DEBUG',
            },
            {
                'component': 'searx.engines',
                'message': 'find engine: Starting background initialization',
                'level': 'DEBUG',
            },
            {
                'component': 'searx.engines',
                'message': 'pattern search in files engine: Starting background initialization',
                'level': 'DEBUG',
            },
        ]
        page2 = [
            {
                'component': 'searx.webapp',
                'message': 'starting webserver on 127.0.0.1:8888',
                'level': 'DEBUG',
            },
            {
                'component': 'werkzeug',
                'message': ' * Debugger is active!',
                'level': 'WARNING',
            },
            {
                'component': 'werkzeug',
                'message': ' * Debugger PIN: 299-578-362',
                'level': 'INFO',
            },
        ]

        page1 = [KeyValue(kvmap=row) for row in page1]
        page2 = [KeyValue(kvmap=row) for row in page2]

        expected_results_by_page = [page1, page2]
        for i in [0, 1]:
            results = echo_engine.search('', {'pageno': i + 1})
            page = expected_results_by_page[i]
            for i, expected in enumerate(page):
                self.assertEqual(expected.kvmap["message"], str(results[i].kvmap["message"]))

    def test_regex_parsing(self):
        txt = '''commit 35f9a8c81d162a361b826bbcd4a1081a4fbe76a7
Author: Noémi Ványi <sitbackandwait@gmail.com>
Date:   Tue Oct 15 11:31:33 2019 +0200

first interesting message

commit 6c3c206316153ccc422755512bceaa9ab0b14faa
Author: Noémi Ványi <sitbackandwait@gmail.com>
Date:   Mon Oct 14 17:10:08 2019 +0200

second interesting message

commit d8594d2689b4d5e0d2f80250223886c3a1805ef5
Author: Noémi Ványi <sitbackandwait@gmail.com>
Date:   Mon Oct 14 14:45:05 2019 +0200

third interesting message

commit '''
        git_log_engine = command_engine
        git_log_engine.command = ['echo', txt]
        git_log_engine.result_separator = '\n\ncommit '
        git_log_engine.delimiter = {}
        git_log_engine.parse_regex = {
            'commit': r'\w{40}',
            'author': r'[\w* ]* <\w*@?\w*\.?\w*>',
            'date': r'Date: .*',
            'message': r'\n\n.*$',
        }
        git_log_engine.init({"command": git_log_engine.command, "parse_regex": git_log_engine.parse_regex})
        expected_results = [
            {
                'commit': '35f9a8c81d162a361b826bbcd4a1081a4fbe76a7',
                'author': ' Noémi Ványi <sitbackandwait@gmail.com>',
                'date': 'Date:   Tue Oct 15 11:31:33 2019 +0200',
                'message': '\n\nfirst interesting message',
            },
            {
                'commit': '6c3c206316153ccc422755512bceaa9ab0b14faa',
                'author': ' Noémi Ványi <sitbackandwait@gmail.com>',
                'date': 'Date:   Mon Oct 14 17:10:08 2019 +0200',
                'message': '\n\nsecond interesting message',
            },
            {
                'commit': 'd8594d2689b4d5e0d2f80250223886c3a1805ef5',
                'author': ' Noémi Ványi <sitbackandwait@gmail.com>',
                'date': 'Date:   Mon Oct 14 14:45:05 2019 +0200',
                'message': '\n\nthird interesting message',
            },
        ]

        expected_results = [KeyValue(kvmap=kvmap) for kvmap in expected_results]
        results = git_log_engine.search('', {'pageno': 1})
        for i, expected in enumerate(expected_results):
            self.assertEqual(expected.kvmap["message"], str(results[i].kvmap["message"]))

    def test_working_dir_path_query(self):
        ls_engine = command_engine
        ls_engine.command = ['ls', '{{QUERY}}']
        ls_engine.result_separator = '\n'
        ls_engine.delimiter = {'chars': ' ', 'keys': ['file']}
        ls_engine.query_type = 'path'

        results = ls_engine.search('.', {'pageno': 1})
        self.assertTrue(len(results) != 0)

        forbidden_paths = [
            '..',
            '../..',
            './..',
            '~',
            '/var',
        ]
        for forbidden_path in forbidden_paths:
            self.assertRaises(ValueError, ls_engine.search, forbidden_path, {'pageno': 1})

    def test_enum_queries(self):
        echo_engine = command_engine
        echo_engine.command = ['echo', '{{QUERY}}']
        echo_engine.query_type = 'enum'
        echo_engine.query_enum = ['i-am-allowed-to-say-this', 'and-that']

        for allowed in echo_engine.query_enum:
            results = echo_engine.search(allowed, {'pageno': 1})
            self.assertTrue(len(results) != 0)

        forbidden_queries = [
            'forbidden',
            'banned',
            'prohibited',
        ]
        for forbidden in forbidden_queries:
            self.assertRaises(ValueError, echo_engine.search, forbidden, {'pageno': 1})
