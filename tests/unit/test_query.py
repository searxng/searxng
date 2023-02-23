from searx import settings
from searx.engines import load_engines
from searx.query import RawTextQuery
from tests import SearxTestCase


TEST_ENGINES = [
    {
        'name': 'dummy engine',
        'engine': 'dummy',
        'categories': 'general',
        'shortcut': 'du',
        'timeout': 3.0,
        'tokens': [],
    },
]


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

    def test_autocomplete(self):
        query = RawTextQuery(':englis', [])
        self.assertEqual(query.autocomplete_list, [":english"])

        query = RawTextQuery(':deutschla', [])
        self.assertEqual(query.autocomplete_list, [":deutschland"])

        query = RawTextQuery(':new_zea', [])
        self.assertEqual(query.autocomplete_list, [":new_zealand"])

        query = RawTextQuery(':hu-H', [])
        self.assertEqual(query.autocomplete_list, [":hu-hu"])

        query = RawTextQuery(':zh-', [])
        self.assertEqual(query.autocomplete_list, [':zh-cn', ':zh-hk', ':zh-tw'])


class TestTimeoutParser(SearxTestCase):
    def test_timeout_below100(self):
        query_text = '<3 the query'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 1)
        self.assertEqual(query.timeout_limit, 3)
        self.assertFalse(query.specific)

    def test_timeout_above100(self):
        query_text = '<350 the query'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 1)
        self.assertEqual(query.timeout_limit, 0.35)
        self.assertFalse(query.specific)

    def test_timeout_above1000(self):
        query_text = '<3500 the query'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 1)
        self.assertEqual(query.timeout_limit, 3.5)
        self.assertFalse(query.specific)

    def test_timeout_invalid(self):
        # invalid number: it is not bang but it is part of the query
        query_text = '<xxx the query'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 0)
        self.assertEqual(query.getQuery(), query_text)
        self.assertEqual(query.timeout_limit, None)
        self.assertFalse(query.specific)

    def test_timeout_autocomplete(self):
        # invalid number: it is not bang but it is part of the query
        query_text = 'the query <'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), query_text)
        self.assertEqual(len(query.query_parts), 0)
        self.assertEqual(query.getQuery(), query_text)
        self.assertEqual(query.timeout_limit, None)
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
        self.assertEqual(query.external_bang, None)
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

    def test_external_bang_autocomplete_empty(self):
        query_text = 'the query !!'
        query = RawTextQuery(query_text, [])

        self.assertEqual(query.getFullQuery(), 'the query !!')
        self.assertEqual(len(query.query_parts), 0)
        self.assertFalse(query.specific)
        self.assertGreater(len(query.autocomplete_list), 2)

        a = query.autocomplete_list[0]
        self.assertEqual(query.get_autocomplete_full_query(a), 'the query ' + a)


class TestBang(SearxTestCase):

    SPECIFIC_BANGS = ['!dummy_engine', '!du', '!general']
    THE_QUERY = 'the query'

    def test_bang(self):
        load_engines(TEST_ENGINES)

        for bang in TestBang.SPECIFIC_BANGS:
            with self.subTest(msg="Check bang", bang=bang):
                query_text = TestBang.THE_QUERY + ' ' + bang
                query = RawTextQuery(query_text, [])

                self.assertEqual(query.getFullQuery(), bang + ' ' + TestBang.THE_QUERY)
                self.assertEqual(query.query_parts, [bang])
                self.assertEqual(query.user_query_parts, TestBang.THE_QUERY.split(' '))

    def test_specific(self):
        for bang in TestBang.SPECIFIC_BANGS:
            with self.subTest(msg="Check bang is specific", bang=bang):
                query_text = TestBang.THE_QUERY + ' ' + bang
                query = RawTextQuery(query_text, [])
                self.assertTrue(query.specific)

    def test_bang_not_found(self):
        load_engines(TEST_ENGINES)
        query = RawTextQuery('the query !bang_not_found', [])
        self.assertEqual(query.getFullQuery(), 'the query !bang_not_found')

    def test_bang_autocomplete(self):
        load_engines(TEST_ENGINES)
        query = RawTextQuery('the query !dum', [])
        self.assertEqual(query.autocomplete_list, ['!dummy_engine'])

        query = RawTextQuery('!dum the query', [])
        self.assertEqual(query.autocomplete_list, [])
        self.assertEqual(query.getQuery(), '!dum the query')

    def test_bang_autocomplete_empty(self):
        load_engines(settings['engines'])
        query = RawTextQuery('the query !', [])
        self.assertEqual(query.autocomplete_list, ['!images', '!wikipedia', '!osm'])

        query = RawTextQuery('the query !', ['osm'])
        self.assertEqual(query.autocomplete_list, ['!images', '!wikipedia'])
