# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

from parameterized.parameterized import parameterized
from searx.query import RawTextQuery
from tests import SearxTestCase


class TestQuery(SearxTestCase):

    def test_simple_query(self):
        query_text = 'the query'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 0)
        self.assertEqual(len(query.user_query_parts), 2)
        self.assertEqual(len(query.languages), 0)
        self.assertFalse(query.specific)

    def test_multiple_spaces_query(self):
        query_text = '\tthe   query'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), 'the query')
        self.assertEqual(len(query.query_parts), 0)
        self.assertEqual(len(query.user_query_parts), 2)
        self.assertEqual(len(query.languages), 0)
        self.assertFalse(query.specific)

    def test_str_method(self):
        query_text = '<7 the query'
        query = RawTextQuery(query_text, [])
        self.assertEqual(str(query), '<7 the query')

    def test_repr_method(self):
        query_text = '<8 the query'
        query = RawTextQuery(query_text, [])
        r = repr(query)
        self.assertTrue(r.startswith(f"<RawTextQuery query='{query_text}' "))

    def test_change_query(self):
        query_text = '<8 the query'
        query = RawTextQuery(query_text, [])
        another_query = query.changeQuery('another text')
        self.assertEqual(query, another_query)
        self.assertEqual(query.getFullQuery(), '<8 another text')


class TestLanguageParser(SearxTestCase):

    def test_language_code(self):
        language = 'es-ES'
        query_text = 'the query'
        full_query = ':' + language + ' ' + query_text
        query = RawTextQuery(full_query, [])

        self.assertEqual(query.getFullQuery(), full_query)
        self.assertEqual(len(query.query_parts), 1)
        self.assertEqual(len(query.languages), 1)
        self.assertIn(language, query.languages)
        self.assertFalse(query.specific)

    def test_language_name(self):
        language = 'english'
        query_text = 'the query'
        full_query = ':' + language + ' ' + query_text
        query = RawTextQuery(full_query, [])

        self.assertEqual(query.getFullQuery(), full_query)
        self.assertEqual(len(query.query_parts), 1)
        self.assertIn('en', query.languages)
        self.assertFalse(query.specific)

    def test_unlisted_language_code(self):
        language = 'all'
        query_text = 'the query'
        full_query = ':' + language + ' ' + query_text
        query = RawTextQuery(full_query, [])

        self.assertEqual(query.getFullQuery(), full_query)
        self.assertEqual(len(query.query_parts), 1)
        self.assertIn('all', query.languages)
        self.assertFalse(query.specific)

    def test_auto_language_code(self):
        language = 'auto'
        query_text = 'una consulta'
        full_query = ':' + language + ' ' + query_text
        query = RawTextQuery(full_query, [])

        self.assertEqual(query.getFullQuery(), full_query)
        self.assertEqual(len(query.query_parts), 1)
        self.assertIn('auto', query.languages)
        self.assertFalse(query.specific)

    def test_invalid_language_code(self):
        language = 'not_a_language'
        query_text = 'the query'
        full_query = ':' + language + ' ' + query_text
        query = RawTextQuery(full_query, [])

        self.assertEqual(query.getFullQuery(), full_query)
        self.assertEqual(len(query.query_parts), 0)
        self.assertEqual(len(query.languages), 0)
        self.assertFalse(query.specific)

    def test_empty_colon_in_query(self):
        query_text = 'the : query'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 0)
        self.assertEqual(len(query.languages), 0)
        self.assertFalse(query.specific)

    def test_autocomplete_empty(self):
        query_text = 'the query :'
        query = RawTextQuery(query_text, [])
        self.assertEqual(query.autocomplete_list, [":en", ":en_us", ":english", ":united_kingdom"])

    @parameterized.expand(
        [
            (':englis', [":english"]),
            (':deutschla', [":deutschland"]),
            (':new_zea', [":new_zealand"]),
            (':zh-', [':zh-cn', ':zh-hk', ':zh-tw']),
        ]
    )
    def test_autocomplete(self, query: str, autocomplete_list: list):
        query = RawTextQuery(query, [])
        self.assertEqual(query.autocomplete_list, autocomplete_list)


