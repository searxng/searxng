# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Infobox item in the result list.  The infobox result item is used in the
:origin:`infobox.html <searx/templates/simple/infobox.html>` template.

A infobox item is a dictionary type with dedicated keys and values.

.. code:: python

   results.append({
       'infobox'       : str,
       'id'            : str,
       'content'       : str,
       'img_src'       : str,
       'urls'          : [url, ...],
       'attributes'    : [attribute, ...],
       'relatedTopics' : [topic, ...],
       'engine'        : engine,
   })

infobox : ``str``
  Name of the infobox (mandatory).

id : ``str``
  URL of the infobox.  Will be used to merge infoboxes.

content : ``str``
  Content of the infobox (the description)

img_src :
  URL of the image to show in the infobox

urls : ``[url, ...]``
  A list of dictionaries with links shown in the infobox.  A **url** item in the
  ``infobox.urls`` list is a dicticonary:

  .. code:: python

     url = {
         'title'    : str,
         'url'      : str,
         'entity'   : str,  # set by some engines but unused
         'official' : bool, # set by some engines but unused (oscar)
     }

attributes : ``[attribute, ...]``
  A **attribute** item in the ``infobox.attributes`` list is a dictionary:

  .. code:: python

     attribute = {
         'label'    : str,
         'value'    : str,
         'image'    : {
             'src': str,
             'alt': str,
         },
         'entity'   : str,  # set by some engines but unused
     }

relatedTopics : ``[topic, ...]``
  A **topic** item in the ``infobox.relatedTopics`` list is a dictionary:

  .. code:: python

     topic = {
         'suggestion'  : str,
         'name'        : str,  # set by some engines but unused
     }

"""

from urllib.parse import urlparse
from searx.engines import engines
from .core import (
    result_content_len,
    compare_urls,
)


def is_infobox(result):
    """Returns ``True`` if result type is :py:obj:`.infobox`, otherwise ``False``

    In the result list a infobox item is identified by the existence of the key
    ``infobox``.
    """
    return 'infobox' in result


class Infoboxes(list):
    """List of infobox items in the :py:obj:`.container.ResultContainer`"""


def merge_two_infoboxes(infobox1, infobox2):
    # pylint: disable=too-many-branches, too-many-statements

    # get engines weights
    if hasattr(engines[infobox1['engine']], 'weight'):
        weight1 = engines[infobox1['engine']].weight
    else:
        weight1 = 1
    if hasattr(engines[infobox2['engine']], 'weight'):
        weight2 = engines[infobox2['engine']].weight
    else:
        weight2 = 1

    if weight2 > weight1:
        infobox1['engine'] = infobox2['engine']

    infobox1['engines'] |= infobox2['engines']

    if 'urls' in infobox2:
        urls1 = infobox1.get('urls', None)
        if urls1 is None:
            urls1 = []

        for url2 in infobox2.get('urls', []):
            unique_url = True
            parsed_url2 = urlparse(url2.get('url', ''))
            entity_url2 = url2.get('entity')
            for url1 in urls1:
                if (entity_url2 is not None and url1.get('entity') == entity_url2) or compare_urls(
                    urlparse(url1.get('url', '')), parsed_url2
                ):
                    unique_url = False
                    break
            if unique_url:
                urls1.append(url2)

        infobox1['urls'] = urls1

    if 'img_src' in infobox2:
        img1 = infobox1.get('img_src', None)
        img2 = infobox2.get('img_src')
        if img1 is None:
            infobox1['img_src'] = img2
        elif weight2 > weight1:
            infobox1['img_src'] = img2

    if 'attributes' in infobox2:
        attributes1 = infobox1.get('attributes')
        if attributes1 is None:
            infobox1['attributes'] = attributes1 = []

        attributeSet = set()
        for attribute in attributes1:
            label = attribute.get('label')
            if label not in attributeSet:
                attributeSet.add(label)
            entity = attribute.get('entity')
            if entity not in attributeSet:
                attributeSet.add(entity)

        for attribute in infobox2.get('attributes', []):
            if attribute.get('label') not in attributeSet and attribute.get('entity') not in attributeSet:
                attributes1.append(attribute)

    if 'content' in infobox2:
        content1 = infobox1.get('content', None)
        content2 = infobox2.get('content', '')
        if content1 is not None:
            if result_content_len(content2) > result_content_len(content1):
                infobox1['content'] = content2
        else:
            infobox1['content'] = content2


def infobox_modify_url(modify_url_func, result):
    """Modify URL fields in the infobox-result.

    :param func modify_url_func: A function that gets one argument; a *url*
        field of the ``result`` item.  The function returns the URL to use
        instead (even the URL is not modified).  To drop the 'url' field from
        the result the function returns ``None``.  This function is called for
        each field that contains URL.

    :param dict result: The result item.

    """

    if not is_infobox(result):
        return

    img_src = result.get('img_src')
    urls = result.get('urls', [])
    attributes = result.get('attributes', [])

    # infobox.img_src
    if img_src:
        _img_src = modify_url_func(img_src)
        if _img_src is None:
            # logger.debug("infobox: remove img_src from %s", infobox_name)
            del result['img_src']
        elif _img_src != img_src:
            # logger.debug("infobox: redirect img_src %s", _img_src)
            result['img_src'] = _img_src

    # A 'url' item in the infobox.urls list has this attributes:
    #
    #     'title', 'url'

    for url in urls:
        url_url = url.get('url')
        if url_url:
            _url_url = modify_url_func(url_url)
            if _url_url is None:
                # logger.debug("infobox: remove url %s", url)
                urls.remove(url)
            elif _url_url != url_url:
                # logger.debug("infobox: redirect url %s", _url_url)
                url['url'] = _url_url

    # A 'attr' item in the infobox.attributes list has this attributes:
    #
    #      'label', 'image'

    for attr in attributes:
        image = attr.get('image')
        if image:
            _image = modify_url_func(image)
            if image is None:
                # logger.debug("infobox: remove image %s", attr)
                attributes.remove(attr)
            elif _image != image:
                # logger.debug("infobox: redirect %s", _image)
                attr['image'] = _image
