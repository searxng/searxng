#!/usr/bin/env python3

"""
count comment density in each file in the /searx directory

Use:
    cd courseProjectCode/Metrics
    python3 comment_density_metrics.py ../../searx
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
            total_lines = len(lines)

        if total_lines == 0:
            continue

        number_of_comment_lines = 0

        for line in lines:
            if line.strip().startswith("#"):
                number_of_comment_lines += 1

        density = number_of_comment_lines / total_lines

        results.append((path, total_lines, number_of_comment_lines, density))


print(f"comment density per file: {scanned_folder}")

total_folder_lines = 0
total_folder_comment_lines = 0

for file_path, total_lines, number_of_comment_lines, density in results:
    print(f"{file_path} : {number_of_comment_lines} / {total_lines} lines ({density:.2%})")
    total_folder_lines += total_lines
    total_folder_comment_lines += number_of_comment_lines

print(f"total files: {len(results)}")
print(f"total lines: {total_folder_lines}")
print(f"total comment lines: {total_folder_comment_lines}")


overall_density = total_folder_comment_lines / total_folder_lines
print(f"comment density: {overall_density:.2%}")