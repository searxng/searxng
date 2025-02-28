# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=too-few-public-methods,missing-module-docstring

from __future__ import annotations

__all__ = ["PluginInfo", "Plugin", "PluginStorage"]

import abc
import importlib
import logging
import pathlib
import types
import typing
import warnings

from dataclasses import dataclass, field

import flask

import searx
from searx.utils import load_module
from searx.extended_types import SXNG_Request
from searx.result_types import Result


if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins


_default = pathlib.Path(__file__).parent
log: logging.Logger = logging.getLogger("searx.plugins")


@dataclass
class PluginInfo:
    """Object that holds informations about a *plugin*, these infos are shown to
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

    preference_section: typing.Literal["general", "ui", "privacy", "query"] | None = "general"
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


class Plugin(abc.ABC):
    """Abstract base class of all Plugins."""

    id: str = ""
    """The ID (suffix) in the HTML form."""

    default_on: bool = False
    """Plugin is enabled/disabled by default."""

    keywords: list[str] = []
    """Keywords in the search query that activate the plugin.  The *keyword* is
    the first word in a search query.  If a plugin should be executed regardless
    of the search query, the list of keywords should be empty (which is also the
    default in the base class for Plugins)."""

    log: logging.Logger
    """A logger object, is automatically initialized when calling the
    constructor (if not already set in the subclass)."""

    info: PluginInfo
    """Informations about the *plugin*, see :py:obj:`PluginInfo`."""

    fqn: str = ""

    def __init__(self) -> None:
        super().__init__()
        if not self.fqn:
            self.fqn = self.__class__.__mro__[0].__module__

        for attr in ["id", "default_on"]:
            if getattr(self, attr, None) is None:
                raise NotImplementedError(f"plugin {self} is missing attribute {attr}")

        if not self.id:
            self.id = f"{self.__class__.__module__}.{self.__class__.__name__}"
        if not getattr(self, "log", None):
            self.log = log.getChild(self.id)

    def __hash__(self) -> int:
        """The hash value is used in :py:obj:`set`, for example, when an object
        is added to the set.  The hash value is also used in other contexts,
        e.g. when checking for equality to identify identical plugins from
        different sources (name collisions)."""

        return id(self)

    def __eq__(self, other):
        """py:obj:`Plugin` objects are equal if the hash values of the two
        objects are equal."""

        return hash(self) == hash(other)

    def init(self, app: flask.Flask) -> bool:  # pylint: disable=unused-argument
        """Initialization of the plugin, the return value decides whether this
        plugin is active or not.  Initialization only takes place once, at the
        time the WEB application is set up.  The base methode always returns
        ``True``, the methode can be overwritten in the inheritances,

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

    def on_result(self, request: SXNG_Request, search: "SearchWithPlugins", result: Result) -> bool:
        """Runs for each result of each engine and returns a boolean:

        - ``True`` to keep the result
        - ``False`` to remove the result from the result list

        The ``result`` can be modified to the needs.

        .. hint::

           If :py:obj:`Result.url` is modified, :py:obj:`Result.parsed_url` must
           be changed accordingly:

           .. code:: python

              result["parsed_url"] = urlparse(result["url"])
        """
        return True

    def post_search(self, request: SXNG_Request, search: "SearchWithPlugins") -> None | typing.Sequence[Result]:
        """Runs AFTER the search request.  Can return a list of :py:obj:`Result`
        objects to be added to the final result list."""
        return


class ModulePlugin(Plugin):
    """A wrapper class for legacy *plugins*.

    .. note::

       For internal use only!

    In a module plugin, the follwing names are mapped:

    - `module.query_keywords` --> :py:obj:`Plugin.keywords`
    - `module.plugin_id` --> :py:obj:`Plugin.id`
    - `module.logger` --> :py:obj:`Plugin.log`
    """

    _required_attrs = (("name", str), ("description", str), ("default_on", bool))

    def __init__(self, mod: types.ModuleType, fqn: str):
        """In case of missing attributes in the module or wrong types are given,
        a :py:obj:`TypeError` exception is raised."""

        self.fqn = fqn
        self.module = mod
        self.id = getattr(self.module, "plugin_id", self.module.__name__)
        self.log = logging.getLogger(self.module.__name__)
        self.keywords = getattr(self.module, "query_keywords", [])

        for attr, attr_type in self._required_attrs:
            if not hasattr(self.module, attr):
                msg = f"missing attribute {attr}, cannot load plugin"
                self.log.critical(msg)
                raise TypeError(msg)
            if not isinstance(getattr(self.module, attr), attr_type):
                msg = f"attribute {attr} is not of type {attr_type}"
                self.log.critical(msg)
                raise TypeError(msg)

        self.default_on = mod.default_on
        self.info = PluginInfo(
            id=self.id,
            name=self.module.name,
            description=self.module.description,
            preference_section=getattr(self.module, "preference_section", None),
            examples=getattr(self.module, "query_examples", []),
            keywords=self.keywords,
        )

        # monkeypatch module
        self.module.logger = self.log  # type: ignore

        super().__init__()

    def init(self, app: flask.Flask) -> bool:
        if not hasattr(self.module, "init"):
            return True
        return self.module.init(app)

    def pre_search(self, request: SXNG_Request, search: "SearchWithPlugins") -> bool:
        if not hasattr(self.module, "pre_search"):
            return True
        return self.module.pre_search(request, search)

    def on_result(self, request: SXNG_Request, search: "SearchWithPlugins", result: Result) -> bool:
        if not hasattr(self.module, "on_result"):
            return True
        return self.module.on_result(request, search, result)

    def post_search(self, request: SXNG_Request, search: "SearchWithPlugins") -> None | list[Result]:
        if not hasattr(self.module, "post_search"):
            return None
        return self.module.post_search(request, search)


