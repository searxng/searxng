# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=too-few-public-methods,missing-module-docstring

__all__ = ["PluginInfo", "Plugin", "PluginCfg", "PluginStorage"]

import abc
import importlib
import inspect
import logging
import re

import typing as t
from collections.abc import Generator

from dataclasses import dataclass, field

from searx.extended_types import SXNG_Request

if t.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.result_types import Result, EngineResults, LegacyResult  # pyright: ignore[reportPrivateLocalImportUsage]
    import flask

log: logging.Logger = logging.getLogger("searx.plugins")


@dataclass
class PluginInfo:
    """Object that holds information about a *plugin*, these infos are shown to
    the user in the Preferences menu.

    To be able to translate the information into other languages, the text must
    be written in English and translated with :py:obj:`flask_babel.gettext`.
    """

    id: str
    """The ID-selector in HTML/CSS `#<id>`."""

    name: str
    """Name of the *plugin*."""

    description: str
    """Short description of the *answerer*."""

    preference_section: t.Literal["general", "ui", "privacy", "query"] | None = "general"
    """Section (tab/group) in the preferences where this plugin is shown to the
    user.

    The value ``query`` is reserved for plugins that are activated via a
    *keyword* as part of a search query, see:

    - :py:obj:`PluginInfo.examples`
    - :py:obj:`Plugin.keywords`

    Those plugins are shown in the preferences in tab *Special Queries*.
    """

    examples: list[str] = field(default_factory=list)
    """List of short examples of the usage / of query terms."""

    keywords: list[str] = field(default_factory=list)
    """See :py:obj:`Plugin.keywords`"""


ID_REGXP = re.compile("[a-z][a-z0-9].*")


class Plugin(abc.ABC):
    """Abstract base class of all Plugins."""

    id: str = ""
    """The ID (suffix) in the HTML form."""

    active: t.ClassVar[bool]
    """Plugin is enabled/disabled by default (:py:obj:`PluginCfg.active`)."""

    keywords: list[str] = []
    """Keywords in the search query that activate the plugin.  The *keyword* is
    the first word in a search query.  If a plugin should be executed regardless
    of the search query, the list of keywords should be empty (which is also the
    default in the base class for Plugins)."""

    log: logging.Logger
    """A logger object, is automatically initialized when calling the
    constructor (if not already set in the subclass)."""

    info: PluginInfo
    """Information about the *plugin*, see :py:obj:`PluginInfo`."""

    fqn: str = ""

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__()
        if not self.fqn:
            self.fqn = self.__class__.__mro__[0].__module__

        # names from the configuration
        for n, v in plg_cfg.__dict__.items():
            setattr(self, n, v)

        # names that must be set by the plugin implementation
        for attr in [
            "id",
        ]:
            if getattr(self, attr, None) is None:
                raise NotImplementedError(f"plugin {self} is missing attribute {attr}")

        if not ID_REGXP.match(self.id):
            raise ValueError(f"plugin ID {self.id} contains invalid character (use lowercase ASCII)")

        if not getattr(self, "log", None):
            pkg_name = inspect.getmodule(self.__class__).__package__  # pyright: ignore[reportOptionalMemberAccess]
            self.log = logging.getLogger(f"{pkg_name}.{self.id}")

    def __hash__(self) -> int:
        """The hash value is used in :py:obj:`set`, for example, when an object
        is added to the set.  The hash value is also used in other contexts,
        e.g. when checking for equality to identify identical plugins from
        different sources (name collisions)."""

        return id(self)

    def __eq__(self, other: t.Any):
        """py:obj:`Plugin` objects are equal if the hash values of the two
        objects are equal."""

        return hash(self) == hash(other)

    def init(self, app: "flask.Flask") -> bool:  # pylint: disable=unused-argument
        """Initialization of the plugin, the return value decides whether this
        plugin is active or not.  Initialization only takes place once, at the
        time the WEB application is set up.  The base method always returns
        ``True``, the method can be overwritten in the inheritances,

        - ``True`` plugin is active
        - ``False`` plugin is inactive
        """
        return True

    # pylint: disable=unused-argument
    def pre_search(self, request: SXNG_Request, search: "SearchWithPlugins") -> bool:
        """Runs BEFORE the search request and returns a boolean:

        - ``True`` to continue the search
        - ``False`` to stop the search
        """
        return True

    def on_result(self, request: SXNG_Request, search: "SearchWithPlugins", result: "Result") -> bool:
        """Runs for each result of each engine and returns a boolean:

        - ``True`` to keep the result
        - ``False`` to remove the result from the result list

        The ``result`` can be modified to the needs.

        .. hint::

           If :py:obj:`Result.url <searx.result_types._base.Result.url>` is modified,
           :py:obj:`Result.parsed_url <searx.result_types._base.Result.parsed_url>` must
           be changed accordingly:

           .. code:: python

              result["parsed_url"] = urlparse(result["url"])
        """
        return True

    def post_search(
        self, request: SXNG_Request, search: "SearchWithPlugins"
    ) -> "None | list[Result | LegacyResult] | EngineResults":
        """Runs AFTER the search request.  Can return a list of
        :py:obj:`Result <searx.result_types._base.Result>` objects to be added to the
        final result list."""
        return


