# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""A dummy service to demonstrate SearXNG service management"""

import os
import sys
import time


def main():

    print("This is arguments")
    print(f"{sys.argv}")
    print("This is environment", flush=True)
    for key, value in os.environ.items():
        print(f"{key} : {value}", flush=True)

    # this should be running for about 2 hours
    for i in range(1000):
        print(f"Iteration {i}...", flush=True)
        time.sleep(10)


if __name__ == "__main__":
    main()
