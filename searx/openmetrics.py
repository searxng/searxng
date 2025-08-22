# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module providing support for displaying data in OpenMetrics format"""

import typing as t

OMFTypeHintType = t.Literal["counter", "gauge", "histogram", "summary"]
OMFDataInfoType = list[dict[str, str]]
OMFDataType = list[t.Any]


class OpenMetricsFamily:  # pylint: disable=too-few-public-methods
    """A family of metrics.

    - The ``key`` parameter is the metric name that should be used (snake case).
    - The ``type_hint`` parameter must be one of ``counter``, ``gauge``,
      ``histogram``, ``summary``.
    - The ``help_hint`` parameter is a short string explaining the metric.
    - The data_info parameter is a dictionary of descriptionary parameters for
      the data point (e.g. request method/path).

    - The data parameter is a flat list of the actual data in shape of a
      primitive type.

    See `OpenMetrics specification`_ for more information.

    .. _OpenMetrics specification:
       https://github.com/prometheus/OpenMetrics/blob/main/specification/OpenMetrics.txt

    """

    def __init__(
        self, key: str, type_hint: OMFTypeHintType, help_hint: str, data_info: OMFDataInfoType, data: list[t.Any]
    ):
        self.key: str = key
        self.type_hint: OMFTypeHintType = type_hint
        self.help_hint: str = help_hint
        self.data_info: OMFDataInfoType = data_info
        self.data: OMFDataType = data

    def __str__(self):
        text_representation = f"""\
# HELP {self.key} {self.help_hint}
# TYPE {self.key} {self.type_hint}
"""

        for i, data_info_dict in enumerate(self.data_info):
            if not data_info_dict or not self.data[i]:
                continue

            info_representation = ','.join([f'{key}="{value}"' for (key, value) in data_info_dict.items()])
            text_representation += f'{self.key}{{{info_representation}}} {self.data[i]}\n'

        return text_representation
