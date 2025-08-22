# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implement request processors used by engine-types."""

__all__ = [
    'EngineProcessor',
    'OfflineProcessor',
    'OnlineProcessor',
    'OnlineDictionaryProcessor',
    'OnlineCurrencyProcessor',
    'OnlineUrlSearchProcessor',
    'PROCESSORS',
]

import typing as t

import threading

from searx import logger
from searx import engines

from .online import OnlineProcessor
from .offline import OfflineProcessor
from .online_dictionary import OnlineDictionaryProcessor
from .online_currency import OnlineCurrencyProcessor
from .online_url_search import OnlineUrlSearchProcessor
from .abstract import EngineProcessor

if t.TYPE_CHECKING:
    from searx.enginelib import Engine

logger = logger.getChild('search.processors')
PROCESSORS: dict[str, EngineProcessor] = {}
"""Cache request processors, stored by *engine-name* (:py:func:`initialize`)

:meta hide-value:
"""


def get_processor_class(engine_type: str) -> type[EngineProcessor] | None:
    """Return processor class according to the ``engine_type``"""
    for c in [
        OnlineProcessor,
        OfflineProcessor,
        OnlineDictionaryProcessor,
        OnlineCurrencyProcessor,
        OnlineUrlSearchProcessor,
    ]:
        if c.engine_type == engine_type:
            return c
    return None


def get_processor(engine: "Engine | ModuleType", engine_name: str) -> EngineProcessor | None:
    """Return processor instance that fits to ``engine.engine.type``"""
    engine_type = getattr(engine, 'engine_type', 'online')
    processor_class = get_processor_class(engine_type)
    if processor_class is not None:
        return processor_class(engine, engine_name)
    return None


def initialize_processor(processor: EngineProcessor):
    """Initialize one processor

    Call the init function of the engine
    """
    if processor.has_initialize_function:
        _t = threading.Thread(target=processor.initialize, daemon=True)
        _t.start()


def initialize(engine_list: list[dict[str, t.Any]]):
    """Initialize all engines and store a processor for each engine in
    :py:obj:`PROCESSORS`."""
    for engine_data in engine_list:
        engine_name: str = engine_data['name']
        engine = engines.engines.get(engine_name)
        if engine:
            processor = get_processor(engine, engine_name)
            if processor is None:
                engine.logger.error('Error get processor for engine %s', engine_name)
            else:
                initialize_processor(processor)
                PROCESSORS[engine_name] = processor