class TestTimeoutParser(SearxTestCase):

    @parameterized.expand(
        [
            ('<3 the query', 3),
            ('<350 the query', 0.35),
            ('<3500 the query', 3.5),
        ]
    )
    def test_timeout_limit(self, query_text: str, timeout_limit: float):
        query = RawTextQuery(query_text, [])
        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 1)
        self.assertEqual(query.timeout_limit, timeout_limit)
        self.assertFalse(query.specific)

    def test_timeout_invalid(self):
        # invalid number: it is not bang but it is part of the query
        query_text = '<xxx the query'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 0)
        self.assertEqual(query.getQuery(), query_text)
        self.assertIsNone(query.timeout_limit)
        self.assertFalse(query.specific)

    def test_timeout_autocomplete(self):
        # invalid number: it is not bang but it is part of the query
        query_text = 'the query <'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 0)
        self.assertEqual(query.getQuery(), query_text)
        self.assertIsNone(query.timeout_limit)
        self.assertFalse(query.specific)
        self.assertEqual(query.autocomplete_list, ['<3', '<850'])


class TestExternalBangParser(SearxTestCase):

    def test_external_bang(self):
        query_text = '!!ddg the query'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 1)
        self.assertFalse(query.specific)

    def test_external_bang_not_found(self):
        query_text = '!!notfoundbang the query'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertIsNone(query.external_bang)
        self.assertFalse(query.specific)

    def test_external_bang_autocomplete(self):
        query_text = 'the query !!dd'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), '!!dd the query')
        self.assertEqual(len(query.query_parts), 1)
        self.assertFalse(query.specific)
        self.assertGreater(len(query.autocomplete_list), 0)

        a = query.autocomplete_list[0]
        self.assertEqual(query.get_autocomplete_full_query(a), a + ' the query')


class TestBang(SearxTestCase):

    SPECIFIC_BANGS = ['!dummy_engine', '!gd', '!general']
    THE_QUERY = 'the query'

    @parameterized.expand(SPECIFIC_BANGS)
    def test_bang(self, bang: str):
        with self.subTest(msg="Check bang", bang=bang):
            query_text = TestBang.THE_QUERY + ' ' + bang
            query = RawTextQuery(query_text, [])

            self.assertEqual(query.getFullQuery(), bang + ' ' + TestBang.THE_QUERY)
            self.assertEqual(query.query_parts, [bang])
            self.assertEqual(query.user_query_parts, TestBang.THE_QUERY.split(' '))

    @parameterized.expand(SPECIFIC_BANGS)
    def test_specific(self, bang: str):
        with self.subTest(msg="Check bang is specific", bang=bang):
            query_text = TestBang.THE_QUERY + ' ' + bang
            query = RawTextQuery(query_text, [])
            self.assertTrue(query.specific)

    def test_bang_not_found(self):
        query = RawTextQuery('the query !bang_not_found', [])
        self.assertEqual(query.getFullQuery(), 'the query !bang_not_found')

    def test_bang_autocomplete(self):
        query = RawTextQuery('the query !dum', [])
        self.assertEqual(query.autocomplete_list, ['!dummy_engine', '!dummy_private_engine'])

        query = RawTextQuery('!dum the query', [])
        self.assertEqual(query.autocomplete_list, [])
        self.assertEqual(query.getQuery(), '!dum the query')

    def test_bang_autocomplete_empty(self):
        query = RawTextQuery('the query !', [])
        self.assertEqual(query.autocomplete_list, ['!images', '!wikipedia', '!osm'])

        query = RawTextQuery('the query !', ['osm'])
        self.assertEqual(query.autocomplete_list, ['!images', '!wikipedia'])
