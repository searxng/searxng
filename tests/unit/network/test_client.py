# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

from unittest.mock import patch

from curl_cffi import CurlOpt

from searx.network import client
from tests import SearxTestCase


class TestNewClient(SearxTestCase):

    def test_ech_is_set_to_grease(self):
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
            )
        curl_options = async_client.call_args.kwargs["curl_options"]
        self.assertEqual(curl_options[CurlOpt.ECH], "grease")
