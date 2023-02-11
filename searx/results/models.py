# SPDX-License-Identifier: AGPL-3.0-or-later
# pyright: basic
# lint: pylint
"""Type definitions of the result items from engines."""

from datetime import datetime
from urllib.parse import ParseResult

from typing import List, Dict, Set
from typing_extensions import TypedDict, NotRequired, Required


__all__ = [
    'Result',
    'UrlResult',
    'Answer',
    'Correction',
    'Suggestion',
    'Infobox',
    'InfoboxUrl',
    'InfoboxImage',
    'InfoboxAttribute',
    'InfoboxRelatedTopic',
    'Map',
    'Paper',
    'Video',
    'Product',
]


class Result(TypedDict):
    """A result from any type"""

    engine: str
    """Internal field. DO NOT USE"""

    weight: float
    """Internal field. DO NOT USE"""

    engines: Set[str]
    """Internal field. DO NOT USE"""

    category: str
    """Internal field. DO NOT USE"""

    positions: List[int]
    """Internal field. DO NOT USE"""

    score: float
    """Internal field. DO NOT USE"""


class MainResult(Result):
    """Result that is going to be displayed as a "main" result"""

    template: NotRequired[str]
    """Template to display the result. The default value is "default.html".
    see searx/templates/simple/result_templates"""


class UrlResult(MainResult):
    """Typical main result: an url, a title and a short description"""

    title: str
    """Title of the result"""

    url: str
    """URL of the result"""

    parsed_url: ParseResult
    """Engines don't have to set this value: it is automatically initialized from the url field.
    However, plugins have to manually update this field when they change the url field"""

    content: NotRequired[str]
    """Content of the result"""


class Default(UrlResult):
    """Default result"""

    iframe_src: NotRequired[str]
    """URL of an iframe to add to the result."""

    audio_src: NotRequired[str]
    """URL of <audio> element"""

    img_src: NotRequired[str]
    """URL of an image to include the result"""

    thumbnail: NotRequired[str]
    """URL of a thumbnail"""

    publishedDate: NotRequired[datetime]
    """Publication date"""

    length: NotRequired[str]
    """Length of the content (for audio or video)"""

    author: NotRequired[str]
    """Author of the content (for audio, video, image, ...)"""

    metadata: NotRequired[Dict]
    """Dictionnary to allow paging"""


class KeyValueResult(MainResult):
    """a set of key value to display, useful for the DB engines.

    The template field must be "key-value.html", all other values are
    displayed.

    template must be equal to `key-value.html`
    """


class Answer(Result):
    """Answer item in the result list.  The answer result item is used in
    the :origin:`results.html <searx/templates/simple/results.html>` template.
    A answer item is a dictionary type with dedicated keys and values."""

    answer: Required[str]
    """The answer string append by the engine."""

    url: NotRequired[str]
    """A link that is related to the answer (e.g. the origin of the answer)."""


class Correction(Result):
    """Correction item in the result list.  The correction result item is used in
    the :origin:`results.html <searx/templates/simple/results.html>` template.
    A correction item is a dictionary type with dedicated keys and values."""

    url: str
    """The SearXNG search URL for the correction term."""

    title: str
    """The 'correction' string append by the engine."""


class Suggestion(Result):
    """Suggestion item in the result list.  The suggestion result item is used in
    the :origin:`infobox.html <searx/templates/simple/results.html>` template.
    A sugestion item is a dictionary type with dedicated keys and values."""

    suggestion: Required[str]
    """The SearXNG search URL for the suggestion term."""


class InfoboxUrl(TypedDict):
    """A list of dictionaries with links shown in the infobox.
    A **url** item in the ``infobox.urls`` list is a dicticonary
    """

    title: str
    """Title of the URL"""

    url: str
    """URL by itself : https:/..."""

    entity: str
    """set by some engines but unused"""

    official: bool
    """set by some engines but unused (oscar)"""


class InfoboxImage(TypedDict):
    """Image in a infobox"""

    src: str
    """URL of the image"""

    alt: str
    """description of the image / alt attribute"""


class InfoboxAttribute(TypedDict):
    """A **attribute** item in the ``infobox.attributes`` list is a dictionary"""

    label: str
    """Label of the attribute"""

    value: str
    """Value of the attribute. If set, the image field is ignored"""

    image: InfoboxImage
    """Image for this attribute. Ignored if the field value is set"""

    entity: str
    """set by some engines but unused"""


class InfoboxRelatedTopic(TypedDict):
    """A **topic** item in the ``infobox.relatedTopics`` list is a dictionary"""

    suggestion: str
    """suggested search query"""

    name: str
    """set by some engines but unused"""


class Infobox(Result):
    """Infobox item in the result list.  The infobox result item is used in the
    :origin:`infobox.html <searx/templates/simple/infobox.html>` template.
    A infobox item is a dictionary type with dedicated keys and values.
    """

    infobox: Required[str]
    """Name of the infobox (mandatory)."""

    id: str
    """URL of the infobox.  Will be used to merge infoboxes."""

    content: str
    """Content of the infobox (the description)"""

    img_src: str
    """URL of the image to show in the infobox"""

    urls: List[InfoboxUrl]
    """A list of dictionaries with links shown in the infobox."""

    attributes: List[InfoboxAttribute]
    """A list of dictionaries with attributes shown in the infobox"""

    relatedTopics: List[InfoboxRelatedTopic]
    """A list of dictionaries with related topics shown in the infobox"""


class Torrent(UrlResult):
    """Torrent result

    The template key has to be "torrent.html"
    """


class Map(UrlResult):
    """Map result

    The template key has to be "map.html"
    """


class Video(UrlResult):
    """Video result

    The template key has to be "videos.html"
    """


class Product(UrlResult):
    """Product from a shop result

    The template key has to be "product.html"
    """


class Paper(UrlResult):
    """Paper from a publication result

    the template key must be "paper.html"
    """
