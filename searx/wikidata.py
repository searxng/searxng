# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared methods for accessing Wikidata."""

import typing as t
from urllib.parse import urlencode

from searx import logger, get_setting
from searx.network import get, post
from searx.utils import searxng_useragent

logger = logger.getChild("wikidata")

# SPARQL V2: https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/WDQS_backend_update
SPARQL_ENDPOINT_URL = "https://query-next.wikidata.org/sparql"
SPARQL_EXPLAIN_URL = "https://query.wikidata.org/bigdata/namespace/wdq/sparql?explain"


def send_wikidata_query(
    query: str,
    method: str = "GET",
    timeout: float = 60,
    **kwargs: dict[str, t.Any],
) -> dict[str, t.Any]:
    """Send SPARQL query to Wikidata and return ``dict`` from the JSON response.

    SPARQL statements can be tested at: https://query-next.wikidata.org/

    The runtimes of queries can be very long, the default timeout is 60 seconds.
    The runtimes are not deterministic, in addition Wikidata cached both the
    queries incoming via POST and those via GET.

    Sometimes it can happen that a query takes too long or for unknown reasons
    Wikidata drops the connection. In these cases, it often helps to simply send
    the query again a second time.
    """

    headers = get_wikidata_headers()
    logger.debug("send_wikidata_query (%s): %s", method, headers)

    if method == "GET":
        http_response = get(
            SPARQL_ENDPOINT_URL + "?" + urlencode({"query": query}),
            headers=headers,
            impersonate="none",
            timeout=timeout,
            **kwargs,
        )
    else:
        http_response = post(
            SPARQL_ENDPOINT_URL,
            data={"query": query},
            headers=headers,
            impersonate="none",
            timeout=timeout,
            # kwargs are lost in commit 38929d14
            **kwargs,
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
