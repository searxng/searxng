# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Engine's traits are fetched from the origin engines and stored in a JSON file
in the *data folder*.  Most often traits are languages and region codes and
their mapping from SearXNG's representation to the representation in the origin
search engine.  For new traits new properties can be added to the class
:py:class:`EngineTraits`.

To load traits from the persistence :py:obj:`EngineTraitsMap.from_data` can be
used.
"""

from __future__ import annotations
import json
import dataclasses
from typing import Dict, Union, List, Callable, Optional, TYPE_CHECKING
from typing_extensions import Literal, Self

from babel.localedata import locale_identifiers

from searx import locales
from searx.data import data_dir, ENGINE_TRAITS

if TYPE_CHECKING:
    from . import Engine


class EngineTraitsEncoder(json.JSONEncoder):
    """Encodes :class:`EngineTraits` to a serializable object, see
    :class:`json.JSONEncoder`."""

    def default(self, o):
        """Return dictionary of a :class:`EngineTraits` object."""
        if isinstance(o, EngineTraits):
            return o.__dict__
        return super().default(o)


@dataclasses.dataclass
class EngineTraits:
    """The class is intended to be instantiated for each engine."""

    regions: Dict[str, str] = dataclasses.field(default_factory=dict)
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

    languages: Dict[str, str] = dataclasses.field(default_factory=dict)
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

    all_locale: Optional[str] = None
    """To which locale value SearXNG's ``all`` language is mapped (shown a "Default
    language").
    """

    data_type: Literal['traits_v1', 'supported_languages'] = 'traits_v1'
    """Data type, default is 'traits_v1' for vintage use 'supported_languages'.

    .. hint::

       For the transition period until the *fetch* functions of all the engines
       are converted there will be the data_type 'supported_languages', which
       maps the old logic unchanged 1:1.

       Instances of data_type 'supported_languages' do not implement methods
       like ``self.get_language(..)`` and ``self.get_region(..)``

    """

    custom: Dict[str, Dict] = dataclasses.field(default_factory=dict)
    """A place to store engine's custom traits, not related to the SearXNG core

    """

    def get_language(self, searxng_locale: str, default=None):
        """Return engine's language string that *best fits* to SearXNG's locale.

        :param searxng_locale: SearXNG's internal representation of locale
          selected by the user.

        :param default: engine's default language

        The *best fits* rules are implemented in
        :py:obj:`locales.get_engine_locale`.  Except for the special value ``all``
        which is determined from :py:obj`EngineTraits.all_language`.
        """
        if searxng_locale == 'all' and self.all_locale is not None:
            return self.all_locale
        return locales.get_engine_locale(searxng_locale, self.languages, default=default)

    def get_region(self, searxng_locale: str, default=None):
        """Return engine's region string that best fits to SearXNG's locale.

        :param searxng_locale: SearXNG's internal representation of locale
          selected by the user.

        :param default: engine's default region

        The *best fits* rules are implemented in
        :py:obj:`locales.get_engine_locale`.  Except for the special value ``all``
        which is determined from :py:obj`EngineTraits.all_language`.
        """
        if searxng_locale == 'all' and self.all_locale is not None:
            return self.all_locale
        return locales.get_engine_locale(searxng_locale, self.regions, default=default)

    def is_locale_supported(self, searxng_locale: str) -> bool:
        """A *locale* (SearXNG's internal representation) is considered to be supported
        by the engine if the *region* or the *language* is supported by the
        engine.  For verification the functions :py:func:`self.get_region` and
        :py:func:`self.get_region` are used.
        """
        if self.data_type == 'traits_v1':
            return bool(self.get_region(searxng_locale) or self.get_language(searxng_locale))

        if self.data_type == 'supported_languages':  # vintage / deprecated
            # pylint: disable=import-outside-toplevel
            from searx.utils import match_language

            if searxng_locale == 'all':
                return True
            x = match_language(searxng_locale, self.supported_languages, self.language_aliases, None)
            return bool(x)

            # return bool(self.get_supported_language(searxng_locale))
        raise TypeError('engine traits of type %s is unknown' % self.data_type)

    def copy(self):
        """Create a copy of the dataclass object."""
        return EngineTraits(**dataclasses.asdict(self))

    @classmethod
    def fetch_traits(cls, engine: Engine) -> Union[Self, None]:
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

    def set_traits(self, engine: Engine):
        """Set traits from self object in a :py:obj:`.Engine` namespace.

        :param engine: engine instance build by :py:func:`searx.engines.load_engine`
        """

        if self.data_type == 'traits_v1':
            self._set_traits_v1(engine)

        elif self.data_type == 'supported_languages':  # vintage / deprecated
            self._set_supported_languages(engine)

        else:
            raise TypeError('engine traits of type %s is unknown' % self.data_type)

    def _set_traits_v1(self, engine: Engine):
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
        engine.traits = traits

    # -------------------------------------------------------------------------
    # The code below is deprecated an can hopefully be deleted at one day
    # -------------------------------------------------------------------------

    supported_languages: Union[List[str], Dict[str, str]] = dataclasses.field(default_factory=dict)
    """depricated: does not work for engines that do support languages based on a
    region.  With this type it is not guaranteed that the key values can be
    parsed by :py:obj:`babel.Locale.parse`!
    """

    # language_aliases: Dict[str, str] = dataclasses.field(default_factory=dict)
    # """depricated: does not work for engines that do support languages based on a
    # region.  With this type it is not guaranteed that the key values can be
    # parsed by :py:obj:`babel.Locale.parse`!
    # """

    BABEL_LANGS = [
        lang_parts[0] + '-' + lang_parts[-1] if len(lang_parts) > 1 else lang_parts[0]
        for lang_parts in (lang_code.split('_') for lang_code in locale_identifiers())
    ]

    # def get_supported_language(self, searxng_locale, default=None):  # vintage / deprecated
    #     """Return engine's language string that *best fits* to SearXNG's locale."""
    #     if searxng_locale == 'all' and self.all_locale is not None:
    #         return self.all_locale
    #     return locales.get_engine_locale(searxng_locale, self.supported_languages, default=default)

    @classmethod  # vintage / deprecated
    def fetch_supported_languages(cls, engine: Engine) -> Union[Self, None]:
        """DEPRECATED: Calls a function ``_fetch_supported_languages`` from engine's
        namespace to fetch languages from the origin engine.  If function does
        not exists, ``None`` is returned.
        """

        # pylint: disable=import-outside-toplevel
        from searx import network
        from searx.utils import gen_useragent

        fetch_languages = getattr(engine, '_fetch_supported_languages', None)
        if fetch_languages is None:
            return None

        # The headers has been moved here from commit 9b6ffed06: Some engines (at
        # least bing and startpage) return a different result list of supported
        # languages depending on the IP location where the HTTP request comes from.
        # The IP based results (from bing) can be avoided by setting a
        # 'Accept-Language' in the HTTP request.

        headers = {
            'User-Agent': gen_useragent(),
            'Accept-Language': "en-US,en;q=0.5",  # bing needs to set the English language
        }
        resp = network.get(engine.supported_languages_url, headers=headers)
        supported_languages = fetch_languages(resp)
        if isinstance(supported_languages, list):
            supported_languages.sort()

        engine_traits = cls()
        engine_traits.data_type = 'supported_languages'
        engine_traits.supported_languages = supported_languages
        return engine_traits

    def _set_supported_languages(self, engine: Engine):  # vintage / deprecated
        traits = self.copy()

        # pylint: disable=import-outside-toplevel
        from searx.utils import match_language

        _msg = "settings.yml - engine: '%s' / %s: '%s' not supported"

        if hasattr(engine, 'language'):
            if engine.language not in self.supported_languages:
                raise ValueError(_msg % (engine.name, 'language', engine.language))

            if isinstance(self.supported_languages, dict):
                traits.supported_languages = {engine.language: self.supported_languages[engine.language]}
            else:
                traits.supported_languages = [engine.language]

        engine.language_support = bool(traits.supported_languages)
        engine.supported_languages = traits.supported_languages

        # find custom aliases for non standard language codes
        traits.language_aliases = {}  # pylint: disable=attribute-defined-outside-init

        for engine_lang in getattr(engine, 'language_aliases', {}):
            iso_lang = match_language(engine_lang, self.BABEL_LANGS, fallback=None)
            if (
                iso_lang
                and iso_lang != engine_lang
                and not engine_lang.startswith(iso_lang)
                and iso_lang not in self.supported_languages
            ):
                traits.language_aliases[iso_lang] = engine_lang

        engine.language_aliases = traits.language_aliases

        # set the copied & modified traits in engine's namespace
        engine.traits = traits


class EngineTraitsMap(Dict[str, EngineTraits]):
    """A python dictionary to map :class:`EngineTraits` by engine name."""

    ENGINE_TRAITS_FILE = (data_dir / 'engine_traits.json').resolve()
    """File with persistence of the :py:obj:`EngineTraitsMap`."""

    def save_data(self):
        """Store EngineTraitsMap in in file :py:obj:`self.ENGINE_TRAITS_FILE`"""
        with open(self.ENGINE_TRAITS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self, f, indent=2, sort_keys=True, cls=EngineTraitsEncoder)

    @classmethod
    def from_data(cls) -> Self:
        """Instantiate :class:`EngineTraitsMap` object from :py:obj:`ENGINE_TRAITS`"""
        obj = cls()
        for k, v in ENGINE_TRAITS.items():
            obj[k] = EngineTraits(**v)
        return obj

    @classmethod
    def fetch_traits(cls, log: Callable) -> Self:
        from searx import engines  # pylint: disable=cyclic-import, import-outside-toplevel

        names = list(engines.engines)
        names.sort()
        obj = cls()

        for engine_name in names:
            engine = engines.engines[engine_name]

            traits = EngineTraits.fetch_traits(engine)
            if traits is not None:
                log("%-20s: SearXNG languages --> %s " % (engine_name, len(traits.languages)))
                log("%-20s: SearXNG regions   --> %s" % (engine_name, len(traits.regions)))
                obj[engine_name] = traits

            # vintage / deprecated
            _traits = EngineTraits.fetch_supported_languages(engine)
            if _traits is not None:
                log("%-20s: %s supported_languages (deprecated)" % (engine_name, len(_traits.supported_languages)))
                if traits is not None:
                    traits.supported_languages = _traits.supported_languages
                    obj[engine_name] = traits
                else:
                    obj[engine_name] = _traits
                continue

        return obj

    def set_traits(self, engine: Engine):
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
