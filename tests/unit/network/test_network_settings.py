# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-class-docstring
# pylint: disable=protected-access
"""Test for settings related to the network configuration
"""

from os.path import dirname, join, abspath
from unittest.mock import patch

from searx import settings_loader, settings_defaults, engines
from searx.network import network
from tests import SearxTestCase


test_dir = abspath(dirname(__file__))


class TestDefaultSettings(SearxTestCase):
    def test_load(self):
        # to do later : write more tests (thank you pylint for stoping the linting of t o d o...)
        # for now, make sure the code does not crash
        with patch.dict(settings_loader.environ, {'SEARXNG_SETTINGS_PATH': join(test_dir, 'network_settings.yml')}):
            settings, _ = settings_loader.load_settings()
            settings_defaults.apply_schema(settings, settings_defaults.SCHEMA, [])
            engines.load_engines(settings["engines"])
            network_manager = network.NetworkManager()
            network_manager.initialize_from_settings(settings["engines"], settings["outgoing"], check=True)

            network_enginea = network_manager.get("enginea")
            http_client = network_enginea._get_http_client()

            repr_network = "<Network logger_name='enginea'>"

            self.assertEqual(repr(network_enginea), repr_network)
            self.assertTrue(repr_network in repr(http_client))
