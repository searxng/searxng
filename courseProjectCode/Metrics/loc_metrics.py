#!/usr/bin/env python3

"""
count lines of code in each file in the /searx directory 

Use:
    cd courseProjectCode/Metrics
    python3 loc_metrics.py ../../searx
"""

import os
import sys

scanned_folder = sys.argv[1]

results = []

for current_folder, list_of_subfolders, list_of_files in os.walk(scanned_folder):
    for filename in list_of_files:

        if not filename.endswith(".py"):
            continue

        path = os.path.join(current_folder, filename)

        with open(path, "r", encoding="utf-8", errors="replace") as open_file:
            lines = open_file.readlines()
            number_of_lines = len(lines)

        results.append((path, number_of_lines))


print(f"lines of code per file: {scanned_folder}")

total_folder_lines = 0

for file_path, number_of_lines in results:
    print(f"{file_path} : {number_of_lines}")
    total_folder_lines += number_of_lines

print(f"total files: {len(results)}")
print(f"total lines: {total_folder_lines}")