# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module providing support for displaying data in OpenMetrics format"""


class OpenMetricsFamily:  # pylint: disable=too-few-public-methods
    """A family of metrics.
    The key parameter is the metric name that should be used (snake case).
    The type_hint parameter must be one of 'counter', 'gauge', 'histogram', 'summary'.
    The help_hint parameter is a short string explaining the metric.
    The data_info parameter is a dictionary of descriptionary parameters for the data point (e.g. request method/path).
    The data parameter is a flat list of the actual data in shape of a primitive type.

    See https://github.com/OpenObservability/OpenMetrics/blob/main/specification/OpenMetrics.md for more information.
    """

    def __init__(self, key: str, type_hint: str, help_hint: str, data_info: list, data: list):
        self.key = key
        self.type_hint = type_hint
        self.help_hint = help_hint
        self.data_info = data_info
        self.data = data

    def __str__(self):
        text_representation = f"""# HELP {self.key} {self.help_hint}
# TYPE {self.key} {self.type_hint}
"""

        for i, data_info_dict in enumerate(self.data_info):
            if not data_info_dict or not self.data[i]:
                continue

            info_representation = ','.join([f"{key}=\"{value}\"" for (key, value) in data_info_dict.items()])
            text_representation += f"{self.key}{{{info_representation}}} {self.data[i]}\n"

        return text_representation
