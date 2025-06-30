# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Method ``http_sec_fetch``
-------------------------

The ``http_sec_fetch`` method protect resources from web attacks with `Fetch
Metadata`_.  A request is filtered out in case of:

- http header Sec-Fetch-Mode_ is invalid
- http header Sec-Fetch-Dest_ is invalid

.. _Fetch Metadata:
   https://developer.mozilla.org/en-US/docs/Glossary/Fetch_metadata_request_header

.. _Sec-Fetch-Dest:
   https://developer.mozilla.org/en-US/docs/Web/API/Request/destination

.. _Sec-Fetch-Mode:
   https://developer.mozilla.org/en-US/docs/Web/API/Request/mode


"""
# pylint: disable=unused-argument

from __future__ import annotations
from ipaddress import (
    IPv4Network,
    IPv6Network,
)

import re
import flask
import werkzeug

from searx.extended_types import SXNG_Request

from . import config
from ._helpers import logger


def is_browser_supported(user_agent: str) -> bool:
    """Check if the browser supports Sec-Fetch headers.

    https://caniuse.com/mdn-http_headers_sec-fetch-dest
    https://caniuse.com/mdn-http_headers_sec-fetch-mode
    https://caniuse.com/mdn-http_headers_sec-fetch-site

    Supported browsers:
    - Chrome >= 80
    - Firefox >= 90
    - Safari >= 16.4
    - Edge (mirrors Chrome)
    - Opera (mirrors Chrome)
    """
    user_agent = user_agent.lower()

    # Chrome/Chromium/Edge/Opera
    chrome_match = re.search(r'chrome/(\d+)', user_agent)
    if chrome_match:
        version = int(chrome_match.group(1))
        return version >= 80

    # Firefox
    firefox_match = re.search(r'firefox/(\d+)', user_agent)
    if firefox_match:
        version = int(firefox_match.group(1))
        return version >= 90

    # Safari
    safari_match = re.search(r'version/(\d+)\.(\d+)', user_agent)
    if safari_match:
        major = int(safari_match.group(1))
        minor = int(safari_match.group(2))
        return major > 16 or (major == 16 and minor >= 4)

    return False


def filter_request(
    network: IPv4Network | IPv6Network,
    request: SXNG_Request,
    cfg: config.Config,
) -> werkzeug.Response | None:

    if not request.is_secure:
        logger.warning(
            "Sec-Fetch cannot be verified for non-secure requests (HTTP headers are not set/sent by the client)."
        )
        return None

    # Only check Sec-Fetch headers for supported browsers
    user_agent = request.headers.get('User-Agent', '')
    if is_browser_supported(user_agent):
        val = request.headers.get("Sec-Fetch-Mode", "")
        if val not in ('navigate', 'cors'):
            logger.debug("invalid Sec-Fetch-Mode '%s'", val)
            return flask.redirect(flask.url_for('index'), code=302)

        val = request.headers.get("Sec-Fetch-Site", "")
        if val not in ('same-origin', 'same-site', 'none'):
            logger.debug("invalid Sec-Fetch-Site '%s'", val)
            flask.redirect(flask.url_for('index'), code=302)

        val = request.headers.get("Sec-Fetch-Dest", "")
        if val not in ('document', 'empty'):
            logger.debug("invalid Sec-Fetch-Dest '%s'", val)
            flask.redirect(flask.url_for('index'), code=302)

    return None
