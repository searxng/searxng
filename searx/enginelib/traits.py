# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine's traits are fetched from the origin engines and stored in a JSON file
in the *data folder*.  Most often traits are languages and region codes and
their mapping from SearXNG's representation to the representation in the origin
search engine.  For new traits new properties can be added to the class
:py:class:`EngineTraits`.

To load traits from the persistence :py:obj:`EngineTraitsMap.from_data` can be
used.
"""


import os
import json
import dataclasses
import types
import typing as t
import pathlib
from searx import locales
from searx.data import data_dir, ENGINE_TRAITS

if t.TYPE_CHECKING:
    from . import Engine


class EngineTraitsEncoder(json.JSONEncoder):
    """Encodes :class:`EngineTraits` to a serializable object, see
    :class:`json.JSONEncoder`."""

    def default(self, o: t.Any) -> t.Any:
        """Return dictionary of a :class:`EngineTraits` object."""
        if isinstance(o, EngineTraits):
            return o.__dict__
        return super().default(o)


@dataclasses.dataclass
class EngineTraits:
    """The class is intended to be instantiated for each engine."""

    regions: dict[str, str] = dataclasses.field(default_factory=dict)
    """Maps SearXNG's internal representation of a region to the one of the engine.

    SearXNG's internal representation can be parsed by babel and the value is
    send to the engine:

    .. code:: python

       regions ={
           'fr-BE' : <engine's region name>,
       }

       for key, egnine_region regions.items():
          searxng_region = babel.Locale.parse(key, sep='-')
          ...
    """

    languages: dict[str, str] = dataclasses.field(default_factory=dict)
    """Maps SearXNG's internal representation of a language to the one of the engine.

    SearXNG's internal representation can be parsed by babel and the value is
    send to the engine:

    .. code:: python

       languages = {
           'ca' : <engine's language name>,
       }

       for key, egnine_lang in languages.items():
          searxng_lang = babel.Locale.parse(key)
          ...
    """

    all_locale: str | None = None
    """To which locale value SearXNG's ``all`` language is mapped (shown a "Default
    language").
    """

    data_type: t.Literal['traits_v1'] = 'traits_v1'
    """Data type, default is 'traits_v1'.
    """

    custom: dict[str, t.Any] = dataclasses.field(default_factory=dict)
    """A place to store engine's custom traits, not related to the SearXNG core.
    """

    def get_language(self, searxng_locale: str, default: str | None = None) -> str | None:
        """Return engine's language string that *best fits* to SearXNG's locale.

        :param searxng_locale: SearXNG's internal representation of locale
          selected by the user.

        :param default: engine's default language

        The *best fits* rules are implemented in
        :py:obj:`searx.locales.get_engine_locale`.  Except for the special value ``all``
        which is determined from :py:obj:`EngineTraits.all_locale`.
        """
        if searxng_locale == 'all' and self.all_locale is not None:
            return self.all_locale
        return locales.get_engine_locale(searxng_locale, self.languages, default=default)

    def get_region(self, searxng_locale: str, default: str | None = None) -> str | None:
        """Return engine's region string that best fits to SearXNG's locale.

        :param searxng_locale: SearXNG's internal representation of locale
          selected by the user.

        :param default: engine's default region

        The *best fits* rules are implemented in
        :py:obj:`searx.locales.get_engine_locale`.  Except for the special value ``all``
        which is determined from :py:obj:`EngineTraits.all_locale`.
        """
        if searxng_locale == 'all' and self.all_locale is not None:
            return self.all_locale
        return locales.get_engine_locale(searxng_locale, self.regions, default=default)

    def is_locale_supported(self, searxng_locale: str) -> bool:
        """A *locale* (SearXNG's internal representation) is considered to be
        supported by the engine if the *region* or the *language* is supported
        by the engine.

        For verification the functions :py:func:`EngineTraits.get_region` and
        :py:func:`EngineTraits.get_language` are used.
        """
        if self.data_type == 'traits_v1':
            return bool(self.get_region(searxng_locale) or self.get_language(searxng_locale))

        raise TypeError('engine traits of type %s is unknown' % self.data_type)

    def copy(self):
        """Create a copy of the dataclass object."""
        return EngineTraits(**dataclasses.asdict(self))

    @classmethod
    def fetch_traits(cls, engine: "Engine | types.ModuleType") -> "EngineTraits | None":
        """Call a function ``fetch_traits(engine_traits)`` from engines namespace to fetch
        and set properties from the origin engine in the object ``engine_traits``.  If
        function does not exists, ``None`` is returned.
        """

        fetch_traits = getattr(engine, 'fetch_traits', None)
        engine_traits = None

        if fetch_traits:
            engine_traits = cls()
            fetch_traits(engine_traits)
        return engine_traits

    def set_traits(self, engine: "Engine | types.ModuleType") -> None:
        """Set traits from self object in a :py:obj:`.Engine` namespace.

        :param engine: engine instance build by :py:func:`searx.engines.load_engine`
        """

        if self.data_type == 'traits_v1':
            self._set_traits_v1(engine)
        else:
            raise TypeError('engine traits of type %s is unknown' % self.data_type)

    def _set_traits_v1(self, engine: "Engine | types.ModuleType") -> None:
        # For an engine, when there is `language: ...` in the YAML settings the engine
        # does support only this one language (region)::
        #
        #   - name: google italian
        #     engine: google
        #     language: it
        #     region: it-IT

        traits = self.copy()

        _msg = "settings.yml - engine: '%s' / %s: '%s' not supported"

        languages = traits.languages
        if hasattr(engine, 'language'):
            if engine.language not in languages:
                raise ValueError(_msg % (engine.name, 'language', engine.language))
            traits.languages = {engine.language: languages[engine.language]}

        regions = traits.regions
        if hasattr(engine, 'region'):
            if engine.region not in regions:
                raise ValueError(_msg % (engine.name, 'region', engine.region))
            traits.regions = {engine.region: regions[engine.region]}

        engine.language_support = bool(traits.languages or traits.regions)

        # set the copied & modified traits in engine's namespace
        engine.traits = traits  # pyright: ignore[reportAttributeAccessIssue]


class EngineTraitsMap(dict[str, EngineTraits]):
    """A python dictionary to map :class:`EngineTraits` by engine name."""

    ENGINE_TRAITS_FILE: pathlib.Path = (data_dir / 'engine_traits.json').resolve()
    """File with persistence of the :py:obj:`EngineTraitsMap`."""

    def save_data(self):
        """Store EngineTraitsMap in in file :py:obj:`self.ENGINE_TRAITS_FILE`"""
        with open(self.ENGINE_TRAITS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self, f, indent=2, sort_keys=True, cls=EngineTraitsEncoder)

    @classmethod
    def from_data(cls) -> 'EngineTraitsMap':
        """Instantiate :class:`EngineTraitsMap` object from :py:obj:`ENGINE_TRAITS`"""
        obj = cls()
        for k, v in ENGINE_TRAITS.items():
            obj[k] = EngineTraits(**v)
        return obj

    @classmethod
    def fetch_traits(cls, log: t.Callable[[str], None]) -> 'EngineTraitsMap':
        from searx import engines  # pylint: disable=cyclic-import, import-outside-toplevel

        names = list(engines.engines)
        names.sort()
        obj = cls()

        for engine_name in names:
            engine: Engine | types.ModuleType = engines.engines[engine_name]
            traits = None

            # pylint: disable=broad-exception-caught
            try:
                traits = EngineTraits.fetch_traits(engine)
            except Exception as exc:
                log("FATAL: while fetch_traits %s: %s" % (engine_name, exc))
                if os.environ.get('FORCE', '').lower() not in ['on', 'true', '1']:
                    raise
                v = ENGINE_TRAITS.get(engine_name)
                if v:
                    log("FORCE: re-use old values from fetch_traits - ENGINE_TRAITS[%s]" % engine_name)
                    traits = EngineTraits(**v)

            if traits is not None:
                log("%-20s: SearXNG languages --> %s " % (engine_name, len(traits.languages)))
                log("%-20s: SearXNG regions   --> %s" % (engine_name, len(traits.regions)))
                obj[engine_name] = traits

        return obj

    def set_traits(self, engine: "Engine | types.ModuleType"):
        """Set traits in a :py:obj:`Engine` namespace.

        :param engine: engine instance build by :py:func:`searx.engines.load_engine`
        """

        engine_traits = EngineTraits(data_type='traits_v1')
        if engine.name in self.keys():
            engine_traits = self[engine.name]

        elif engine.engine in self.keys():
            # The key of the dictionary traits_map is the *engine name*
            # configured in settings.xml.  When multiple engines are configured
            # in settings.yml to use the same origin engine (python module)
            # these additional engines can use the languages from the origin
            # engine.  For this use the configured ``engine: ...`` from
            # settings.yml
            engine_traits = self[engine.engine]

        engine_traits.set_traits(engine)
