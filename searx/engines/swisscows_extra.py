# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""Swisscows (images, videos)"""

import base64
import codecs
import hashlib
import json
import random

from datetime import datetime
from urllib.parse import urlencode

import typing as t

from searx.result_types import EngineResults
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


categories = ["videos"]
swisscows_category = "videos"  # possible: "videos", "images"
paging = True
results_per_page = 50

base_url = "https://api.swisscows.com"

CAESAR_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
NONCE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"


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


def generate_nonce_and_signature(url_path: str) -> tuple[str, str]:
    """
    Generate "X-Request-Nonce" and "X-Request-Signature" which are required for accessing
    Swisscows images (reverse engineered from their official website).
    """
    nonce = generate_nonce()
    nonce_shifted = caesar_shift_with_switch_case(nonce, 13)

    signature = sha256_hash_b64_url(url_path + nonce_shifted)
    return (nonce, signature)


def init(_):
    if swisscows_category not in ("videos", "images"):
        raise ValueError("illegal swisscows category: %s" % swisscows_category)

    if swisscows_category == "videos" and results_per_page > 10:
        raise ValueError("results_per_page for swisscows videos can be at most 10")


def request(query: str, params: "OnlineParams") -> None:
    # swisscows images only supports 2 pages
    if swisscows_category == "images" and params["pageno"] > 2:
        params["url"] = None
        return

    # the keys have to be sorted in alphabetic order,
    # otherwise the generated signature won't be accepted!
    url_path = ""
    if swisscows_category == "images":
        args = {
            "itemsCount": results_per_page,
            "locale": "en-US",
            "offset": (params["pageno"] - 1) * results_per_page,
            "query": query,
            "spellcheck": True,
        }
        url_path = f"/v5/images/search?{urlencode(args)}"
    else:
        args = {
            "itemsCount": results_per_page,
            "offset": (params["pageno"] - 1) * results_per_page,
            "query": query,
            "region": "en-US",
            "spellcheck": True,
        }
        url_path = f"/v2/videos/search?{urlencode(args)}"

    nonce, signature = generate_nonce_and_signature(url_path)

    params["headers"].update(
        {
            "X-Request-Nonce": nonce,
            "X-Request-Signature": signature,
        }
    )
    params["url"] = base_url + url_path


def response(resp: "SXNG_Response"):
    res = EngineResults()

    json_data = resp.json()

    # only appears to be the case for images, for videos the data doesn't seem to be encoded
    # payload is encoded as a JSON web token -> 3 parts, separated by "."
    # the actual data is in the center of the encoded string
    if "payload" in json_data:
        payload = json_data["payload"].split(".")[1]
        # pad with '=' to be valid base64
        payload = payload + '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        json_data = json.loads(decoded.decode())

    for result in json_data["items"]:
        if swisscows_category == "images":
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
        else:
            published_date = None
            if result["datePublished"]:
                published_date = datetime.fromisoformat(result["datePublished"])

            res.add(
                res.types.LegacyResult(
                    {
                        "template": "videos.html",
                        "url": result["url"],
                        "title": html_to_text(result["title"]),
                        "content": result["description"],
                        "thumbnail": result["thumbnailUrl"],
                        "length": result["duration"],
                        "iframe_src": result["embedUrl"],
                        "publishedDate": published_date,
                        "views": humanize_number(result["viewCount"]),
                    }
                )
            )

    return res
