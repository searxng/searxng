# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import mock
from parameterized.parameterized import parameterized
from searx import webutils
from tests import SearxTestCase


class TestWebUtils(SearxTestCase):

    @parameterized.expand(
        [
            ('https://searx.me/', 'https://searx.me/'),
            ('https://searx.me/ű', 'https://searx.me/ű'),
            ('https://searx.me/' + (100 * 'a'), 'https://searx.me/[...]aaaaaaaaaaaaaaaaa'),
            ('https://searx.me/' + (100 * 'ű'), 'https://searx.me/[...]űűűűűűűűűűűűűűűűű'),
        ]
    )
    def test_prettify_url(self, test_url: str, expected: str):
        self.assertEqual(webutils.prettify_url(test_url, max_length=32), expected)

    @parameterized.expand(
        [
            (0, None, None),
            (None, None, None),
            ('', None, None),
            (False, None, None),
        ]
    )
    def test_highlight_content_none(self, content, query, expected):
        self.assertEqual(webutils.highlight_content(content, query), expected)

    def test_highlight_content_same(self):
        content = '<html></html>not<'
        self.assertEqual(webutils.highlight_content(content, None), content)

    @parameterized.expand(
        [
            ('test', 'a', 'a'),
            ('a test', 'a', '<span class="highlight">a</span>'),
            ('" test "', 'a test string', 'a <span class="highlight">test</span> string'),
            ('"a"', 'this is a test string', 'this is <span class="highlight">a</span> test string'),
            (
                'a test',
                'this is a test string that matches entire query',
                'this is <span class="highlight">a</span>'
                ' <span class="highlight">test</span>'
                ' string that matches entire query',
            ),
            (
                'this a test',
                'this is a string to test.',
                (
                    '<span class="highlight">this</span>'
                    ' is <span class="highlight">a</span>'
                    ' string to <span class="highlight">test</span>.'
                ),
            ),
            (
                'match this "exact phrase"',
                'this string contains the exact phrase we want to match',
                ''.join(
                    [
                        '<span class="highlight">this</span> string contains the <span class="highlight">exact</span> ',
                        '<span class="highlight">phrase</span> we want to <span class="highlight">match</span>',
                    ]
                ),
            ),
            (
                'a class',
                'a string with class.',
                '<span class="highlight">a</span> string with <span class="highlight">class</span>.',
            ),
        ]
    )
    def test_highlight_content_equal(self, query: str, content: str, expected: str):
        self.assertEqual(webutils.highlight_content(content, query), expected)


class TestUnicodeWriter(SearxTestCase):

    def setUp(self):
        super().setUp()
        self.unicode_writer = webutils.CSVWriter(mock.MagicMock())

    def test_write_row(self):
        row = [1, 2, 3]
        self.assertIsNone(self.unicode_writer.writerow(row))

    def test_write_rows(self):
        self.unicode_writer.writerow = mock.MagicMock()
        rows = [1, 2, 3]
        self.unicode_writer.writerows(rows)
        self.assertEqual(self.unicode_writer.writerow.call_count, len(rows))


class TestNewHmac(SearxTestCase):

    @parameterized.expand(
        [
            b'secret',
            1,
        ]
    )
    def test_attribute_error(self, secret_key):
        data = b'http://example.com'
        with self.assertRaises(AttributeError):
            webutils.new_hmac(secret_key, data)

    def test_bytes(self):
        data = b'http://example.com'
        res = webutils.new_hmac('secret', data)
        self.assertEqual(res, '23e2baa2404012a5cc8e4a18b4aabf0dde4cb9b56f679ddc0fd6d7c24339d819')
