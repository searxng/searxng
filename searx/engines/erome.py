# SPDX-License-Identifier: AGPL-3.0-or-later
"""EroMe_ is an adult (18+) hosting site for image & video albums.  There is no
official API, this engine scrapes the public search page.

This engine is part of the ``adult`` category (tab), it does not show up in
the ``videos`` category of a default instance.

.. _EroMe: https://www.erome.com

"""

import re
from urllib.parse import urlencode, urljoin

from lxml import html

from searx.utils import extract_text

about = {
    "website": "https://www.erome.com",
    "wikidata_id": None,
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "HTML",
}

# engine dependent config
categories = ["adult"]
paging = True
safesearch = False
"""The site has no safesearch, it is 18+ only."""

base_url = "https://www.erome.com"
search_url = base_url + "/search"

order = "hot"
"""Result order: ``hot`` (most viewed) or ``new``."""

ALBUM_ANCHOR_XPATH = (
    '//a[img and (contains(@href, "://www.erome.com/a/") or starts-with(@href, "/a/"))]'
)
"""An album card is anchored by a link that contains a preview image.  The
album title is a second link with the same ``href`` but without an image."""

VIEWS_RE = re.compile(r"([\d.,\s]+)\s*K?", re.IGNORECASE)


def request(query, params):
    args = {"q": query}
    if order == "new":
        args["o"] = "new"
    if params["pageno"] > 1:
        args["page"] = params["pageno"]
    params["url"] = f"{search_url}?{urlencode(args)}"
    return params


def response(resp):
    results = []
    doc = html.fromstring(resp.text)
    seen = set()

    for anchor in doc.xpath(ALBUM_ANCHOR_XPATH):
        href = anchor.get("href") or ""
        url = urljoin(base_url + "/", href)
        album_id = url.rstrip("/").rsplit("/", 1)[-1]

        if not album_id or album_id in seen:
            continue

        thumbnail = _thumbnail(anchor)
        if not thumbnail:
            # without a preview image the card is useless in a media search
            continue
        seen.add(album_id)

        results.append(
            {
                "template": "videos.html",
                "url": url,
                "title": _title(doc, anchor, href, album_id),
                "thumbnail": thumbnail,
                "views": _views(anchor),
            }
        )

    return results


def _thumbnail(anchor):
    for img in anchor.xpath("./img"):
        src = img.get("data-src") or img.get("src") or ""
        if src.startswith("//"):
            src = "https:" + src
        if src.startswith("http"):
            return src
    return None


def _title(doc, anchor, href, album_id):
    # the title is a link with the same href but without an image inside
    if '"' not in href:
        title_el = doc.xpath(f'//a[@href="{href}"][not(img)][1]')
        if title_el:
            title = extract_text(title_el[0]).strip()
            if title:
                return title
    # fallbacks: alt / title attribute of the preview image
    for name in ("alt", "title"):
        value = (anchor.xpath(f"./img/@{name}") or [""])[0].strip()
        if value:
            return value
    return album_id


def _views(anchor):
    """Parse view counts like ``1841,2K`` / ``11131K`` / ``3`` rendered inside
    the preview anchor.  Returns an int or None."""
    text = " ".join(t.strip() for t in anchor.xpath("./text()") if t.strip())
    if not text:
        return None
    match = VIEWS_RE.search(text)
    if not match:
        return None
    number = match.group(1).strip().replace(" ", "").replace(".", "")
    try:
        if text.upper().endswith("K"):
            return int(float(number.replace(",", ".")) * 1000)
        return int(number)
    except ValueError:
        return None