class PluginStorage:
    """A storage for managing the *plugins* of SearXNG."""

    plugin_list: set[Plugin]
    """The list of :py:obj:`Plugins` in this storage."""

    legacy_plugins = [
        "ahmia_filter",
        "calculator",
        "hostnames",
        "oa_doi_rewrite",
        "tor_check",
        "tracker_url_remover",
        "unit_converter",
    ]
    """Internal plugins implemented in the legacy style (as module / deprecated!)."""

    def __init__(self):
        self.plugin_list = set()

    def __iter__(self):

        yield from self.plugin_list

    def __len__(self):
        return len(self.plugin_list)

    @property
    def info(self) -> list[PluginInfo]:
        return [p.info for p in self.plugin_list]

    def load_builtins(self):
        """Load plugin modules from:

        - the python packages in :origin:`searx/plugins` and
        - the external plugins from :ref:`settings plugins`.
        """

        for f in _default.iterdir():

            if f.name.startswith("_"):
                continue

            if f.stem not in self.legacy_plugins:
                self.register_by_fqn(f"searx.plugins.{f.stem}.SXNGPlugin")
                continue

            # for backward compatibility
            mod = load_module(f.name, str(f.parent))
            self.register(ModulePlugin(mod, f"searx.plugins.{f.stem}"))

        for fqn in searx.get_setting("plugins"):  # type: ignore
            self.register_by_fqn(fqn)

    def register(self, plugin: Plugin):
        """Register a :py:obj:`Plugin`.  In case of name collision (if two
        plugins have same ID) a :py:obj:`KeyError` exception is raised.
        """

        if plugin in self.plugin_list:
            msg = f"name collision '{plugin.id}'"
            plugin.log.critical(msg)
            raise KeyError(msg)

        if not plugin.fqn.startswith("searx.plugins."):
            self.plugin_list.add(plugin)
            plugin.log.debug("plugin has been registered")
            return

        # backward compatibility for the enabled_plugins setting
        # https://docs.searxng.org/admin/settings/settings_plugins.html#enabled-plugins-internal
        en_plgs: list[str] | None = searx.get_setting("enabled_plugins")  # type:ignore

        if en_plgs is None:
            # enabled_plugins not listed in the /etc/searxng/settings.yml:
            # check default_on before register ..
            if plugin.default_on:
                self.plugin_list.add(plugin)
                plugin.log.debug("builtin plugin has been registered by SearXNG's defaults")
                return
            plugin.log.debug("builtin plugin is not registered by SearXNG's defaults")
            return

        if plugin.info.name not in en_plgs:
            # enabled_plugins listed in the /etc/searxng/settings.yml,
            # but this plugin is not listed in:
            plugin.log.debug("builtin plugin is not registered by maintainer's settings")
            return

        # if the plugin is in enabled_plugins, then it is on by default.
        plugin.default_on = True
        self.plugin_list.add(plugin)
        plugin.log.debug("builtin plugin is registered by maintainer's settings")

    def register_by_fqn(self, fqn: str):
        """Register a :py:obj:`Plugin` via its fully qualified class name (FQN).
        The FQNs of external plugins could be read from a configuration, for
        example, and registered using this method
        """

        mod_name, _, obj_name = fqn.rpartition('.')
        if not mod_name:
            # for backward compatibility
            code_obj = importlib.import_module(fqn)
        else:
            mod = importlib.import_module(mod_name)
            code_obj = getattr(mod, obj_name, None)

        if code_obj is None:
            msg = f"plugin {fqn} is not implemented"
            log.critical(msg)
            raise ValueError(msg)

        if isinstance(code_obj, types.ModuleType):
            # for backward compatibility
            warnings.warn(
                f"plugin {fqn} is implemented in a legacy module / migrate to searx.plugins.Plugin", DeprecationWarning
            )

            self.register(ModulePlugin(code_obj, fqn))
            return

        self.register(code_obj())

    def init(self, app: flask.Flask) -> None:
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

    def on_result(self, request: SXNG_Request, search: "SearchWithPlugins", result: Result) -> bool:

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
