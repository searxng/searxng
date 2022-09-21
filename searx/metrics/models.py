# SPDX-License-Identifier: AGPL-3.0-or-later

import decimal
from numbers import Number
import threading
from typing import Dict, List, Optional, Tuple

from searx import logger


__all__ = ["Histogram", "HistogramStorage", "CounterStorage"]

logger = logger.getChild('searx.metrics')


class Histogram:

    _slots__ = '_lock', '_size', '_sum', '_quartiles', '_count', '_width'

    def __init__(self, width: int = 10, size: int = 200):
        """
        * width: quantile width
        * size: number of quantiles
        """
        self._lock = threading.Lock()
        self._width = width
        self._size = size
        self._quartiles = [0] * size
        self._count: int = 0
        self._sum: int = 0

    def observe(self, value: Number):
        q = int(value / self._width)
        if q < 0:
            """Value below zero is ignored"""
            q = 0
        if q >= self._size:
            """Value above the maximum is replaced by the maximum"""
            q = self._size - 1
        with self._lock:
            self._quartiles[q] += 1
            self._count += 1
            self._sum += value

    @property
    def quartiles(self) -> List[int]:
        return list(self._quartiles)

    @property
    def count(self) -> int:
        return self._count

    @property
    def sum(self) -> int:
        return self._sum

    @property
    def average(self) -> float:
        with self._lock:
            if self._count != 0:
                return self._sum / self._count
            else:
                return 0

    @property
    def quartile_percentages(self) -> List[int]:
        """Quartile in percentage"""
        with self._lock:
            if self._count > 0:
                return [int(q * 100 / self._count) for q in self._quartiles]
            else:
                return self._quartiles

    def percentile(self, percentage: Number) -> Optional[decimal.Decimal]:
        """
        Return the percentile.

        * percentage from 0 to 100
        """
        # use Decimal to avoid rounding errors
        x = decimal.Decimal(0)
        width = decimal.Decimal(self._width)
        stop_at_value = decimal.Decimal(self._count) / 100 * percentage
        sum_value = 0
        with self._lock:
            if self._count > 0:
                for y in self._quartiles:
                    sum_value += y
                    if sum_value >= stop_at_value:
                        return x
                    x += width
        return None

    def __repr__(self):
        return "Histogram<avg: " + str(self.average) + ", count: " + str(self._count) + ">"


class HistogramStorage:

    __slots__ = 'measures', 'histogram_class'

    def __init__(self, histogram_class=Histogram):
        self.clear()
        self.histogram_class = histogram_class

    def clear(self):
        self.measures: Dict[Tuple[str], Histogram] = {}

    def configure(self, width, size, *args):
        measure = self.histogram_class(width, size)
        self.measures[args] = measure
        return measure

    def get(self, *args, raise_on_not_found=True) -> Optional[Histogram]:
        h = self.measures.get(args, None)
        if raise_on_not_found and h is None:
            raise ValueError("histogram " + repr((*args,)) + " doesn't not exist")
        return h

    def observe(self, duration, *args):
        self.get(*args).observe(duration)

    def dump(self):
        logger.debug("Histograms:")
        ks = sorted(self.measures.keys(), key='/'.join)
        for k in ks:
            logger.debug("- %-60s %s", '|'.join(k), self.measures[k])


class CounterStorage:

    __slots__ = 'counters', 'lock'

    def __init__(self):
        self.lock = threading.Lock()
        self.clear()

    def clear(self):
        with self.lock:
            self.counters: Dict[Tuple[str], int] = {}

    def configure(self, *args):
        with self.lock:
            self.counters[args] = 0

    def get(self, *args) -> int:
        return self.counters[args]

    def inc(self, *args):
        self.add(1, *args)

    def add(self, value, *args):
        with self.lock:
            self.counters[args] += value

    def dump(self):
        with self.lock:
            ks = sorted(self.counters.keys(), key='/'.join)
        logger.debug("Counters:")
        for k in ks:
            logger.debug("- %-60s %s", '|'.join(k), self.counters[k])


class VoidHistogram(Histogram):
    def observe(self, value):
        pass


class VoidCounterStorage(CounterStorage):
    def add(self, value, *args):
        pass
