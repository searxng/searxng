# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""Swisscows (general, images, videos)"""

import typing as t

import base64
import codecs
import hashlib
import json
import random

from datetime import datetime
from urllib.parse import urlencode

from babel.core import get_global

from searx.result_types import EngineResults, LegacyResult  # pyright: ignore[reportPrivateLocalImportUsage]
from searx.utils import humanize_number, html_to_text

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://swisscows.com",
    "wikidata_id": "Q22937452",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}


categories = ["general"]
swisscows_category = "web"  # possible: "web", "videos", "images"

results_per_page = 50

time_range_support = True
paging = True

base_url = "https://api.swisscows.com"

CAESAR_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
NONCE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"

time_range_map = {"day": "Day", "week": "Week", "month": "Month", "year": "Year"}

# fmt: off
swisscows_regions: list[str] = [
    "AR", "AU", "AT", "BE", "BR", "CA", "CL", "CN", "DK", "FI",
    "FR", "DE", "HK", "HU", "IN", "ID", "IT", "JP", "KR", "LV",
    "MY", "MX", "NL", "NZ", "NO", "PH", "PL", "PT", "RU", "SA",
    "ZA", "ES", "SE", "CH", "TW", "TR", "UA", "GB", "US"
]
"""Regions supported by swisscows."""
# fmt: on

# swisscows_languages = [
#     "GB", "DE", "ES", "FR", "IT", "LV", "HU", "NL", "PT", "RU", "UA"
# ]


def appropriate_locale(searxng_locale: str, regions: list[str], default: str) -> str:
    """Returns the appropriate swisscows locale for the region or language
    selected by the user.  If no value is determined, ``default`` is returned
    """
    _locale = searxng_locale.split("-")

    if _locale[0] == "all":
        return default

    if len(_locale) == 1 or _locale[1] in regions:
        return searxng_locale

    sxng_lang = _locale[0]
    if sxng_lang.upper() in regions:
        return f"{sxng_lang}-{sxng_lang.upper()}"

    likely_subtag: str | None = get_global("likely_subtags").get(sxng_lang)
    if likely_subtag:
        _tag: list[str] = likely_subtag.split("_")
        if _tag[-1] in regions:
            return f"{_tag[0]}-{_tag[-1]}"

    return default


def generate_nonce(length: int = 32) -> str:
    """
    Generate a random char sequence with the given length.
    """
    return "".join([random.choice(NONCE_ALPHABET) for _ in range(length)])


def caesar_shift_with_switch_case(s: str, offset: int = 13) -> str:
    """
    Caesar shift by :py:obj:`offset` that additionally inverts the casing of all letters
    (i.e. from lowercase to uppercase and vice versa).
    """
    out = ""
    for c in s:
        if c.upper() in CAESAR_ALPHABET:
            alphabet_index = ord(c.upper()) - ord("A")
            shifted = CAESAR_ALPHABET[(alphabet_index + offset) % len(CAESAR_ALPHABET)]
            case_switched = shifted.lower() if c.isupper() else shifted.upper()
            out += case_switched
        else:
            out += c
    return out


def sha256_hash_b64_url(s: str) -> str:
    """
    Calculate the SHA256 hash and base64 URL-encodes it.
    """
    hasher = hashlib.sha256()
    hasher.update(s.encode())
    hashed_bytes = hasher.digest()

    # hashlib generates a byte digest, but since we need to convert it to base64, we
    # need to do that by hand
    hash_base64 = codecs.encode(hashed_bytes, "base64").decode("utf-8").rstrip('\n')

    hash_base64_url_encoded = hash_base64.replace("=", "").replace("+", '-').replace("/", '_')
    return hash_base64_url_encoded


def generate_nonce_and_signature(base_path: str, args: dict[str, t.Any]) -> tuple[str, str]:
    """
    Generate "X-Request-Nonce" and "X-Request-Signature" which are required for accessing
    Swisscows images (reverse engineered from their official website).
    """
    nonce = generate_nonce()
    nonce_shifted = caesar_shift_with_switch_case(nonce, 13)

    # in the path, all keys must be sorted in alphabetic order,
    # otherwise the generated signature won't be accepted!
    # additionally, the values may not be URL encoded, they have to be plain text
    # hence we don't use urlencode here
    args_sorted = sorted(args.items(), key=lambda arg: arg[0])
    query_string = "&".join(f"{key}={value}" for (key, value) in args_sorted)
    full_path = f"{base_path}?{query_string}"

    signature = sha256_hash_b64_url(full_path + nonce_shifted)
    return (nonce, signature)


