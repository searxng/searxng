# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring

import sys
import io
import os
import argparse
import logging

import searx.search
import searx.search.checker
from searx.search import PROCESSORS
from searx.engines import engine_shortcuts


# configure logging
root = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
for h in root.handlers:
    root.removeHandler(h)
root.addHandler(handler)

# color only for a valid terminal
if sys.stdout.isatty() and os.environ.get('TERM') not in ['dumb', 'unknown']:
    RESET_SEQ = "\033[0m"
    COLOR_SEQ = "\033[1;%dm"
    BOLD_SEQ = "\033[1m"
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = map(lambda i: COLOR_SEQ % (30 + i), range(8))
else:
    RESET_SEQ = ""
    COLOR_SEQ = ""
    BOLD_SEQ = ""
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = "", "", "", "", "", "", "", ""

# equivalent of 'python -u' (unbuffered stdout, stderr)
stdout = io.TextIOWrapper(
    # pylint: disable=consider-using-with
    open(sys.stdout.fileno(), 'wb', 0),
    write_through=True,
)
stderr = io.TextIOWrapper(
    # pylint: disable=consider-using-with
    open(sys.stderr.fileno(), 'wb', 0),
    write_through=True,
)


# iterator of processors
def iter_processor(engine_name_list):
    if len(engine_name_list) > 0:
        for name in engine_name_list:
            name = engine_shortcuts.get(name, name)
            processor = PROCESSORS.get(name)
            if processor is not None:
                yield name, processor
            else:
                stdout.write(f'{BOLD_SEQ}Engine {name:30}{RESET_SEQ}{RED}Engine does not exist{RESET_SEQ}')
    else:
        for name, processor in searx.search.PROCESSORS.items():
            yield name, processor


# actual check & display
def run(engine_name_list, verbose):
    searx.search.initialize()
    for name, processor in iter_processor(engine_name_list):
        stdout.write(f'{BOLD_SEQ}Engine {name:30}{RESET_SEQ}Checking\n')
        if not sys.stdout.isatty():
            stderr.write(f'{BOLD_SEQ}Engine {name:30}{RESET_SEQ}Checking\n')
        checker = searx.search.checker.Checker(processor)
        checker.run()
        if checker.test_results.successful:
            stdout.write(f'{BOLD_SEQ}Engine {name:30}{RESET_SEQ}{GREEN}OK{RESET_SEQ}\n')
            if verbose:
                stdout.write(f'    {"found languages":15}: {" ".join(sorted(list(checker.test_results.languages)))}\n')
        else:
            stdout.write(f'{BOLD_SEQ}Engine {name:30}{RESET_SEQ}{RESET_SEQ}{RED}Error{RESET_SEQ}')
            if not verbose:
                errors = [test_name + ': ' + error for test_name, error in checker.test_results]
                stdout.write(f'{RED}Error {str(errors)}{RESET_SEQ}\n')
            else:
                stdout.write('\n')
                stdout.write(f'    {"found languages":15}: {" ".join(sorted(list(checker.test_results.languages)))}\n')
                for test_name, logs in checker.test_results.logs.items():
                    for log in logs:
                        log = map(lambda l: l if isinstance(l, str) else repr(l), log)
                        stdout.write(f'    {test_name:15}: {RED}{" ".join(log)}{RESET_SEQ}\n')


# call by setup.py
def main():
    parser = argparse.ArgumentParser(description='Check searx engines.')
    parser.add_argument(
        'engine_name_list',
        metavar='engine name',
        type=str,
        nargs='*',
        help='engines name or shortcut list. Empty for all engines.',
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        dest='verbose',
        help='Display details about the test results',
        default=False,
    )
    args = parser.parse_args()
    run(args.engine_name_list, args.verbose)


if __name__ == '__main__':
    main()
