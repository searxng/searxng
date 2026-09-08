#!/usr/bin/env python3

"""
count test cases and test suites in the /tests directory

Use:
    cd courseProjectCode/Metrics
    python3 testability_metrics.py ../..
"""

import os
import sys
import ast

repo_folder = sys.argv[1]
tests_folder = os.path.join(repo_folder, "tests")

results = []

for current_folder, list_of_subfolders, list_of_files in os.walk(tests_folder):
    for filename in list_of_files:

        if not filename.endswith(".py"):
            continue

        if filename == "__init__.py":
            continue

        path = os.path.join(current_folder, filename)

        with open(path, "r", encoding="utf-8", errors="replace") as open_file:
            source = open_file.read()

        tree = ast.parse(source)

        number_of_test_cases = 0
        number_of_test_suites = 0

        for node in ast.iter_child_nodes(tree):

            # 'class TestEnginesInit(SearxTestCase):'
            if isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    number_of_test_suites += 1

                    # 'def test_initialize_engines_default(self):'
                    for sub_node in node.body:
                        if isinstance(sub_node, ast.FunctionDef):
                            if sub_node.name.startswith("test_"):
                                number_of_test_cases += 1

        results.append((path, number_of_test_cases, number_of_test_suites))


print(f"test cases per file: {tests_folder}")

total_test_cases = 0
total_test_suites = 0

for file_path, number_of_test_cases, number_of_test_suites in results:
    print(f"{file_path} : {number_of_test_suites} suites, {number_of_test_cases} test cases")
    total_test_cases += number_of_test_cases
    total_test_suites += number_of_test_suites

print(f"total files: {len(results)}")
print(f"total test suites: {total_test_suites}")
print(f"total test cases: {total_test_cases}")