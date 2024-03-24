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
            for keyword in answerer.keywords:
                query.query = '{} {}'.format(keyword, unicode_payload)
                answer_dicts = answerer.answer(query)
                self.assertTrue(isinstance(answer_dicts, list))
                for answer_dict in answer_dicts:
                    self.assertTrue('answer' in answer_dict)
                    self.assertTrue(isinstance(answer_dict['answer'], str))
