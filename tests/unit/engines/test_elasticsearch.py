# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

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

from json import loads
from searx.engines import elasticsearch as elasticsearch_engine
from tests import SearxTestCase


class TestElasticsearchEngine(SearxTestCase):  # pylint: disable=missing-class-docstring
    default_params = {"headers": {}}

    def test_url_settings(self):
        elasticsearch_engine.base_url = 'http://es:12345'
        elasticsearch_engine.index = 'index'
        params = elasticsearch_engine.request("city:berlin", self.default_params)
        self.assertEqual(params["url"], "http://es:12345/index/_search")

    def test_basic_queries(self):
        queries = [
            ['match', 'field:stuff', '{"query": {"match": {"field": {"query": "stuff"}}}}'],
            ['simple_query_string', 'stuff', '{"query": {"simple_query_string": {"query": "stuff"}}}'],
            ['term', 'field:stuff', '{"query": {"term": {"field": "stuff"}}}'],
            ['terms', 'field:stuff1,stuff2', '{"query": {"terms": {"field": ["stuff1", "stuff2"]}}}'],
        ]

        for query in queries:
            elasticsearch_engine.query_type = query[0]
            params = elasticsearch_engine.request(query[1], self.default_params)
            self.assertEqual(loads(params["data"]), loads(query[2]))

    def test_basic_failures(self):
        queries = [
            ['match', 'stuff', 'query format must be "key:value'],
            ['term', 'stuff', 'query format must be key:value'],
            ['terms', 'stuff', 'query format must be key:value1,value2'],
        ]

        for query in queries:
            elasticsearch_engine.query_type = query[0]
            with self.assertRaises(ValueError) as context:
                elasticsearch_engine.request(query[1], self.default_params)
            self.assertIn(query[2], str(context.exception))

    def test_custom_queries(self):
        queries = [
            [
                'field:stuff',
                '{"query": {"match": {"{{KEY}}": {"query": "{{VALUE}}"}}}}',
                '{"query": {"match": {"field": {"query": "stuff"}}}}',
            ],
            [
                'stuff',
                '{"query": {"simple_query_string": {"query": "{{QUERY}}"}}}',
                '{"query": {"simple_query_string": {"query": "stuff"}}}',
            ],
            [
                'space stuff',
                '{"query": {"simple_query_string": {"query": "{{QUERY}}"}}}',
                '{"query": {"simple_query_string": {"query": "space stuff"}}}',
            ],
            [
                '"space stuff"',
                '{"query": {"simple_query_string": {"query": "{{QUERY}}"}}}',
                '{"query": {"simple_query_string": {"query": "\\\"space stuff\\\""}}}',
            ],
            [
                "embedded'apostrophe",
                '{"query": {"simple_query_string": {"query": "{{QUERY}}"}}}',
                '{"query": {"simple_query_string": {"query": "embedded\'apostrophe"}}}',
            ],
            [
                'more:stuff',
                '{"query": {"simple_query_string": {"query": "{{QUERY}}"}}}',
                '{"query": {"simple_query_string": {"query": "more:stuff"}}}',
            ],
            [
                'field:stuff',
                '{"query": {"term": {"{{KEY}}": "{{VALUE}}"}}}',
                '{"query": {"term": {"field": "stuff"}}}',
            ],
            [
                'field:more:stuff',
                '{"query": {"match": {"{{KEY}}": {"query": "{{VALUE}}"}}}}',
                '{"query": {"match": {"field": {"query": "more:stuff"}}}}',
            ],
            [
                'field:stuff1,stuff2',
                '{"query": {"terms": {"{{KEY}}": "{{VALUES}}"}}}',
                '{"query": {"terms": {"field": ["stuff1", "stuff2"]}}}',
            ],
            [
                'field:stuff1',
                '{"query": {"terms": {"{{KEY}}": "{{VALUES}}"}}}',
                '{"query": {"terms": {"field": ["stuff1"]}}}',
            ],
        ]

        elasticsearch_engine.query_type = 'custom'
        for query in queries:
            elasticsearch_engine.custom_query_json = query[1]
            params = elasticsearch_engine.request(query[0], self.default_params)
            self.assertEqual(loads(params["data"]), loads(query[2]))

    def test_custom_failures(self):
        queries = [
            ['stuff', '{"query": {"match": {"{{KEY}}": {"query": "{{VALUE}}"}}}}', 'query format must be "key:value"'],
            ['stuff', '{"query": {"terms": {"{{KEY}}": "{{VALUES}}"}}}', 'query format must be "key:value"'],
            ['stuff', '{"query": {"simple_query_string": {"query": {{QUERY}}}}}', 'invalid custom_query string'],
            ['stuff', '"query": {"simple_query_string": {"query": "{{QUERY}}"}}}', 'invalid custom_query string'],
        ]

        elasticsearch_engine.query_type = 'custom'
        for query in queries:
            elasticsearch_engine.custom_query_json = query[1]
            with self.assertRaises(ValueError) as context:
                elasticsearch_engine.request(query[0], self.default_params)
            self.assertIn(query[2], str(context.exception))


# vi:sw=4
