# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implement request processors used by engine-types."""

__all__ = [
    "OfflineParamTypes",
    "OnlineCurrenciesParams",
    "OnlineDictParams",
    "OnlineParamTypes",
    "OnlineParams",
    "OnlineUrlSearchParams",
    "PROCESSORS",
    "ParamTypes",
    "RequestParams",
]

import typing as t

from searx import logger
from searx import engines

from .abstract import EngineProcessor, RequestParams
from .offline import OfflineProcessor
from .online import OnlineProcessor, OnlineParams
from .online_dictionary import OnlineDictionaryProcessor, OnlineDictParams
from .online_currency import OnlineCurrencyProcessor, OnlineCurrenciesParams
from .online_url_search import OnlineUrlSearchProcessor, OnlineUrlSearchParams

logger = logger.getChild("search.processors")

OnlineParamTypes: t.TypeAlias = OnlineParams | OnlineDictParams | OnlineCurrenciesParams | OnlineUrlSearchParams
OfflineParamTypes: t.TypeAlias = RequestParams
ParamTypes: t.TypeAlias = OfflineParamTypes | OnlineParamTypes


class ProcessorMap(dict[str, EngineProcessor]):
    """Class to manage :py:obj:`EngineProcessor` instances in a key/value map
    (instances stored by *engine-name*)."""

    processor_types: dict[str, type[EngineProcessor]] = {
        OnlineProcessor.engine_type: OnlineProcessor,
        OfflineProcessor.engine_type: OfflineProcessor,
        OnlineDictionaryProcessor.engine_type: OnlineDictionaryProcessor,
        OnlineCurrencyProcessor.engine_type: OnlineCurrencyProcessor,
        OnlineUrlSearchProcessor.engine_type: OnlineUrlSearchProcessor,
    }

    def init(self, engine_list: list[dict[str, t.Any]]):
        """Initialize all engines and registers a processor for each engine."""

        for eng_settings in engine_list:
            eng_name: str = eng_settings["name"]

            if eng_settings.get("inactive", False) is True:
                continue

            eng_obj = engines.engines.get(eng_name)
            if eng_obj is None:
                logger.warning("Engine of name '%s' does not exists.", eng_name)
                continue

            eng_type = getattr(eng_obj, "engine_type", "online")
            proc_cls = self.processor_types.get(eng_type)
            if proc_cls is None:
                logger.error("Engine '%s' is of unknown engine_type: %s", eng_type)
                continue

            # initialize (and register) the engine
            eng_proc = proc_cls(eng_obj)
            eng_proc.initialize(self.register_processor)

    def register_processor(self, eng_proc: EngineProcessor, eng_proc_ok: bool) -> bool:
        """Register the :py:obj:`EngineProcessor`.

        This method is usually passed as a callback to the initialization of the
        :py:obj:`EngineProcessor`.

        The value (true/false) passed in ``eng_proc_ok`` indicates whether the
        initialization of the :py:obj:`EngineProcessor` was successful; if this
        is not the case, the processor is not registered.
        """

        if eng_proc_ok:
            self[eng_proc.engine.name] = eng_proc
            # logger.debug("registered engine processor: %s", eng_proc.engine.name)
        else:
            logger.error("can't register engine processor: %s (init failed)", eng_proc.engine.name)

        return eng_proc_ok


PROCESSORS = ProcessorMap()
"""Global :py:obj:`ProcessorMap`.

:meta hide-value:
"""
