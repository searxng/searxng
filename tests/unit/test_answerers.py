# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

from parameterized import parameterized

import zhensa.plugins
import zhensa.answerers
import zhensa.preferences

from zhensa.extended_types import sxng_request

from tests import SearxTestCase


class AnswererTest(SearxTestCase):

    def setUp(self):
        super().setUp()

        self.storage = zhensa.plugins.PluginStorage()
        engines = {}
        self.pref = zhensa.preferences.Preferences(["simple"], ["general"], engines, self.storage)
        self.pref.parse_dict({"locale": "en"})

    @parameterized.expand(zhensa.answerers.STORAGE.answerer_list)
    def test_unicode_input(self, answerer_obj: zhensa.answerers.Answerer):

        with self.app.test_request_context():
            sxng_request.preferences = self.pref

            unicode_payload = "árvíztűrő tükörfúrógép"
            for keyword in answerer_obj.keywords:
                query = f"{keyword} {unicode_payload}"
                self.assertIsInstance(answerer_obj.answer(query), list)
