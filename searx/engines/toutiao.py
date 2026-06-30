# SPDX-License-Identifier: AGPL-3.0-or-later
"""Toutiao (今日头条) search engine

`Toutiao`_ is a Chinese search engine by ByteDance that aggregates news,
videos, encyclopedia articles and more. Supports "synthesis" (综合),
"information" (资讯), "atlas" (图片),
"weitoutiao" (微头条) and "video" (视频) categories via the
``toutiao_pd`` setting.

For most categories, results are JSON embedded in
``<script type="application/json">`` tags. For atlas (images), results
are parsed directly from the HTML DOM.

.. _Toutiao: https://www.toutiao.com
"""

import json
import re
import typing as t

from datetime import datetime
from html import unescape
from urllib.parse import urlencode, urlparse, parse_qs, unquote

from lxml import html as lxml_html

from searx import logger
from searx.enginelib import EngineCache
from searx.utils import html_to_text
from searx.exceptions import SearxEngineCaptchaException
from searx.network import post as http_post

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response

log = logger.getChild(__name__)

about = {
    "website": "https://www.toutiao.com",
    "wikidata_id": "Q24835387",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

language = "zh"
categories = ["general", "news"]
paging = True
max_page = 10
time_range_support = True

base_url = "https://so.toutiao.com"

# Search scope: "all" = web-wide (default), "site" = Toutiao-only
# Override via toutiao_filter_vendor in settings.yml
toutiao_filter_vendor = "all"

# Search category: "synthesis" (综合, default), "information" (资讯),
# "atlas" (图片), "weitoutiao" (微头条),
# or "video" (视频)
# Override via toutiao_pd in settings.yml
toutiao_pd = "synthesis"

# SearXNG time range key -> Toutiao filter_period value
time_range_dict = {
    "day": "day",
    "week": "week",
    "month": "month",
    "year": "year",
}

# Non-result card types to skip
_SKIP_TEMPLATE_KEYS = {
    "SearchBar",
    "SearchFilter",
    "BottomBar",
    "LoadMore",
    "71-undefined",  # captcha / verification challenge card
    "79-undefined",  # "no results found" placeholder card
}

_TTWID_REGISTER_URL = "https://ttwid.bytedance.com/ttwid/union/register/"
_TTWID_CACHE_KEY = "ttwid"
_TTWID_CACHE_EXPIRATION = 3600  # re-fetch hourly, cached in EngineCache

CACHE: EngineCache
"""Stores the ttwid cookie to avoid re-fetching on every request."""


def setup(engine_settings: dict[str, t.Any]) -> bool:
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache("cache" + engine_settings["name"])
    return True


def _get_ttwid() -> str:
    """Fetch a ttwid cookie from ByteDance's registration API.

    The ttwid helps avoid anti-bot detection (isCheating=2) on some
    search tabs. The cookie is stored in EngineCache with a 1-hour TTL.
    """
    cached: str | None = CACHE.get(_TTWID_CACHE_KEY)
    if cached:
        return cached

    try:
        resp: SXNG_Response = http_post(
            _TTWID_REGISTER_URL,
            json={
                "region": "cn",
                "aid": 24,
                "needFid": False,
                "service": "so.toutiao.com",
                "cbUrlProtocol": "https",
                "union": True,
            },
        )
        ttwid_value: str | None = resp.cookies.get("ttwid")
        if ttwid_value:
            CACHE.set(
                key=_TTWID_CACHE_KEY,
                value=ttwid_value,
                expire=_TTWID_CACHE_EXPIRATION,
            )
            return ttwid_value
    except Exception as e:  # pylint: disable=broad-except
        log.error("Failed to fetch ttwid: %s", e)

    return ""


def request(query, params):
    """Build a Toutiao search request."""
    page_num = params["pageno"] - 1

    query_params = {
        "dvpf": "pc",
        "source": "search_subtab_switch",
        "keyword": query,
        "enable_druid_v2": "1",
        "pd": toutiao_pd,
        "page_num": page_num,
    }

    if toutiao_pd == "information":
        query_params["from"] = "news"
        query_params["cur_tab_title"] = "news"
        query_params["action_type"] = "search_subtab_switch"
    elif toutiao_pd == "atlas":
        query_params["from"] = "gallery"
        query_params["cur_tab_title"] = "gallery"
        query_params["action_type"] = "search_subtab_switch"
    elif toutiao_pd == "weitoutiao":
        query_params["from"] = "weitoutiao"
        query_params["cur_tab_title"] = "weitoutiao"
        query_params["action_type"] = "search_subtab_switch"
    elif toutiao_pd == "video":
        query_params["from"] = "video"
        query_params["cur_tab_title"] = "video"
        query_params["action_type"] = "search_subtab_switch"
    else:
        # synthesis (综合): default search tab
        query_params["from"] = "search_tab"
        query_params["cur_tab_title"] = "search_tab"
        query_params["action_type"] = "search_subtab_switch"
        query_params["filter_vendor"] = toutiao_filter_vendor
        query_params["index_resource"] = toutiao_filter_vendor

    time_range = params.get("time_range")
    if time_range in time_range_dict:
        query_params["filter_period"] = time_range_dict[time_range]

    params["url"] = f"{base_url}/search?{urlencode(query_params)}"
    params["allow_redirects"] = False

    ttwid = _get_ttwid()
    if ttwid:
        params["cookies"]["ttwid"] = ttwid

    return params


def response(resp):
    """Parse Toutiao search results."""

    if resp.status_code == 302:
        location = resp.headers.get("Location", "")
        if "verify" in location or "captcha" in location:
            raise SearxEngineCaptchaException()

    if toutiao_pd == "atlas":
        return _parse_atlas(resp)

    results = []

    dom = lxml_html.fromstring(resp.text)
    script_nodes = dom.xpath(
        '//script[@data-druid-card-data-id and @type="application/json"]'
    )

    for node in script_nodes:
        try:
            card_data = json.loads(node.text_content())
        except (json.JSONDecodeError, ValueError):
            continue

        data = card_data.get("data", {})
        template_key = data.get("template_key", "")

        # Detect captcha / verification challenge
        if template_key == "71-undefined" and data.get("cell_type") == 71:
            decision = data.get("decision_conf", "")
            if isinstance(decision, str):
                try:
                    decision = json.loads(decision)
                except (json.JSONDecodeError, ValueError):
                    pass
            if isinstance(decision, dict) and decision.get("type") == "verify":
                raise SearxEngineCaptchaException(
                    message=f"toutiao [{toutiao_pd}]: slide captcha challenge detected"
                )

        if template_key in _SKIP_TEMPLATE_KEYS:
            continue

        parsed = _parse_card(card_data)
        if parsed:
            if isinstance(parsed, list):
                results.extend(parsed)
            else:
                results.append(parsed)

    return results


def _parse_atlas(resp):
    """Parse image (图片) results from the HTML DOM.

    Each image card is a ``<div data-log-extra>`` element containing an
    ``<img>`` for the thumbnail, an ``<a>`` with the source page URL
    (wrapped in a search redirect), and a ``<span class="text-underline-hover">``
    with the resolution string (e.g. "800x600").
    """
    results = []
    dom = lxml_html.fromstring(resp.text)

    for card in dom.xpath("//div[@data-log-extra]"):
        try:
            log_extra = json.loads(card.get("data-log-extra", "{}"))
        except (json.JSONDecodeError, ValueError):
            continue

        template_key = log_extra.get("template_key", "")
        if template_key in _SKIP_TEMPLATE_KEYS:
            continue

        imgs = card.xpath(".//img")
        if not imgs:
            continue
        img_src = imgs[0].get("src", "")
        if not img_src:
            continue

        # Extract title and source page URL from the link
        title = ""
        source_url = img_src
        links = card.xpath(".//a")
        if links:
            title = links[0].text_content().strip()
            href = links[0].get("href", "")
            if href:
                source_url = _extract_redirect_url(href) or href

        # Thumbnail: use the img src as-is (CDN proxy with crop, or original)
        thumbnail_src = img_src.replace("http://", "https://")

        # Original image: strip CDN crop parameters if present
        img_original = re.sub(r"~tplv-[^.]+", "", img_src).replace(
            "http://", "https://"
        )

        # Resolution
        resolution = ""
        res_spans = card.xpath('.//span[contains(@class, "text-underline-hover")]')
        if res_spans:
            resolution = res_spans[0].text_content().strip()

        results.append(
            {
                "template": "images.html",
                "url": source_url.replace("http://", "https://"),
                "thumbnail_src": thumbnail_src,
                "img_src": img_original,
                "title": title or "",
                "resolution": resolution,
            }
        )

    return results


def _extract_redirect_url(href):
    """Extract the final destination URL from a Toutiao search redirect chain."""
    parsed = urlparse(href)
    qs = parse_qs(parsed.query)
    url = unquote(qs["url"][0]) if "url" in qs else None
    if not url:
        return None
    # Toutiao sometimes double-wraps redirects
    parsed2 = urlparse(url)
    qs2 = parse_qs(parsed2.query)
    if "url" in qs2:
        return unquote(qs2["url"][0])
    return url


def _parse_card(card_data):
    """Dispatch card data to the appropriate parser by template_key."""
    data = card_data.get("data", {})
    template_key = data.get("template_key", "")

    if template_key in _SKIP_TEMPLATE_KEYS:
        return None

    if "toutiao_web" in template_key:
        return _parse_web_result(data)
    if "video_oracle" in template_key:
        return _parse_video_oracle(data)
    if "self_video" in template_key:
        return _parse_result(data)
    if "baike" in template_key:
        return _parse_result(data)
    if template_key.startswith("50-"):
        return _parse_weitoutiao(data)

    # Default: article / news results (undefined-default, etc.)
    return _parse_result(data)


def _parse_result(data):
    """Parse a generic search result (article, video, encyclopedia, etc.)."""
    display = data.get("display", {})
    if not isinstance(display, dict):
        return None

    title = _get_title(data, display)
    url = _get_url(data, display)
    content = _get_content(data, display)

    if not title or not url:
        return None

    result: dict[str, object] = {
        "title": title,
        "url": url,
        "content": content,
    }

    published_date = _get_published_date(data)
    if published_date:
        result["publishedDate"] = published_date

    thumbnail = _get_thumbnail(data)
    if thumbnail:
        result["thumbnail"] = thumbnail

    return result


def _parse_web_result(data):
    """Parse an external web result (67-toutiao_web type)."""
    display = data.get("display", {})

    title = display.get("title", {}).get("text", "") or data.get("title", "")
    url = data.get("url", "") or display.get("info", {}).get("url", "")
    content = display.get("summary", {}).get("text", "") or ""

    if not title or not url:
        return None

    return {
        "title": html_to_text(unescape(title)),
        "url": url,
        "content": html_to_text(unescape(content)) if content else "",
    }


def _parse_video_oracle(data):
    """Parse a video aggregation card (26-video_oracle type), returns multiple results."""
    display_list = data.get("display", [])
    if not isinstance(display_list, list):
        return None

    results = []
    for item in display_list:
        title = _get_title(item, item.get("display", {}))
        url = _get_url(item, item.get("display", {}))
        content = _get_content(item, item.get("display", {}))

        if not title or not url:
            continue

        result: dict[str, object] = {
            "title": title,
            "url": url,
            "content": content,
        }

        published_date = _get_published_date(item)
        if published_date:
            result["publishedDate"] = published_date

        thumbnail = _get_thumbnail(item)
        if thumbnail:
            result["thumbnail"] = thumbnail

        results.append(result)

    return results if results else None


def _extract_sslocal_tid(data):
    """Extract the thread id (tid) from an sslocal:// deep-link.

    Weitoutiao cards expose app deep-links such as
    ``sslocal://thread_detail?...&tid=1869353535365132`` in the
    ``schema``, ``source_url`` or ``pc_schema`` fields. The ``tid``
    equals the post group id and can build a real web article URL.
    """
    for key in ("schema", "source_url", "pc_schema", "comment_schema"):
        value = data.get(key, "")
        if isinstance(value, str) and value.startswith("sslocal://"):
            qs = parse_qs(urlparse(value).query)
            tid = qs.get("tid", [""])[0]
            if tid and tid.isdigit() and tid != "0":
                return tid
    return None


def _parse_weitoutiao(data):
    """Parse a weitoutiao (微头条) result.

    Weitoutiao posts have no title field. The content text is used as both
    title (truncated) and content, prefixed with the author name.
    URL comes from ``pc_schema`` or is constructed from ``id``.
    """
    content = data.get("content", "") or data.get("rich_content", "")
    if not content:
        return None

    content = html_to_text(unescape(content))
    media_name = data.get("media_name", "")

    # Build title from content: first line or first 80 chars
    first_line = content.split("\n")[0].strip()
    if len(first_line) > 80:
        title = first_line[:80] + "..."
    else:
        title = first_line
    if media_name:
        title = f"{media_name}: {title}"

    # URL: prefer pc_schema web path, then the post id, then the tid
    # embedded in any sslocal:// deep-link. App deep-links (sslocal://...)
    # are never usable as-is, so they are converted to web article URLs.
    url = ""
    pc_schema = data.get("pc_schema", "")
    if pc_schema and pc_schema.startswith("/"):
        url = f"https://www.toutiao.com{pc_schema}"
    if not url:
        post_id = data.get("id") or data.get("group_id") or _extract_sslocal_tid(data)
        if post_id:
            url = f"https://www.toutiao.com/a{post_id}/"

    if not url:
        return None

    result: dict[str, object] = {
        "title": title,
        "url": url,
        "content": content,
    }

    published_date = _get_published_date(data)
    if published_date:
        result["publishedDate"] = published_date

    thumbnail = _get_thumbnail(data)
    if thumbnail:
        result["thumbnail"] = thumbnail

    return result


def _get_title(data, display):
    """Extract title with fallback chain."""
    title_field = display.get("title", {})
    if isinstance(title_field, dict):
        title = title_field.get("text", "")
    elif isinstance(title_field, str):
        title = title_field
    else:
        title = ""
    title = title or data.get("title", "")
    if title:
        title = html_to_text(unescape(title))
    return title


def _get_url(data, display):
    """Extract URL, preferring direct links over redirect URLs.

    App deep-links (sslocal://) are rejected — they are not usable in a
    browser and must be converted to web article URLs via group_id fallback.
    """

    def _is_bad_url(val):
        if not isinstance(val, str) or not val:
            return True
        return val.startswith("sslocal://") or "preview_article" in val

    url = (
        display.get("info", {}).get("url", "")
        or data.get("article_url", "")
        or data.get("url", "")
    )

    # Reject sslocal:// deep-links and preview_article URLs so the
    # source_url / group_id fallbacks below get a chance to work.
    if _is_bad_url(url):
        url = ""

    if not url and data.get("source_url"):
        source_url = data["source_url"]
        if source_url.startswith("/"):
            url = f"https://www.toutiao.com{source_url}"
        elif not source_url.startswith("sslocal://"):
            url = source_url

    # Fallback: construct URL from group_id
    if not url and data.get("group_id"):
        url = f"https://www.toutiao.com/a{data['group_id']}/"

    if url and url.startswith("/"):
        url = f"https://www.toutiao.com{url}"

    return url


def _get_content(data, display):
    """Extract summary content with fallback chain."""
    content = display.get("summary", {}).get("text", "") or data.get("abstract", "")
    if content:
        content = html_to_text(unescape(content))
    return content


def _get_published_date(data):
    """Extract publish date from Unix timestamp fields."""
    timestamp = data.get("publish_time") or data.get("create_time")
    if timestamp:
        try:
            ts = int(timestamp)
            if ts > 0:
                return datetime.fromtimestamp(ts)  # noqa: DTZ006
        except (ValueError, TypeError, OSError):
            pass
    return None


def _get_thumbnail(data):
    """Extract thumbnail URL."""
    image_list = data.get("image_list")
    if image_list and isinstance(image_list, list):
        first_img = image_list[0]
        if isinstance(first_img, dict):
            img_url = first_img.get("url", "")
        elif isinstance(first_img, str):
            img_url = first_img
        else:
            img_url = ""
        if img_url:
            return img_url.replace("http://", "https://")

    for key in (
        "image_url",
        "middle_image_url",
        "thumbnail_url",
        "large_thumbnail_url",
    ):
        img = data.get(key, "")
        if img:
            return img.replace("http://", "https://")

    return None
