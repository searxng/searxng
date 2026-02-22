.. _google engines:

==============
Google Engines
==============

.. contents::
   :depth: 2
   :local:
   :backlinks: entry


.. _google API:

Google API
==========

.. _Query Parameter Definitions:
   https://developers.google.com/custom-search/docs/xml_results#WebSearch_Query_Parameter_Definitions

SearXNG's implementation of the Google API is mainly done in
:py:obj:`get_google_info <searx.engines.google.get_google_info>`.

For detailed description of the *REST-full* API see: `Query Parameter
Definitions`_.  The linked API documentation can sometimes be helpful during
reverse engineering.  However, we cannot use it in the freely accessible WEB
services; not all parameters can be applied and some engines are more *special*
than other (e.g. :ref:`google news engine`).


.. _google web engine:

Google WEB
==========

.. automodule:: searx.engines.google
  :members:

.. _google autocomplete:

Google Autocomplete
====================

.. autofunction:: searx.autocomplete.google_complete

.. _google images engine:

Google Images
=============

.. automodule:: searx.engines.google_images
  :members:

.. _google videos engine:

Google Videos
=============

.. automodule:: searx.engines.google_videos
  :members:

.. _google news engine:

Google News
===========

.. automodule:: searx.engines.google_news
  :members:

.. _google scholar engine:

Google Scholar
==============

.. automodule:: searx.engines.google_scholar
  :members:
