# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tiger_ is a Swiss meta search engine.

.. _Tiger: https://tiger.ch
"""

from json import loads
import random
from urllib.parse import urlencode

import typing as t

from dateutil import parser
from lxml import html

from searx.exceptions import SearxEngineAPIException
from searx.extended_types import SXNG_Response
from searx.network import get, post
from searx.result_types import EngineResults
from searx.utils import extr, eval_xpath_list, eval_xpath, extract_text
from searx.enginelib import EngineCache

if t.TYPE_CHECKING:
    from searx.search.processors import OnlineParams

about = {
    "website": "https://tiger.ch",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

paging = True

base_url = "https://tiger.ch"
categories = []
tiger_category = "Websuche"
"""
Possible values: "Websuche", "News".
"""


CACHE: EngineCache
"""Cache to store session codes (result of solved CAPTCHA)."""


def init(_):
    if tiger_category not in ("Websuche", "News"):
        raise ValueError("invalid search category: %s" % tiger_category)


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])
    return True


def _obtain_session_code() -> str:
    """The challenge works like this:

    - We first generate 3 random numbers.
    - Then we send them to /Human.svc/Make to get the operands (+, -) for the
      math challenge (i.e. a simple calculation)
    - Based on the operands, we calculate a result (usually done by the user by
      hand)
    - We send the result of the math calculation to the server to obtain a
      session "code" that has to be sent as cookie parameter for all searches

    E.g., challenges look like ``19-3+5``.
    """
    cached_session = CACHE.get("session")
    if cached_session:
        return cached_session

    results_page = get(f"{base_url}/checkCode.aspx")
    doc = html.fromstring(results_page.text)

    extra_data: dict[str, str] = {}
    for extra_param in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
        extra_data[extra_param] = doc.xpath(f"//input[@name='{extra_param}']/@value")[0]

    # var z1 = Math.floor((Math.random() * 8) + 11);
    # var z2 = Math.floor((Math.random() * 8) + 1);
    # var z3 = Math.floor((Math.random() * 8) + 1);
    num1 = random.randint(11, 19)
    num2 = random.randint(1, 9)
    num3 = random.randint(1, 9)

    challenge = get(f"{base_url}/Services/Human.svc/Make?M1={num1}&M2={num2}&M3={num3}", cookies=results_page.cookies)
    signs = loads(challenge.json()["d"])[0]
    sign1 = signs["Z1"]
    sign2 = signs["Z2"]

    result = num1
    for num, sign in [(num2, sign1), (num3, sign2)]:
        if sign == "+":
            result += num
        else:
            result -= num

    logger.debug(f"got challenge: {num1} {sign1} {num2} {sign2} {num3} = {result}")
    data = {
        **extra_data,
        "txtM": str(result),
        "btnHuman": "OK",
    }

    challenge_response = post(
        f"{base_url}/checkCode.aspx",
        cookies=results_page.cookies,
        data=data,
    )

    cookie = challenge_response.cookies["Tiger.ch"]
    code = extr(cookie, "Code=", "&")
    if not code:
        raise SearxEngineAPIException("failed to obtain session code")

    CACHE.set("session", code, expire=60 * 24 * 60)  # cookie is valid for two months
    return code


def request(query: str, params: "OnlineParams"):
    code = _obtain_session_code()
    args = {"w": query, "page": params["pageno"]}
    params["url"] = f"{base_url}/{tiger_category}?{urlencode(args)}"
    # Setting Checked=1 shows related search terms / suggestions
    # Language and country could be set with Lng= and Land= in the future
    params["cookies"]["Tiger.ch"] = f"Tiger.ch=&Code={code}&Checked=1"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    doc = html.fromstring(resp.text)

    if tiger_category == "Websuche":
        for result in eval_xpath_list(doc, "//div[@id='mainContainer']//table/tr"):
            url = extract_text(eval_xpath(result, ".//a[contains(@class, 'weblink')]/@href"))
            if not url:
                continue
            res.add(
                res.types.MainResult(
                    url=url,
                    title=extract_text(eval_xpath(result, ".//a[contains(@class, 'weblink')]")) or "",
                    content=extract_text(eval_xpath(result, ".//*[contains(@class, 'webbodynopic')]")) or "",
                )
            )

        for suggestion in eval_xpath_list(doc, "//a[contains(@class, 'linkAnders')]"):
            res.add(res.types.LegacyResult(suggestion=extract_text(suggestion)))
    elif tiger_category == "News":
        for result in eval_xpath_list(doc, "//div[@id='panNews']/div"):
            publishedDate = None
            try:
                date_str = extract_text(eval_xpath(result, ".//span[contains(@class, 'help')]/span")) or ""
                date_str = date_str.strip().removeprefix("-").strip()
                publishedDate = parser.parse(date_str)
            except parser.ParserError:
                pass

            thumbnail = extract_text(eval_xpath(result, "./img/@src"))
            if thumbnail:
                thumbnail = base_url + thumbnail

            res.add(
                res.types.MainResult(
                    url=extract_text(eval_xpath(result, ".//a[contains(@class, 'webLink')]/@href")),
                    title=extract_text(eval_xpath(result, ".//a[contains(@class, 'webLink')]")) or "",
                    thumbnail=thumbnail or "",
                    publishedDate=publishedDate,
                )
            )

    return res
