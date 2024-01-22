# SPDX-License-Identifier: AGPL-3.0-or-later
"""build environment used by shell scripts
"""

# set path
import sys
import importlib.util
import re

from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent


def main(setting_name):

    settings_path = repo_root / "searx" / "settings.yml"
    with open(settings_path) as f:
        settings = parse_yaml(f.read())
    print(get_setting_value(settings, setting_name))


def get_setting_value(settings, name):
    value = settings
    for a in name.split("."):
        value = value[a]
    if value is True:
        value = "1"
    elif value is False:
        value = ""
    return value


def parse_yaml(yaml_str):
    """A simple YAML parser that converts a YAML string to a Python dictionary.
    This parser can handle nested dictionaries, but does not handle list or JSON
    like structures.

    Good enough parser to get the values of server.base_url, server.port and
    server.bind_address

    """

    def get_type_and_value_without_comment(line):
        """Extract value without comment and quote

        Returns a tuple:

        1. str or None: str when the value is written inside quote, None otherwise
        2. the value without quote if any
        """
        match = re.search(r"\"(.*)\"(\s+#)?|\'(.*)\'(\s+#)?|([^#]*)(\s+#)?", line)
        if match:
            g = match.groups()
            if g[0] is not None:
                return str, g[0]
            elif g[2] is not None:
                return str, g[2]
            elif g[4] is not None:
                return None, g[4].strip()
        return None, line.strip()

    # fmt: off
    true_values = ("y", "Y", "yes", "Yes", "YES", "true", "True", "TRUE", "on", "On", "ON",)
    false_values = ("n", "N", "no", "No", "NO", "false", "False", "FALSE", "off", "Off", "OFF",)
    # fmt: on

    def process_line(line):
        """Extract key and value from a line, considering its indentation."""
        if ": " in line:
            key, value = line.split(": ", 1)
            key = key.strip()
            value_type, value = get_type_and_value_without_comment(value)
            if value in true_values and value_type is None:
                value = True
            elif value in false_values and value_type is None:
                value = False
            elif value.replace(".", "").isdigit() and value_type is None:
                for t in (int, float):
                    try:
                        value = t(value)
                        break
                    except ValueError:
                        continue
            return key, value
        return None, None

    def get_indentation_level(line):
        """Determine the indentation level of a line."""
        return len(line) - len(line.lstrip())

    yaml_dict = {}
    lines = yaml_str.split("\n")
    stack = [yaml_dict]

    for line in lines:
        if not line.strip():
            continue  # Skip empty lines

        indentation_level = get_indentation_level(line)
        # Assuming 2 spaces per indentation level
        # see .yamllint.yml
        current_level = indentation_level // 2

        # Adjust the stack based on the current indentation level
        while len(stack) > current_level + 1:
            stack.pop()

        if line.endswith(":"):
            key = line[0:-1].strip()
            new_dict = {}
            stack[-1][key] = new_dict
            stack.append(new_dict)
        else:
            key, value = process_line(line)
            if key is not None:
                stack[-1][key] = value

    return yaml_dict


if __name__ == "__main__":
    main(sys.argv[1])
