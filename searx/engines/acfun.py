# SPDX-License-Identifier: AGPL-3.0-or-later
"""Acfun search engine for searxng"""

from urllib.parse import urlencode
import re
import json
from datetime import datetime, timedelta
from lxml import html

from searx.utils import extract_text

# Metadata
about = {
    "website": "https://www.acfun.cn/",
    "wikidata_id": "Q3077675",
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
    "language": "zh",
}

# Engine Configuration
categories = ["videos"]
paging = True

# Base URL
base_url = "https://www.acfun.cn"


def request(query, params):
    query_params = {"keyword": query, "pCursor": params["pageno"]}
    params["url"] = f"{base_url}/search?{urlencode(query_params)}"
    return params


def response(resp):
    results = []

    matches = re.findall(r'bigPipe\.onPageletArrive\((\{.*?\})\);', resp.text, re.DOTALL)
    if not matches:
        return results

    for match in matches:
        try:
            json_data = json.loads(match)
            raw_html = json_data.get("html", "")
            if not raw_html:
                continue

            tree = html.fromstring(raw_html)

            video_blocks = tree.xpath('//div[contains(@class, "search-video")]')
            if not video_blocks:
                continue

            for video_block in video_blocks:
                video_info = extract_video_data(video_block)
                if video_info and video_info["title"] and video_info["url"]:
                    results.append(video_info)

        except json.JSONDecodeError:
            continue

    return results


def extract_video_data(video_block):
    try:
        data_exposure_log = video_block.get('data-exposure-log')
        video_data = json.loads(data_exposure_log)

        content_id = video_data.get("content_id", "")
        title = video_data.get("title", "")

        url = f"{base_url}/v/ac{content_id}"
        iframe_src = f"{base_url}/player/ac{content_id}"

        create_time = extract_text(video_block.xpath('.//span[contains(@class, "info__create-time")]'))
        video_cover = extract_text(video_block.xpath('.//div[contains(@class, "video__cover")]/a/img/@src')[0])
        video_duration = extract_text(video_block.xpath('.//span[contains(@class, "video__duration")]'))
        video_intro = extract_text(video_block.xpath('.//div[contains(@class, "video__main__intro")]'))

        published_date = None
        if create_time:
            try:
                published_date = datetime.strptime(create_time.strip(), "%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        length = None
        if video_duration:
            try:
                timediff = datetime.strptime(video_duration.strip(), "%M:%S")
                length = timedelta(minutes=timediff.minute, seconds=timediff.second)
            except (ValueError, TypeError):
                pass

        return {
            "title": title,
            "url": url,
            "content": video_intro,
            "thumbnail": video_cover,
            "length": length,
            "publishedDate": published_date,
            "iframe_src": iframe_src,
        }

    except (json.JSONDecodeError, AttributeError, TypeError, ValueError):
        return None
