# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared methods for accessing Wikidata."""

import typing as t
from urllib.parse import urlencode

from searx import logger, get_setting
from searx.network import get, post
from searx.utils import searxng_useragent

logger = logger.getChild("wikidata")

# SPARQL
SPARQL_ENDPOINT_URL = "https://query.wikidata.org/sparql"
SPARQL_EXPLAIN_URL = "https://query.wikidata.org/bigdata/namespace/wdq/sparql?explain"


def send_wikidata_query(query: str, method: str = "GET", **kwargs: dict[str, t.Any]) -> dict[str, t.Any]:

    headers = get_wikidata_headers()
    logger.debug("send_wikidata_query (%s): %s", method, headers)

    if method == "GET":
        # query will be cached by wikidata
        http_response = get(
            SPARQL_ENDPOINT_URL + "?" + urlencode({"query": query}),
            headers=headers,
            impersonate="none",
            **kwargs,
        )
    else:
        # query won't be cached by wikidata
        http_response = post(
            SPARQL_ENDPOINT_URL,
            data={"query": query},
            headers=headers,
            impersonate="none",
        )

    http_response.raise_for_status()
    return http_response.json()


def get_wikidata_headers() -> dict[str, str]:
    """Creates the HTTP headers that are required for a Wikidata query.

    Any Wikidata request needs a valid User-Agent header, see below.

    .. attention::

       In order to comply with the policy, the :ref:`contact_url <settings
       general.contact_url>` must be configured!

    User-Agent policy and Query limits (:issue:`6840`):

    - https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual#Query_limits

      Clients who don’t comply with the User-Agent policy may be blocked
      completely -- make sure to send a good User-Agent header.

    - https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy

      The generic format is (parts that are not applicable can be omitted)::

          <client name>/<version> (<contact information>)
          <library/framework name>/<version> [<library name>/<version> ...]

    """

    contact: str = get_setting("general.contact_url", "") or ""
    contact = contact.removeprefix("mailto:").strip()
    if not contact:
        logger.warning("wikidata requires a valid general.contact_url (SEARXNG_CONTACT_URL)")

    return {
        "Accept": "application/sparql-results+json",
        "User-Agent": searxng_useragent(contact),
    }
