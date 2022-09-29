# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Engine related implementations

.. note::

   The long term goal is to modularize all relevant implementations to the
   engines here in this Python package.  In addition to improved modularization,
   this will also be necessary in part because the probability of circular
   imports will increase due to the increased typification of implementations in
   the future.

   ToDo:

   - move :py:obj:`searx.engines.load_engine` to a new module `searx.enginelib`.
"""


from __future__ import annotations
from typing import Union, Dict, List, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from searx.enginelib import traits


class Engine:  # pylint: disable=too-few-public-methods
    """Class of engine instances build from YAML settings.

    Further documentation see :ref:`general engine configuration`.

    .. hint::

       This class is currently never initialized and only used for type hinting.
    """

    # Common options in the engine module

    engine_type: str
    """Type of the engine (:origin:`searx/search/processors`)"""

    paging: bool
    """Engine supports multiple pages."""

    time_range_support: bool
    """Engine supports search time range."""

    safesearch: bool
    """Engine supports SafeSearch"""

    language_support: bool
    """Engine supports languages (locales) search."""

    language: str
    """For an engine, when there is ``language: ...`` in the YAML settings the engine
    does support only this one language:

    .. code:: yaml

      - name: google french
        engine: google
        language: fr
    """

    region: str
    """For an engine, when there is ``region: ...`` in the YAML settings the engine
    does support only this one region::

    .. code:: yaml

      - name: google belgium
        engine: google
        region: fr-BE
    """

    fetch_traits: Callable
    """Function to to fetch engine's traits from origin."""

    traits: traits.EngineTraits
    """Traits of the engine."""

    # settings.yml

    categories: List[str]
    """Tabs, in which the engine is working."""

    name: str
    """Name that will be used across SearXNG to define this engine.  In settings, on
    the result page .."""

    engine: str
    """Name of the python file used to handle requests and responses to and from
    this search engine (file name from :origin:`searx/engines` without
    ``.py``)."""

    enable_http: bool
    """Enable HTTP (by default only HTTPS is enabled)."""

    shortcut: str
    """Code used to execute bang requests (``!foo``)"""

    timeout: float
    """Specific timeout for search-engine."""

    display_error_messages: bool
    """Display error messages on the web UI."""

    proxies: dict
    """Set proxies for a specific engine (YAML):

    .. code:: yaml

       proxies :
         http:  socks5://proxy:port
         https: socks5://proxy:port
    """

    disabled: bool
    """To disable by default the engine, but not deleting it.  It will allow the
    user to manually activate it in the settings."""

    inactive: bool
    """Remove the engine from the settings (*disabled & removed*)."""

    about: dict
    """Additional fileds describing the engine.

    .. code:: yaml

       about:
          website: https://example.com
          wikidata_id: Q306656
          official_api_documentation: https://example.com/api-doc
          use_official_api: true
          require_api_key: true
          results: HTML
    """

    # deprecated properties

    _fetch_supported_languages: Callable  # deprecated use fetch_traits
    supported_languages: Union[List[str], Dict[str, str]]  # deprecated use traits
    language_aliases: Dict[str, str]  # deprecated not needed when using triats
    supported_languages_url: str  # deprecated not needed when using triats
