# SPDX-License-Identifier: AGPL-3.0-or-later
"""Calculate mathematical expressions using ack#eval
"""

import re
import sys
import subprocess
from pathlib import Path

import flask
import babel
from flask_babel import gettext

from searx.plugins import logger

name = "Basic Calculator"
description = gettext("Calculate mathematical expressions via the search bar")
default_on = True

preference_section = 'general'
plugin_id = 'calculator'

logger = logger.getChild(plugin_id)


def call_calculator(query_py_formatted, timeout):
    calculator_process_py_path = Path(__file__).parent.absolute() / "calculator_process.py"
    # see https://docs.python.org/3/using/cmdline.html
    # -S Disable the import of the module site and the site-dependent manipulations
    #    of sys.path that it entails. Also disable these manipulations if site is
    #    explicitly imported later (call site.main() if you want them to be triggered).
    # -I Run Python in isolated mode. This also implies -E, -P and -s options.
    # -E Ignore all PYTHON* environment variables, e.g. PYTHONPATH and PYTHONHOME, that might be set.
    # -P Don’t prepend a potentially unsafe path to sys.path
    # -s Don’t add the user site-packages directory to sys.path.
    process = subprocess.Popen(  # pylint: disable=R1732
        [sys.executable, "-S", "-I", calculator_process_py_path, query_py_formatted],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        if process.returncode == 0 and not stderr:
            return stdout
        logger.debug("calculator exited with stderr %s", stderr)
        return None
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            # Give the process a grace period to terminate
            process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            # Forcefully kill the process
            process.kill()
            process.communicate()
        logger.debug("calculator terminated after timeout")
        # Capture any remaining output
        return None
    finally:
        # Ensure the process is fully cleaned up
        if process.poll() is None:  # If still running
            process.kill()
            process.communicate()


def post_search(_request, search):

    # only show the result of the expression on the first page
    if search.search_query.pageno > 1:
        return True

    query = search.search_query.query
    # in order to avoid DoS attacks with long expressions, ignore long expressions
    if len(query) > 100:
        return True

    # replace commonly used math operators with their proper Python operator
    query = query.replace("x", "*").replace(":", "/")

    # use UI language
    ui_locale = babel.Locale.parse(flask.request.preferences.get_value('locale'), sep='-')

    # parse the number system in a localized way
    def _decimal(match: re.Match) -> str:
        val = match.string[match.start() : match.end()]
        val = babel.numbers.parse_decimal(val, ui_locale, numbering_system="latn")
        return str(val)

    decimal = ui_locale.number_symbols["latn"]["decimal"]
    group = ui_locale.number_symbols["latn"]["group"]
    query = re.sub(f"[0-9]+[{decimal}|{group}][0-9]+[{decimal}|{group}]?[0-9]?", _decimal, query)

    # only numbers and math operators are accepted
    if any(str.isalpha(c) for c in query):
        return True

    # in python, powers are calculated via **
    query_py_formatted = query.replace("^", "**")

    # Prevent the runtime from being longer than 50 ms
    result = call_calculator(query_py_formatted, 0.05)
    if result is None or result == "":
        return True
    result = babel.numbers.format_decimal(result, locale=ui_locale)
    search.result_container.answers['calculate'] = {'answer': f"{search.search_query.query} = {result}"}
    return True
