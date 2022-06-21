.. _engine results:
.. _searx.results:

==============
Engine Results
==============

.. automodule:: searx.results
  :members:

The result items are organized in the :py:obj:`container.ResultContainer` and
rendered in the :ref:`result template macros` and :ref:`result template files`.

.. contents:: Contents
   :depth: 2
   :local:
   :backlinks: entry

.. _standard result:

Result items
============

A result **item** is a python dictionary with dedicated keys and values.  In the
result list a **standard result type** is identified by the existence of the key
``url``.  Other **result types** are:

- :py:obj:`searx.results.suggestion`
- :py:obj:`searx.results.answer`
- :py:obj:`searx.results.correction`
- :py:obj:`searx.results.infobox`

The **standard result type**:

.. code:: python

   results.append({
       'template'      : str,

       # result_header

       'url'           : str,
       'title'         : str,
       'content'       : str,
       'img_src'       : str,
       'thumbnail'     : str,

       # result_sub_header

       'publishedDate' : datetime.datetime,
       'length'        : time.struct_time,
       'author'        : str,
       'metadata'      : str,
    })

template : ``str``
  :reF:`Media type <result media types>` of the result item.  Name of the
  :ref:`template file <result template files>` from :origin:`result_templates
  <searx/templates/simple/result_templates>`.  If unset, ``default.html`` is
  used.

.. hint::

   Each **standard result type** of an engine can be of different
   :reF:`media-types <result media types>`.


.. _result template macros:

Result template macros
======================

.. _macro result_header:

``result_header``
-----------------

Execpt ``image.html`` this macro is used in all :ref:`result template files`.
Fields used in the template :origin:`macro result_header
<searx/templates/simple/macros.html>`:

url :  ``str``
  Link URL of the result item.

title :  ``str``
  Link title of the result item.

img_src, thumbnail : ``str``
  URL of a image or thumbnail that is displayed in the result item.

.. _macro result_sub_header:

``result_sub_header``
---------------------

Execpt ``image.html`` this macro is used in all :ref:`result template files`.
Fields used in the template :origin:`macro result_sub_header
<searx/templates/simple/macros.html>`:

publishedDate : :py:obj:`datetime.datetime`
  The date on which the object was published.

length: :py:obj:`time.struct_time`
  Playing duration in seconds.

author : ``str``
  Author of the title.

metadata : ``str``
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

.. _result media types:
.. _result template files:

Result template files
=====================

The **media types** of the **standard result type** are the template files in
the :origin:`result_templates <searx/templates/simple/result_templates>`.

``default.html``
----------------

Displays result fields from:

- :ref:`macro result_header` and
- :ref:`macro result_sub_header`

Additional fields used in the :origin:`default.html
<searx/templates/simple/result_templates/default.html>`:

content :  ``str``
  General text of the result item.

iframe_src : ``str``
  URL of an embedded ``<iframe>`` / the frame is collapsible.

audio_src : uri,
  URL of an embedded ``<audio controls>``.


``code.html``
-------------

Displays result fields from:

- :ref:`macro result_header` and
- :ref:`macro result_sub_header`

Additional fields used in the :origin:`code.html
<searx/templates/simple/result_templates/code.html>`:

content :  ``str``
  Description of the code fragment.

codelines : ``[line1, line2, ...]``
  Lines of the code fragment.

code_language : ``str``
  Name of the code language, the value is passed to
  :py:obj:`pygments.lexers.get_lexer_by_name`.

repository : ``str``
  URL of the repository of the code fragment.


``images.html``
---------------

Fields used in the :origin:`images.html
<searx/templates/simple/result_templates/images.html>`:

title :  ``str``
  Title of the image.

thumbnail_src : ``str``
  URL of a preview of the image.

img_src : ``str``
  URL of the full size image.

Image labels
~~~~~~~~~~~~

content:  ``str``
  Description of the image.

author:  ``str``
  Name of the author of the image.

img_format : ``str``
  Format of the image.

source : ``str``
  Source of the image.

url :  ``str``
  URL of the page from where the images comes from (source).


``videos.html``
---------------

Displays result fields from:

- :ref:`macro result_header` and
- :ref:`macro result_sub_header`

Additional fields used in the :origin:`videos.html
<searx/templates/simple/result_templates/videos.html>`:

iframe_src : ``str``
  URL of an embedded ``<iframe>`` / the frame is collapsible.

content :  ``str``
  Description of the code fragment.


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

content :  ``str``
  Description of the item.

address_label : ``str``
  Label of the address / default ``_('address')``.

geojson : GeoJSON_
  Geometries mapped to HTMLElement.dataset_ (``data-map-geojson``) and used by
  Leaflet_.

boundingbox : ``[ min-lon, min-lat, max-lon, max-lat]``
  A bbox_ area defined by min longitude , min latitude , max longitude and max
  latitude.  The bounding box is mapped to HTMLElement.dataset_
  (``data-map-boundingbox``) and is used by Leaflet_.

longitude, latitude : ``str``
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

  country_code : ``str``
    `Country code`_ of the object.

  locality : ``str``
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

type : ``str``  # set by some engines but unused (oscar)
  Tag label from :ref:`OSM_KEYS_TAGS['tags'] <update_osm_keys_tags.py>`.

type_icon : ``str``  # set by some engines but unused (oscar)
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

  type : ``str``
    Type of osm-object (if OSM-Result).

  id :
    ID of osm-object (if OSM-Result).

  .. hint::

     The ``osm`` property is set by engine ``openstreetmap.py``, but it is not
     used in the ``map.html`` template yet.


``products.html``
-----------------

Displays result fields from:

- :ref:`macro result_header` and
- :ref:`macro result_sub_header`

Additional fields used in the :origin:`products.html
<searx/templates/simple/result_templates/products.html>`:

content :  ``str``
  Description of the product.

price : ``str``
  The price must include the currency.

shipping : ``str``
  Shipping details.

source_country : ``str``
  Place from which the shipment is made.


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


Suggestion results
==================

.. automodule:: searx.results.suggestion
  :members:


Answer results
==============

.. automodule:: searx.results.answer
  :members:


Correction results
==================

.. automodule:: searx.results.correction
  :members:


Infobox results
===============

.. automodule:: searx.results.infobox
  :members:


Result container
================

.. automodule:: searx.results.container
  :members:

results.core
============

.. automodule:: searx.results.core
  :members:

