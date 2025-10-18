.. _simple theme templates:

======================
Simple Theme Templates
======================

The simple template is complex, it consists of many different elements and also
uses macros and include statements.  The following is a rough overview that we
would like to give the developer at hand, details must still be taken from the
:origin:`sources <searx/templates/simple/>`.

A :ref:`result item <result types>` can be of different media types.  The media
type of a result is defined by the :py:obj:`result_type.Result.template`.  To
set another media-type as :ref:`template default`, the field ``template``
in the result item must be set to the desired type.

.. contents:: Contents
   :depth: 2
   :local:
   :backlinks: entry


.. _result template macros:

Result template macros
======================

.. _macro result_header:

``result_header``
-----------------

Execpt ``image.html`` and some others this macro is used in nearly all result
types in the :ref:`main result list`.

Fields used in the template :origin:`macro result_header
<searx/templates/simple/macros.html>`:

url :  :py:class:`str`
  Link URL of the result item.

title :  :py:class:`str`
  Link title of the result item.

img_src, thumbnail : :py:class:`str`
  URL of a image or thumbnail that is displayed in the result item.


.. _macro result_sub_header:

``result_sub_header``
---------------------

Execpt ``image.html`` and some others this macro is used in nearly all result
types in the :ref:`main result list`.

Fields used in the template :origin:`macro result_sub_header
<searx/templates/simple/macros.html>`:

publishedDate : :py:obj:`datetime.datetime`
  The date on which the object was published.

length: :py:obj:`datetime.timedelta`
  Playing duration in seconds.

views: :py:class:`str`
  View count in humanized number format.

author : :py:class:`str`
  Author of the title.

metadata : :py:class:`str`
  Miscellaneous metadata.


.. _engine_data:

``engine_data_form``
--------------------

The ``engine_data_form`` macro is used in :origin:`results,html
<searx/templates/simple/results.html>` in a HTML ``<form/>`` element.  The
intention of this macro is to pass data of a engine from one :py:obj:`response
<searx.engines.demo_online.response>` to the :py:obj:`searx.search.SearchQuery`
of the next :py:obj:`request <searx.engines.demo_online.request>`.

To pass data, engine's response handler can append result items of typ
``engine_data``.  This is by example used to pass a token from the response to
the next request:

.. code:: python

   def response(resp):
       ...
       results.append({
          'engine_data': token,
          'key': 'next_page_token',
       })
       ...
       return results

   def request(query, params):
       page_token = params['engine_data'].get('next_page_token')


.. _main result list:

Main Result List
================

The **media types** of the **main result type** are the template files in
the :origin:`result_templates <searx/templates/simple/result_templates>`.

.. _template default:

``default.html``
----------------

Displays result fields from:

- :ref:`macro result_header` and
- :ref:`macro result_sub_header`

Additional fields used in the :origin:`default.html
<searx/templates/simple/result_templates/default.html>`:

content :  :py:class:`str`
  General text of the result item.

iframe_src : :py:class:`str`
  URL of an embedded ``<iframe>`` / the frame is collapsible.

audio_src : uri,
  URL of an embedded ``<audio controls>``.


.. _template images:

``images.html``
---------------

The images are displayed as small thumbnails in the main results list.

title :  :py:class:`str`
  Title of the image.

thumbnail_src : :py:class:`str`
  URL of a preview of the image.

resolution :py:class:`str`
  The resolution of the image (e.g. ``1920 x 1080`` pixel)


Image labels
~~~~~~~~~~~~

Clicking on the preview opens a gallery view in which all further metadata for
the image is displayed.  Addition fields used in the :origin:`images.html
<searx/templates/simple/result_templates/images.html>`:

img_src : :py:class:`str`
  URL of the full size image.

content:  :py:class:`str`
  Description of the image.

author:  :py:class:`str`
  Name of the author of the image.

img_format : :py:class:`str`
  The format of the image (e.g. ``png``).

source : :py:class:`str`
  Source of the image.

filesize: :py:class:`str`
  Size of bytes in :py:obj:`human readable <searx.humanize_bytes>` notation
  (e.g. ``MB`` for 1024 \* 1024 Bytes filesize).

url : :py:class:`str`
  URL of the page from where the images comes from (source).


.. _template videos:

``videos.html``
---------------

Displays result fields from:

- :ref:`macro result_header` and
- :ref:`macro result_sub_header`

Additional fields used in the :origin:`videos.html
<searx/templates/simple/result_templates/videos.html>`:

iframe_src : :py:class:`str`
  URL of an embedded ``<iframe>`` / the frame is collapsible.

  The videos are displayed as small thumbnails in the main results list, there
  is an additional button to collaps/open the embeded video.

content :  :py:class:`str`
  Description of the code fragment.


.. _template torrent:

``torrent.html``
----------------

.. _magnet link: https://en.wikipedia.org/wiki/Magnet_URI_scheme
.. _torrent file: https://en.wikipedia.org/wiki/Torrent_file

Displays result fields from:

- :ref:`macro result_header` and
- :ref:`macro result_sub_header`

Additional fields used in the :origin:`torrent.html
<searx/templates/simple/result_templates/torrent.html>`:

magnetlink:
  URL of the `magnet link`_.

torrentfile
  URL of the `torrent file`_.

seed : ``int``
  Number of seeders.

leech : ``int``
  Number of leecher

filesize : ``int``
  Size in Bytes (rendered to human readable unit of measurement).

files : ``int``
  Number of files.


.. _template map:

``map.html``
------------

.. _GeoJSON: https://en.wikipedia.org/wiki/GeoJSON
.. _Leaflet: https://github.com/Leaflet/Leaflet
.. _bbox: https://wiki.openstreetmap.org/wiki/Bounding_Box
.. _HTMLElement.dataset: https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/dataset
.. _Nominatim: https://nominatim.org/release-docs/latest/
.. _Lookup: https://nominatim.org/release-docs/latest/api/Lookup/
.. _place_id is not a persistent id:
    https://nominatim.org/release-docs/latest/api/Output/#place_id-is-not-a-persistent-id
.. _perma_id: https://wiki.openstreetmap.org/wiki/Permanent_ID
.. _country code: https://wiki.openstreetmap.org/wiki/Country_code

Displays result fields from:

- :ref:`macro result_header` and
- :ref:`macro result_sub_header`

Additional fields used in the :origin:`map.html
<searx/templates/simple/result_templates/map.html>`:

content :  :py:class:`str`
  Description of the item.

address_label : :py:class:`str`
  Label of the address / default ``_('address')``.

geojson : GeoJSON_
  Geometries mapped to HTMLElement.dataset_ (``data-map-geojson``) and used by
  Leaflet_.

boundingbox : ``[ min-lon, min-lat, max-lon, max-lat]``
  A bbox_ area defined by min longitude , min latitude , max longitude and max
  latitude.  The bounding box is mapped to HTMLElement.dataset_
  (``data-map-boundingbox``) and is used by Leaflet_.

longitude, latitude : :py:class:`str`
  Geographical coordinates, mapped to HTMLElement.dataset_ (``data-map-lon``,
  ``data-map-lat``) and is used by Leaflet_.

address : ``{...}``
  A dicticonary with the address data:

  .. code:: python

     address = {
         'name'          : str,  # name of object
         'road'          : str,  # street name of object
         'house_number'  : str,  # house number of object
         'postcode'      : str,  # postcode of object
         'country'       : str,  # country of object
         'country_code'  : str,
         'locality'      : str,
     }

  country_code : :py:class:`str`
    `Country code`_ of the object.

  locality : :py:class:`str`
    The name of the city, town, township, village, borough, etc. in which this
    object is located.

links : ``[link1, link2, ...]``
  A list of links with labels:

  .. code:: python

     links.append({
         'label'       : str,
         'url'         : str,
         'url_label'   : str,  # set by some engines but unused (oscar)
     })

data : ``[data1, data2, ...]``
  A list of additional data, shown in two columns and containing a label and
  value.

  .. code:: python

     data.append({
        'label'   : str,
        'value'   : str,
        'key'     : str,  # set by some engines but unused
     })

type : :py:class:`str`  # set by some engines but unused (oscar)
  Tag label from :ref:`OSM_KEYS_TAGS['tags'] <update_osm_keys_tags.py>`.

