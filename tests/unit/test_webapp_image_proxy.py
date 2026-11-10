# SPDX-License-Identifier: AGPL-3.0-or-later
"""The image proxy fetches an image on behalf of a browser."""

from unittest.mock import patch

import searx.webapp
from searx import settings
from searx.webutils import new_hmac

from tests import SearxTestCase


class ImageProxyRequestTestCase(SearxTestCase):
    """An outgoing request the image proxy sends must carry the configured
    outgoing timeout. curl is asked for no timeout when none is given, so a
    host that accepts the connection and never answers holds the web worker
    until the operating system gives up on the socket."""

    def setUp(self):
        super().setUp()
        self.url = 'https://images.example.org/cat.png'
        self.sig = new_hmac(settings['server']['secret_key'], self.url.encode())

    def capture_stream_kwargs(self):
        """Runs the view and returns the keyword arguments it sends the network layer."""
        captured = {}

        class StopAtRequest(Exception):
            """Raised in place of the outgoing request, once it is recorded."""

        def fake_stream(**kwargs):
            captured.update(kwargs)
            raise StopAtRequest()

        request_path = '/image_proxy?url={0}&h={1}'.format(self.url, self.sig)
        with searx.webapp.app.test_request_context(request_path):
            with patch.object(searx.webapp, 'http_stream', fake_stream):
                try:
                    searx.webapp.image_proxy()
                except StopAtRequest:
                    pass
        return captured

    def test_image_proxy_has_timeout(self):
        kwargs = self.capture_stream_kwargs()
        self.assertIn('timeout', kwargs)
        self.assertEqual(kwargs['timeout'], settings['outgoing']['request_timeout'])
