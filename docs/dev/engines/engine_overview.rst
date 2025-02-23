.. _engines-dev:

===============
Engine Overview
===============

.. contents::
   :depth: 3
   :local:
   :backlinks: entry

.. _metasearch-engine: https://en.wikipedia.org/wiki/Metasearch_engine

.. sidebar:: Further reading ..

   - :ref:`configured engines`
   - :ref:`settings engines`

SearXNG is a metasearch-engine_, so it uses different search engines to provide
better results.

Because there is no general search API which could be used for every search
engine, an adapter has to be built between SearXNG and the external search
engines.  Adapters are stored under the folder :origin:`searx/engines`.

.. _general engine configuration:

General Engine Configuration
============================

It is required to tell SearXNG the type of results the engine provides. The
arguments can be set in the engine file or in the settings file (normally
``settings.yml``). The arguments in the settings file override the ones in the
engine file.

It does not matter if an option is stored in the engine file or in the settings.
However, the standard way is the following:

.. _engine file:

Engine File
-----------

.. table:: Common options in the engine module
   :width: 100%

   ======================= =========== ========================================================
   argument                type        information
   ======================= =========== ========================================================
   categories              list        categories, in which the engine is working
   paging                  boolean     support multiple pages
   time_range_support      boolean     support search time range
   engine_type             str         - ``online`` :ref:`[ref] <online engines>` by
                                         default, other possibles values are:
                                       - ``offline`` :ref:`[ref] <offline engines>`
                                       - ``online_dictionary`` :ref:`[ref] <online dictionary>`
                                       - ``online_currency`` :ref:`[ref] <online currency>`
                                       - ``online_url_search`` :ref:`[ref] <online url search>`
   ======================= =========== ========================================================

.. _engine settings:

Engine ``settings.yml``
-----------------------

For a more  detailed description, see :ref:`settings engines` in the :ref:`settings.yml`.

.. table:: Common options in the engine setup (``settings.yml``)
   :width: 100%

   ======================= =========== ==================================================
   argument                type        information
   ======================= =========== ==================================================
   name                    string      name of search-engine
   engine                  string      name of searxng-engine (file name without ``.py``)
   enable_http             bool        enable HTTP (by default only HTTPS is enabled).
   shortcut                string      shortcut of search-engine
   timeout                 string      specific timeout for search-engine
   display_error_messages  boolean     display error messages on the web UI
   proxies                 dict        set proxies for a specific engine
                                       (e.g. ``proxies : {http: socks5://proxy:port,
                                       https: socks5://proxy:port}``)
   ======================= =========== ==================================================

.. _engine overrides:

Overrides
---------

A few of the options have default values in the namespace of the engine's python
module, but are often overwritten by the settings.  If ``None`` is assigned to an
option in the engine file, it has to be redefined in the settings, otherwise
SearXNG will not start with that engine (global names with a leading underline can
be ``None``).

Here is an very simple example of the global names in the namespace of engine's
module:

.. code:: python

   # engine dependent config
   categories = ['general']
   paging = True
   _non_overwritten_global = 'foo'


.. table:: The naming of overrides is arbitrary / recommended overrides are:
   :width: 100%

   ======================= =========== ===========================================
   argument                type        information
   ======================= =========== ===========================================
   base_url                string      base-url, can be overwritten to use same
                                       engine on other URL
   number_of_results       int         maximum number of results per request
   language                string      ISO code of language and country like en_US
   api_key                 string      api-key if required by engine
   ======================= =========== ===========================================

.. _engine request:

Making a Request
================

To perform a search an URL have to be specified.  In addition to specifying an
URL, arguments can be passed to the query.

.. _engine request arguments:

Passed Arguments (request)
--------------------------

These arguments can be used to construct the search query.  Furthermore,
parameters with default value can be redefined for special purposes.

.. _engine request online:

.. table:: If the ``engine_type`` is :py:obj:`online
           <searx.search.processors.online.OnlineProcessor.get_params>`
   :width: 100%

   ====================== ============== ========================================================================
   argument               type           default-value, information
   ====================== ============== ========================================================================
   url                    str            ``''``
   method                 str            ``'GET'``
   headers                set            ``{}``
   data                   set            ``{}``
   cookies                set            ``{}``
   verify                 bool           ``True``
   headers.User-Agent     str            a random User-Agent
   category               str            current category, like ``'general'``
   safesearch             int            ``0``, between ``0`` and ``2`` (normal, moderate, strict)
   time_range             Optional[str]  ``None``, can be ``day``, ``week``, ``month``, ``year``
   pageno                 int            current pagenumber
   searxng_locale         str            SearXNG's locale selected by user.  Specific language code like
                                         ``'en'``, ``'en-US'``, or ``'all'`` if unspecified.
   ====================== ============== ========================================================================


.. _engine request online_dictionary:

.. table:: If the ``engine_type`` is :py:obj:`online_dictionary
           <searx.search.processors.online_dictionary.OnlineDictionaryProcessor.get_params>`,
           in addition to the :ref:`online <engine request online>` arguments:
   :width: 100%

   ====================== ============== ========================================================================
   argument               type           default-value, information
   ====================== ============== ========================================================================
   from_lang              str            specific language code like ``'en_US'``
   to_lang                str            specific language code like ``'en_US'``
   query                  str            the text query without the languages
   ====================== ============== ========================================================================

.. _engine request online_currency:

.. table:: If the ``engine_type`` is :py:obj:`online_currency
           <searx.search.processors.online_currency.OnlineCurrencyProcessor.get_params>`,
           in addition to the :ref:`online <engine request online>` arguments:
   :width: 100%

   ====================== ============== ========================================================================
   argument               type           default-value, information
   ====================== ============== ========================================================================
   amount                 float          the amount to convert
   from                   str            ISO 4217 code
   to                     str            ISO 4217 code
   from_name              str            currency name
   to_name                str            currency name
   ====================== ============== ========================================================================

.. _engine request online_url_search:

.. table:: If the ``engine_type`` is :py:obj:`online_url_search
           <searx.search.processors.online_url_search.OnlineUrlSearchProcessor.get_params>`,
           in addition to the :ref:`online <engine request online>` arguments:
   :width: 100%

   ====================== ============== ========================================================================
   argument               type           default-value, information
   ====================== ============== ========================================================================
   search_url             dict           URLs from the search query:

                                         .. code:: python

                                            {
                                              'http': str,
                                              'ftp': str,
                                              'data:image': str
                                            }
   ====================== ============== ========================================================================

Specify Request
---------------

The function :py:func:`def request(query, params):
<searx.engines.demo_online.request>` always returns the ``params`` variable, the
following parameters can be used to specify a search request:

.. table::
   :width: 100%

   =================== =========== ==========================================================================
   argument            type        information
   =================== =========== ==========================================================================
   url                 str         requested url
   method              str         HTTP request method
   headers             set         HTTP header information
   data                set         HTTP data information
   cookies             set         HTTP cookies
   verify              bool        Performing SSL-Validity check
   allow_redirects     bool        Follow redirects
   max_redirects       int         maximum redirects, hard limit
   soft_max_redirects  int         maximum redirects, soft limit. Record an error but don't stop the engine
   raise_for_httperror bool        True by default: raise an exception if the HTTP code of response is >= 300
   =================== =========== ==========================================================================


Making a Response
=================

In the ``response`` function of the engine, the HTTP response (``resp``) is
parsed and a list of results is returned.

A engine can append result-items of different media-types and different
result-types to the result list.  The list of the result items is render to HTML
by templates.  For more details read section:

- :ref:`simple theme templates`
- :ref:`result types`



