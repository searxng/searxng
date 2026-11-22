# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name,too-few-public-methods

import typing as t

from searx.extended_types import SXNG_Response
from tests import SearxTestCase


class _FakeResponse:
    content = b'<?xml version="1.0" encoding="UTF-8"?><feed><title>x</title></feed>'
    text = '<?xml version="1.0" encoding="UTF-8"?><feed><title>x</title></feed>'


class TestSXNGResponse(SearxTestCase):

    def test_html_parses_xml_with_encoding_declaration(self):
        # lxml refuses unicode strings that carry an encoding declaration, so
        # the response must be parsed from bytes (see #6324).
        dom = SXNG_Response.html(t.cast(SXNG_Response, t.cast(object, _FakeResponse())))
        self.assertEqual(dom.tag, "feed")