type_icon : :py:class:`str`  # set by some engines but unused (oscar)
  Type's icon.

osm : ``{...}``
  OSM-type and OSM-ID, can be used to Lookup_ OSM data (Nominatim_). There is
  also a discussion about "`place_id is not a persistent id`_" and the
  perma_id_.

  .. code:: python

     osm = {
         'type': str,
         'id':   str,
     }

  type : :py:class:`str`
    Type of osm-object (if OSM-Result).

  id :
    ID of osm-object (if OSM-Result).

  .. hint::

     The ``osm`` property is set by engine ``openstreetmap.py``, but it is not
     used in the ``map.html`` template yet.



.. _template paper:

``paper.html``
--------------

.. _BibTeX format: https://www.bibtex.com/g/bibtex-format/
.. _BibTeX field types: https://en.wikipedia.org/wiki/BibTeX#Field_types

Displays result fields from:

- :ref:`macro result_header`

Additional fields used in the :origin:`paper.html
<searx/templates/simple/result_templates/paper.html>`:

content :  :py:class:`str`
  An abstract or excerpt from the document.

comments : :py:class:`str`
  Free text display in italic below the content.

tags : :py:class:`List <list>`\ [\ :py:class:`str`\ ]
  Free tag list.

type : :py:class:`str`
  Short description of medium type, e.g. *book*, *pdf* or *html* ...

authors : :py:class:`List <list>`\ [\ :py:class:`str`\ ]
  List of authors of the work (authors with a "s" suffix, the "author" is in the
  :ref:`macro result_sub_header`).

editor : :py:class:`str`
  Editor of the book/paper.

publisher : :py:class:`str`
  Name of the publisher.

journal : :py:class:`str`
  Name of the journal or magazine the article was published in.

volume : :py:class:`str`
  Volume number.

pages : :py:class:`str`
  Page range where the article is.

number : :py:class:`str`
  Number of the report or the issue number for a journal article.

doi : :py:class:`str`
  DOI number (like ``10.1038/d41586-018-07848-2``).

issn : :py:class:`List <list>`\ [\ :py:class:`str`\ ]
  ISSN number like ``1476-4687``

isbn : :py:class:`List <list>`\ [\ :py:class:`str`\ ]
  ISBN number like ``9780201896831``

pdf_url : :py:class:`str`
  URL to the full article, the PDF version

html_url : :py:class:`str`
  URL to full article, HTML version


.. _template packages:

``packages``
------------

Displays result fields from:

- :ref:`macro result_header`

Additional fields used in the :origin:`packages.html
<searx/templates/simple/result_templates/packages.html>`:

package_name : :py:class:`str`
  The name of the package.

version : :py:class:`str`
  The current version of the package.

maintainer : :py:class:`str`
  The maintainer or author of the project.

publishedDate : :py:class:`datetime <datetime.datetime>`
  Date of latest update or release.

tags : :py:class:`List <list>`\ [\ :py:class:`str`\ ]
  Free tag list.

popularity : :py:class:`str`
  The popularity of the package, e.g. rating or download count.

license_name : :py:class:`str`
  The name of the license.

license_url : :py:class:`str`
  The web location of a license copy.

homepage : :py:class:`str`
  The url of the project's homepage.

source_code_url: :py:class:`str`
  The location of the project's source code.

links : :py:class:`dict`
  Additional links in the form of ``{'link_name': 'http://example.com'}``


.. _template products:

``products.html``
-----------------

Displays result fields from:

- :ref:`macro result_header` and
- :ref:`macro result_sub_header`

Additional fields used in the :origin:`products.html
<searx/templates/simple/result_templates/products.html>`:

content :  :py:class:`str`
  Description of the product.

price : :py:class:`str`
  The price must include the currency.

shipping : :py:class:`str`
  Shipping details.

source_country : :py:class:`str`
  Place from which the shipment is made.


.. _template answer results:

Answer results
==============

See :ref:`result_types.answer`

Suggestion results
==================

See :ref:`result_types.suggestion`

Correction results
==================

See :ref:`result_types.corrections`

Infobox results
===============

See :ref:`result_types.infobox`
