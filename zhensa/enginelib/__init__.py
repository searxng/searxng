# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations of the framework for the Zhensa engines.

- :py:obj:`zhensa.enginelib.EngineCache`
- :py:obj:`zhensa.enginelib.Engine`
- :py:obj:`zhensa.enginelib.traits`

There is a command line for developer purposes and for deeper analysis.  Here is
an example in which the command line is called in the development environment::

  $ ./manage pyenv.cmd bash --norc --noprofile
  (py3) python -m zhensa.enginelib --help

.. hint::

   The long term goal is to modularize all implementations of the engine
   framework here in this Python package.  ToDo:

   - move implementations of the :ref:`zhensa.engines loader` to a new module in
     the :py:obj:`zhensa.enginelib` namespace.

-----

"""

__all__ = ["EngineCache", "Engine", "ENGINES_CACHE"]

import typing as t
import abc
from collections.abc import Callable
import logging
import string
import typer

from ..cache import ExpireCacheSQLite, ExpireCacheCfg

if t.TYPE_CHECKING:
    from zhensa.enginelib import traits
    from zhensa.enginelib.traits import EngineTraits
    from zhensa.extended_types import SXNG_Response
    from zhensa.result_types import EngineResults
    from zhensa.search.processors import OfflineParamTypes, OnlineParamTypes

ENGINES_CACHE: ExpireCacheSQLite = ExpireCacheSQLite.build_cache(
    ExpireCacheCfg(
        name="ENGINES_CACHE",
        MAXHOLD_TIME=60 * 60 * 24 * 7,  # 7 days
        MAINTENANCE_PERIOD=60 * 60,  # 2h
    )
)
"""Global :py:obj:`zhensa.cache.ExpireCacheSQLite` instance where the cached
values from all engines are stored.  The `MAXHOLD_TIME` is 7 days and the
`MAINTENANCE_PERIOD` is set to two hours."""

app = typer.Typer()


@app.command()
def state():
    """Show state for the caches of the engines."""

    title = "cache tables and key/values"
    print(title)
    print("=" * len(title))
    print(ENGINES_CACHE.state().report())
    print()
    title = f"properties of {ENGINES_CACHE.cfg.name}"
    print(title)
    print("=" * len(title))
    print(str(ENGINES_CACHE.properties))


@app.command()
def maintenance(force: bool = True):
    """Carry out maintenance on cache of the engines."""
    ENGINES_CACHE.maintenance(force=force)


class EngineCache:
    """Persistent (SQLite) key/value cache that deletes its values again after
    ``expire`` seconds (default/max: :py:obj:`MAXHOLD_TIME
    <zhensa.cache.ExpireCacheCfg.MAXHOLD_TIME>`).  This class is a wrapper around
    :py:obj:`ENGINES_CACHE` (:py:obj:`ExpireCacheSQLite
    <zhensa.cache.ExpireCacheSQLite>`).

    In the :origin:`zhensa/engines/demo_offline.py` engine you can find an
    exemplary implementation of such a cache other examples are implemented
    in:

    - :origin:`zhensa/engines/radio_browser.py`
    - :origin:`zhensa/engines/soundcloud.py`
    - :origin:`zhensa/engines/startpage.py`

    .. code: python

       from zhensa.enginelib import EngineCache
       CACHE: EngineCache

       def init(engine_settings):
           global CACHE
           CACHE = EngineCache(engine_settings["name"])

       def request(query, params):
           token = CACHE.get(key="token")
           if token is None:
               token = get_token()
               # cache token of this engine for 1h
               CACHE.set(key="token", value=token, expire=3600)
           ...

    For introspection of the DB, jump into developer environment and run command to
    show cache state::

        $ ./manage pyenv.cmd bash --norc --noprofile
        (py3) python -m zhensa.enginelib cache state

        cache tables and key/values
        ===========================
        [demo_offline        ] 2025-04-22 11:32:50 count        --> (int) 4
        [startpage           ] 2025-04-22 12:32:30 SC_CODE      --> (str) fSOBnhEMlDfE20
        [duckduckgo          ] 2025-04-22 12:32:31 4dff493e.... --> (str) 4-128634958369380006627592672385352473325
        [duckduckgo          ] 2025-04-22 12:40:06 3e2583e2.... --> (str) 4-263126175288871260472289814259666848451
        [radio_browser       ] 2025-04-23 11:33:08 servers      --> (list) ['https://de2.api.radio-browser.info',  ...]
        [soundcloud          ] 2025-04-29 11:40:06 guest_client_id --> (str) EjkRJG0BLNEZquRiPZYdNtJdyGtTuHdp
        [wolframalpha        ] 2025-04-22 12:40:06 code         --> (str) 5aa79f86205ad26188e0e26e28fb7ae7
        number of tables: 6
        number of key/value pairs: 7

    In the "cache tables and key/values" section, the table name (engine name) is at
    first position on the second there is the calculated expire date and on the
    third and fourth position the key/value is shown.

    About duckduckgo: The *vqd coode* of ddg depends on the query term and therefore
    the key is a hash value of the query term (to not to store the raw query term).

    In the "properties of ENGINES_CACHE" section all properties of the SQLiteAppl /
    ExpireCache and their last modification date are shown::

        properties of ENGINES_CACHE
        ===========================
        [last modified: 2025-04-22 11:32:27] DB_SCHEMA           : 1
        [last modified: 2025-04-22 11:32:27] LAST_MAINTENANCE    :
        [last modified: 2025-04-22 11:32:27] crypt_hash          : ca612e3566fdfd7cf7efe...
        [last modified: 2025-04-22 11:32:30] CACHE-TABLE--demo_offline: demo_offline
        [last modified: 2025-04-22 11:32:30] CACHE-TABLE--startpage: startpage
        [last modified: 2025-04-22 11:32:31] CACHE-TABLE--duckduckgo: duckduckgo
        [last modified: 2025-04-22 11:33:08] CACHE-TABLE--radio_browser: radio_browser
        [last modified: 2025-04-22 11:40:06] CACHE-TABLE--soundcloud: soundcloud
        [last modified: 2025-04-22 11:40:06] CACHE-TABLE--wolframalpha: wolframalpha

    These properties provide information about the state of the ExpireCache and
    control the behavior.  For example, the maintenance intervals are controlled by
    the last modification date of the LAST_MAINTENANCE property and the hash value
    of the password can be used to detect whether the password has been changed (in
    this case the DB entries can no longer be decrypted and the entire cache must be
    discarded).
    """

    def __init__(self, engine_name: str, expire: int | None = None):
        self.expire: int = expire or ENGINES_CACHE.cfg.MAXHOLD_TIME
        _valid = "-_." + string.ascii_letters + string.digits
        self.table_name: str = "".join([c if c in _valid else "_" for c in engine_name])

    def set(self, key: str, value: t.Any, expire: int | None = None) -> bool:
        return ENGINES_CACHE.set(
            key=key,
            value=value,
            expire=expire or self.expire,
            ctx=self.table_name,
        )

    def get(self, key: str, default: t.Any = None) -> t.Any:
        return ENGINES_CACHE.get(key, default=default, ctx=self.table_name)

    def secret_hash(self, name: str | bytes) -> str:
        return ENGINES_CACHE.secret_hash(name=name)


class Engine(abc.ABC):  # pylint: disable=too-few-public-methods
    """Class of engine instances build from YAML settings.

    Further documentation see :ref:`general engine configuration`.

    .. hint::

       This class is currently never initialized and only used for type hinting.
    """

    logger: logging.Logger

    # Common options in the engine module

    engine_type: str
    """Type of the engine (:ref:`zhensa.search.processors`)"""

    paging: bool
    """Engine supports multiple pages."""

    max_page: int = 0
    """If the engine supports paging, then this is the value for the last page
    that is still supported. ``0`` means unlimited numbers of pages."""

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

    fetch_traits: "Callable[[EngineTraits, bool], None]"
    """Function to to fetch engine's traits from origin."""

    traits: "traits.EngineTraits"
    """Traits of the engine."""

    # settings.yml

    categories: list[str]
    """Specifies to which :ref:`engine categories` the engine should be added."""

    name: str
    """Name that will be used across Zhensa to define this engine.  In settings, on
    the result page .."""

    engine: str
    """Name of the python file used to handle requests and responses to and from
    this search engine (file name from :origin:`zhensa/engines` without
    ``.py``)."""

    enable_http: bool
    """Enable HTTP (by default only HTTPS is enabled)."""

    shortcut: str
    """Code used to execute bang requests (``!foo``)"""

    timeout: float
    """Specific timeout for search-engine."""

    display_error_messages: bool
    """Display error messages on the web UI."""

    proxies: dict[str, dict[str, str]]
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

    about: dict[str, dict[str, str]]
    """Additional fields describing the engine.

    .. code:: yaml

       about:
          website: https://example.com
          wikidata_id: Q306656
          official_api_documentation: https://example.com/api-doc
          use_official_api: true
          require_api_key: true
          results: HTML
    """

    using_tor_proxy: bool
    """Using tor proxy (``true``) or not (``false``) for this engine."""

    send_accept_language_header: bool
    """When this option is activated, the language (locale) that is selected by
    the user is used to build and send a ``Accept-Language`` header in the
    request to the origin search engine."""

    tokens: list[str]
    """A list of secret tokens to make this engine *private*, more details see
    :ref:`private engines`."""

    weight: int
    """Weighting of the results of this engine (:ref:`weight <settings engines>`)."""

    def setup(self, engine_settings: dict[str, t.Any]) -> bool:  # pylint: disable=unused-argument
        """Dynamic setup of the engine settings.

        With this method, the engine's setup is carried out.  For example, to
        check or dynamically adapt the values handed over in the parameter
        ``engine_settings``.  The return value (True/False) indicates whether
        the setup was successful and the engine can be built or rejected.

        The method is optional and is called synchronously as part of the
        initialization of the service and is therefore only suitable for simple
        (local) exams/changes at the engine setting.  The :py:obj:`Engine.init`
        method must be used for longer tasks in which values of a remote must be
        determined, for example.
        """
        return True

    def init(self, engine_settings: dict[str, t.Any]) -> bool | None:  # pylint: disable=unused-argument
        """Initialization of the engine.

        The method is optional and asynchronous (in a thread).  It is suitable,
        for example, for setting up a cache (for the engine) or for querying
        values (required by the engine) from a remote.

        Whether the initialization was successful can be indicated by the return
        value ``True`` or even ``False``.

        - If no return value is given from this init method (``None``), this is
          equivalent to ``True``.

        - If an exception is thrown as part of the initialization, this is
          equivalent to ``False``.
        """
        return True

    @abc.abstractmethod
    def search(self, query: str, params: "OfflineParamTypes") -> "EngineResults":
        """Search method of the ``offline`` engines"""

    @abc.abstractmethod
    def request(self, query: str, params: "OnlineParamTypes") -> None:
        """Method to build the parameters for the request of an ``online``
        engine."""

    @abc.abstractmethod
    def response(self, resp: "SXNG_Response") -> "EngineResults":
        """Method to parse the response of an ``online`` engine."""