@dataclass
class PluginCfg:
    """Settings of a plugin.

    .. code:: yaml

       mypackage.mymodule.MyPlugin:
         active: true
    """

    active: bool = False
    """Plugin is active by default and the user can *opt-out* in the preferences."""

    parameters: dict[str, t.Any] = field(default_factory=dict)
    """Arbitrary plugin parameters from settings.yml (plugin-specific)."""


class PluginStorage:
    """A storage for managing the *plugins* of SearXNG."""

    plugin_list: set[Plugin]
    """The list of :py:obj:`Plugins` in this storage."""

    def __init__(self):
        self.plugin_list = set()

    def __iter__(self) -> Generator[Plugin]:
        yield from self.plugin_list

    def __len__(self):
        return len(self.plugin_list)

    @property
    def info(self) -> list[PluginInfo]:

        return [p.info for p in self.plugin_list]

    def load_settings(self, cfg: dict[str, dict[str, t.Any]]):
        """Load plugins configured in SearXNG's settings :ref:`settings
        plugins`."""

        for fqn, plg_settings in cfg.items():
            cls = None
            mod_name, cls_name = fqn.rsplit('.', 1)
            try:
                mod = importlib.import_module(mod_name)
                cls = getattr(mod, cls_name, None)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                log.exception(exc)

            if cls is None:
                msg = f"plugin {fqn} is not implemented"
                raise ValueError(msg)
            plg = cls(PluginCfg(**plg_settings))
            self.register(plg)

    def register(self, plugin: Plugin):
        """Register a :py:obj:`Plugin`.  In case of name collision (if two
        plugins have same ID) a :py:obj:`KeyError` exception is raised.
        """

        if plugin in [p.id for p in self.plugin_list]:
            msg = f"name collision '{plugin.id}'"
            plugin.log.critical(msg)
            raise KeyError(msg)

        self.plugin_list.add(plugin)
        plugin.log.debug("plugin has been loaded")

    def init(self, app: "flask.Flask") -> None:
        """Calls the method :py:obj:`Plugin.init` of each plugin in this
        storage.  Depending on its return value, the plugin is removed from
        *this* storage or not."""

        for plg in self.plugin_list.copy():
            if not plg.init(app):
                self.plugin_list.remove(plg)

    def pre_search(self, request: SXNG_Request, search: "SearchWithPlugins") -> bool:

        ret = True
        for plugin in [p for p in self.plugin_list if p.id in search.user_plugins]:
            try:
                ret = bool(plugin.pre_search(request=request, search=search))
            except Exception:  # pylint: disable=broad-except
                plugin.log.exception("Exception while calling pre_search")
                continue
            if not ret:
                # skip this search on the first False from a plugin
                break
        return ret

    def on_result(self, request: SXNG_Request, search: "SearchWithPlugins", result: "Result") -> bool:

        ret = True
        for plugin in [p for p in self.plugin_list if p.id in search.user_plugins]:
            try:
                ret = bool(plugin.on_result(request=request, search=search, result=result))
            except Exception:  # pylint: disable=broad-except
                plugin.log.exception("Exception while calling on_result")
                continue
            if not ret:
                # ignore this result item on the first False from a plugin
                break

        return ret

    def post_search(self, request: SXNG_Request, search: "SearchWithPlugins") -> None:
        """Extend :py:obj:`search.result_container
        <searx.results.ResultContainer`> with result items from plugins listed
        in :py:obj:`search.user_plugins <SearchWithPlugins.user_plugins>`.
        """

        keyword = None
        for keyword in search.search_query.query.split():
            if keyword:
                break

        for plugin in [p for p in self.plugin_list if p.id in search.user_plugins]:

            if plugin.keywords:
                # plugin with keywords: skip plugin if no keyword match
                if keyword and keyword not in plugin.keywords:
                    continue
            try:
                results = plugin.post_search(request=request, search=search) or []
            except Exception:  # pylint: disable=broad-except
                plugin.log.exception("Exception while calling post_search")
                continue

            # In case of *plugins* prefix ``plugin:`` is set, see searx.result_types.Result
            search.result_container.extend(f"plugin: {plugin.id}", results)
