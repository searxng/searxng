# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

from unittest.mock import patch

from curl_cffi import CurlOpt

from searx.network import client
from tests import SearxTestCase


class TestNewClient(SearxTestCase):

    def _new_client(self, **kwargs):
        with patch.object(client, "AsyncClient") as async_client:
            client.new_client(
                enable_http=False,
                verify=True,
                enable_http2=True,
                enable_http3=False,
                max_connections=10,
                proxies={},
                local_address=None,
                max_redirects=5,
                **kwargs,
            )
        return async_client.call_args.kwargs["curl_options"]

    def test_ech_keeps_library_default(self):
        # ECH must stay enabled unless the operator opts in (#6912)
        self.assertNotIn(CurlOpt.ECH, self._new_client())

    def test_ech_is_configurable(self):
        self.assertEqual(self._new_client(ech="grease")[CurlOpt.ECH], "grease")