maximum_page_size = {"web": 20, "images": 50, "videos": 10}


def init(_):
    if swisscows_category not in ("web", "images", "videos"):
        raise ValueError("illegal swisscows category: %s" % swisscows_category)

    if results_per_page > maximum_page_size[swisscows_category]:
        raise ValueError(
            "results_per_page for swisscows %s can be at most %d"
            % (swisscows_category, maximum_page_size[swisscows_category])
        )


def request(query: str, params: "OnlineParams") -> None:
    # swisscows images only supports 2 pages
    if swisscows_category == "images" and params["pageno"] > 2:
        params["url"] = None
        return

    locale = appropriate_locale(params["searxng_locale"], swisscows_regions, "en-US")
    base_path = ""
    args = dict[str, t.Any]
    if swisscows_category == "web":
        freshness = "All"
        if params["time_range"]:
            freshness = time_range_map[params["time_range"]]
        args = {
            "freshness": freshness,
            "itemsCount": results_per_page,
            "locale": locale,
            "offset": (params["pageno"] - 1) * results_per_page,
            "query": query,
            "spellcheck": True,
        }
        base_path = "/v5/web/search"
    elif swisscows_category == "images":
        args = {
            "itemsCount": results_per_page,
            "locale": locale,
            "offset": (params["pageno"] - 1) * results_per_page,
            "query": query,
            "spellcheck": True,
        }
        base_path = "/v5/images/search"
    else:
        args = {
            "itemsCount": results_per_page,
            "offset": (params["pageno"] - 1) * results_per_page,
            "query": query,
            "region": locale,
            "spellcheck": True,
        }
        base_path = "/v2/videos/search"

    nonce, signature = generate_nonce_and_signature(base_path, args)

    params["headers"].update(
        {
            "X-Request-Nonce": nonce,
            "X-Request-Signature": signature,
        }
    )
    params["url"] = f"{base_url}{base_path}?{urlencode(args)}"


def _video_result(result: dict[str, str]) -> LegacyResult:
    published_date = None
    if result.get("datePublished"):
        published_date = datetime.fromisoformat(result["datePublished"])

    view_count = None
    if result.get("viewCount"):
        view_count = humanize_number(result["viewCount"])  # pyright: ignore[reportArgumentType]

    return LegacyResult(
        {
            "template": "videos.html",
            "url": result["url"],
            "title": html_to_text(result.get("title") or result["name"]),
            "content": result["description"],
            "thumbnail": result.get("thumbnailUrl")
            or result.get("thumbnail", {}).get("url"),  # pyright: ignore[reportAttributeAccessIssue]
            "length": result.get("duration"),
            "iframe_src": result.get("embedUrl"),
            "publishedDate": published_date,
            "views": view_count,
        }
    )


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()

    json_data = resp.json()

    # the payload encoding is only used for general and images,
    # for videos the data gets returned directly as a normal JSON response
    # payload is encoded as a JSON web token -> 3 parts, separated by "."
    # the actual data is in the center of the encoded string
    if "payload" in json_data:
        payload = json_data["payload"].split(".")[1]
        # pad with '=' to be valid base64
        payload = payload + '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        json_data = json.loads(decoded.decode())

    result: dict[str, t.Any]
    for result in json_data["items"]:
        if result["type"] == "WebPage":
            res.add(
                res.types.MainResult(
                    url=result["url"],
                    title=result["name"],
                    content=html_to_text(result["description"]),
                    thumbnail=result.get("thumbnail", {}).get("url"),
                )
            )
        elif swisscows_category == "videos" and result["type"] == "VideoCollection":
            for video in result["hasPart"]:
                res.add(_video_result(video))
        elif result["type"] == "ImageObject":
            res.add(
                res.types.LegacyResult(
                    {
                        "template": "images.html",
                        "url": result["url"],
                        "thumbnail_src": result["thumbnail"]["url"],
                        "img_src": result["contentUrl"],
                        "title": result["name"],
                    }
                )
            )
        elif result["type"] == "video":
            res.add(_video_result(result))

    return res
