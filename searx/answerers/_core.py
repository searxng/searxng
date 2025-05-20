# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=too-few-public-methods, missing-module-docstring

from __future__ import annotations

import abc
import importlib
import logging
import pathlib
import warnings

from dataclasses import dataclass

from searx.utils import load_module
from searx.result_types.answer import BaseAnswer


_default = pathlib.Path(__file__).parent
log: logging.Logger = logging.getLogger("searx.answerers")


@dataclass
class AnswererInfo:
    """Object that holds information about an answerer, these infos are shown
    to the user in the Preferences menu.

    To be able to translate the information into other languages, the text must
    be written in English and translated with :py:obj:`flask_babel.gettext`.
    """

    name: str
    """Name of the *answerer*."""

    description: str
    """Short description of the *answerer*."""

    examples: list[str]
    """List of short examples of the usage / of query terms."""

    keywords: list[str]
    """See :py:obj:`Answerer.keywords`"""


class Answerer(abc.ABC):
    """Abstract base class of answerers."""

    keywords: list[str]
    """Keywords to which the answerer has *answers*."""

    @abc.abstractmethod
    def answer(self, query: str) -> list[BaseAnswer]:
        """Function that returns a list of answers to the question/query."""

    @abc.abstractmethod
    def info(self) -> AnswererInfo:
        """Information about the *answerer*, see :py:obj:`AnswererInfo`."""


class ModuleAnswerer(Answerer):
    """A wrapper class for legacy *answerers* where the names (keywords, answer,
    info) are implemented on the module level (not in a class).

    .. note::

       For internal use only!
    """

    def __init__(self, mod):

        for name in ["keywords", "self_info", "answer"]:
            if not getattr(mod, name, None):
                raise SystemExit(2)
        if not isinstance(mod.keywords, tuple):
            raise SystemExit(2)

        self.module = mod
        self.keywords = mod.keywords  # type: ignore

    def answer(self, query: str) -> list[BaseAnswer]:
        return self.module.answer(query)

    def info(self) -> AnswererInfo:
        kwargs = self.module.self_info()
        kwargs["keywords"] = self.keywords
        return AnswererInfo(**kwargs)


class AnswerStorage(dict):
    """A storage for managing the *answerers* of SearXNG.  With the
    :py:obj:`AnswerStorage.ask`” method, a caller can ask questions to all
    *answerers* and receives a list of the results."""

    answerer_list: set[Answerer]
    """The list of :py:obj:`Answerer` in this storage."""

    def __init__(self):
        super().__init__()
        self.answerer_list = set()

    def load_builtins(self):
        """Loads ``answerer.py`` modules from the python packages in
        :origin:`searx/answerers`.  The python modules are wrapped by
        :py:obj:`ModuleAnswerer`."""

        for f in _default.iterdir():
            if f.name.startswith("_"):
                continue

            if f.is_file() and f.suffix == ".py":
                self.register_by_fqn(f"searx.answerers.{f.stem}.SXNGAnswerer")
                continue

            # for backward compatibility (if a fork has additional answerers)

            if f.is_dir() and (f / "answerer.py").exists():
                warnings.warn(
                    f"answerer module {f} is deprecated / migrate to searx.answerers.Answerer", DeprecationWarning
                )
                mod = load_module("answerer.py", str(f))
                self.register(ModuleAnswerer(mod))

    def register_by_fqn(self, fqn: str):
        """Register a :py:obj:`Answerer` via its fully qualified class namen(FQN)."""

        mod_name, _, obj_name = fqn.rpartition('.')
        mod = importlib.import_module(mod_name)
        code_obj = getattr(mod, obj_name, None)

        if code_obj is None:
            msg = f"answerer {fqn} is not implemented"
            log.critical(msg)
            raise ValueError(msg)

        self.register(code_obj())

    def register(self, answerer: Answerer):
        """Register a :py:obj:`Answerer`."""

        self.answerer_list.add(answerer)
        for _kw in answerer.keywords:
            self[_kw] = self.get(_kw, [])
            self[_kw].append(answerer)

    def ask(self, query: str) -> list[BaseAnswer]:
        """An answerer is identified via keywords, if there is a keyword at the
        first position in the ``query`` for which there is one or more
        answerers, then these are called, whereby the entire ``query`` is passed
        as argument to the answerer function."""

        results = []
        keyword = None
        for keyword in query.split():
            if keyword:
                break

        if not keyword or keyword not in self:
            return results

        for answerer in self[keyword]:
            for answer in answerer.answer(query):
                # In case of *answers* prefix ``answerer:`` is set, see searx.result_types.Result
                answer.engine = f"answerer: {keyword}"
                results.append(answer)

        return results

    @property
    def info(self) -> list[AnswererInfo]:
        return [a.info() for a in self.answerer_list]
