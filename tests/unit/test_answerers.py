# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from mock import Mock

from searx.answerers import answerers
from tests import SearxTestCase


class AnswererTest(SearxTestCase):  # pylint: disable=missing-class-docstring
    def test_unicode_input(self):
        query = Mock()
        unicode_payload = 'árvíztűrő tükörfúrógép'
        for answerer in answerers:
            query.query = '{} {}'.format(answerer.keywords[0], unicode_payload)
            self.assertTrue(isinstance(answerer.answer(query), list))
