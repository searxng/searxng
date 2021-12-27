'''
searx is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

searx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with searx. If not, see < http://www.gnu.org/licenses/ >.

'''


from searx.engines import command as command_engine
from tests import SearxTestCase


class TestCommandEngine(SearxTestCase):
    def test_basic_seq_command_engine(self):
        ls_engine = command_engine
        ls_engine.command = ['seq', '{{QUERY}}']
        ls_engine.delimiter = {'chars': ' ', 'keys': ['number']}
        expected_results = [
            {'number': '1', 'template': 'key-value.html'},
            {'number': '2', 'template': 'key-value.html'},
            {'number': '3', 'template': 'key-value.html'},
            {'number': '4', 'template': 'key-value.html'},
            {'number': '5', 'template': 'key-value.html'},
        ]
        results = ls_engine.search('5'.encode('utf-8'), {'pageno': 1})
        self.assertEqual(results, expected_results)

    def test_delimiter_parsing_command_engine(self):
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

        expected_results_by_page = [
            [
                {
                    'component': 'searx.webapp',
                    'message': 'static directory is /home/n/p/searx/searx/static',
                    'template': 'key-value.html',
                    'level': 'DEBUG',
                },
                {
                    'component': 'searx.webapp',
                    'message': 'templates directory is /home/n/p/searx/searx/templates',
                    'template': 'key-value.html',
                    'level': 'DEBUG',
                },
                {
                    'component': 'searx.engines',
                    'message': 'soundcloud engine: Starting background initialization',
                    'template': 'key-value.html',
                    'level': 'DEBUG',
                },
                {
                    'component': 'searx.engines',
                    'message': 'wolframalpha engine: Starting background initialization',
                    'template': 'key-value.html',
                    'level': 'DEBUG',
                },
                {
                    'component': 'searx.engines',
                    'message': 'locate engine: Starting background initialization',
                    'template': 'key-value.html',
                    'level': 'DEBUG',
                },
                {
                    'component': 'searx.engines',
                    'message': 'regex search in files engine: Starting background initialization',
                    'template': 'key-value.html',
                    'level': 'DEBUG',
                },
                {
                    'component': 'urllib3.connectionpool',
                    'message': 'Starting new HTTPS connection (1): www.wolframalpha.com',
                    'template': 'key-value.html',
                    'level': 'DEBUG',
                },
                {
                    'component': 'urllib3.connectionpool',
                    'message': 'Starting new HTTPS connection (1): soundcloud.com',
                    'template': 'key-value.html',
                    'level': 'DEBUG',
                },
                {
                    'component': 'searx.engines',
                    'message': 'find engine: Starting background initialization',
                    'template': 'key-value.html',
                    'level': 'DEBUG',
                },
                {
                    'component': 'searx.engines',
                    'message': 'pattern search in files engine: Starting background initialization',
                    'template': 'key-value.html',
                    'level': 'DEBUG',
                },
            ],
            [
                {
                    'component': 'searx.webapp',
                    'message': 'starting webserver on 127.0.0.1:8888',
                    'template': 'key-value.html',
                    'level': 'DEBUG',
                },
                {
                    'component': 'werkzeug',
                    'message': ' * Debugger is active!',
                    'template': 'key-value.html',
                    'level': 'WARNING',
                },
                {
                    'component': 'werkzeug',
                    'message': ' * Debugger PIN: 299-578-362',
                    'template': 'key-value.html',
                    'level': 'INFO',
                },
            ],
        ]

        for i in [0, 1]:
            results = echo_engine.search(''.encode('utf-8'), {'pageno': i + 1})
            self.assertEqual(results, expected_results_by_page[i])

    def test_regex_parsing_command_engine(self):
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
            'commit': '\w{40}',
            'author': '[\w* ]* <\w*@?\w*\.?\w*>',
            'date': 'Date: .*',
            'message': '\n\n.*$',
        }
        expected_results = [
            {
                'commit': '35f9a8c81d162a361b826bbcd4a1081a4fbe76a7',
                'author': ' Noémi Ványi <sitbackandwait@gmail.com>',
                'date': 'Date:   Tue Oct 15 11:31:33 2019 +0200',
                'message': '\n\nfirst interesting message',
                'template': 'key-value.html',
            },
            {
                'commit': '6c3c206316153ccc422755512bceaa9ab0b14faa',
                'author': ' Noémi Ványi <sitbackandwait@gmail.com>',
                'date': 'Date:   Mon Oct 14 17:10:08 2019 +0200',
                'message': '\n\nsecond interesting message',
                'template': 'key-value.html',
            },
            {
                'commit': 'd8594d2689b4d5e0d2f80250223886c3a1805ef5',
                'author': ' Noémi Ványi <sitbackandwait@gmail.com>',
                'date': 'Date:   Mon Oct 14 14:45:05 2019 +0200',
                'message': '\n\nthird interesting message',
                'template': 'key-value.html',
            },
        ]

        results = git_log_engine.search(''.encode('utf-8'), {'pageno': 1})
        self.assertEqual(results, expected_results)

    def test_working_dir_path_query(self):
        ls_engine = command_engine
        ls_engine.command = ['ls', '{{QUERY}}']
        ls_engine.result_separator = '\n'
        ls_engine.delimiter = {'chars': ' ', 'keys': ['file']}
        ls_engine.query_type = 'path'

        results = ls_engine.search('.'.encode(), {'pageno': 1})
        self.assertTrue(len(results) != 0)

        forbidden_paths = [
            '..',
            '../..',
            './..',
            '~',
            '/var',
        ]
        for forbidden_path in forbidden_paths:
            self.assertRaises(ValueError, ls_engine.search, '..'.encode(), {'pageno': 1})

    def test_enum_queries(self):
        echo_engine = command_engine
        echo_engine.command = ['echo', '{{QUERY}}']
        echo_engine.query_type = 'enum'
        echo_engine.query_enum = ['i-am-allowed-to-say-this', 'and-that']

        for allowed in echo_engine.query_enum:
            results = echo_engine.search(allowed.encode(), {'pageno': 1})
            self.assertTrue(len(results) != 0)

        forbidden_queries = [
            'forbidden',
            'banned',
            'prohibited',
        ]
        for forbidden in forbidden_queries:
            self.assertRaises(ValueError, echo_engine.search, forbidden.encode(), {'pageno': 1})
