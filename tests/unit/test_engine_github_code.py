# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring

import logging
from unittest.mock import Mock
from urllib.parse import urlparse
from parameterized import parameterized

import searx.engines
from tests import SearxTestCase
from searx.result_types import EngineResults


class GithubCodeTests(SearxTestCase):

    TEST_SETTINGS = "test_github_code.yml"

    def setUp(self):
        super().setUp()
        self.ghc = searx.engines.engines['github code']
        self.ghc.logger.setLevel(logging.INFO)

    def tearDown(self):
        searx.search.load_engines([])

    @parameterized.expand(
        [
            [
                [
                    {
                        "fragment": "    - [Tab management](#tab-management)\n    - [Buffer/window management]"
                        "(#bufferwindow-management)\n- [🎨 Highlights](#-highlights)",
                        "matches": [{"indices": [47, 53], "text": "Buffer"}, {"indices": [74, 80], "text": "buffer"}],
                    },
                    {
                        "fragment": "To conditionally activate plugins, the best solution is to use the\n"
                        "[LazyVim VSCode extra](https://www.lazyvim.org/extras/vscode). However, "
                        "`packer.nvim` and `lazy.nvim` have built-in\nsupport for "
                        "`cond = vim.g.vscode` and `vim-plug` has a",
                        "matches": [
                            {"indices": [68, 75], "text": "LazyVim"},
                            {"indices": [102, 109], "text": "lazyvim"},
                        ],
                    },
                ],
                [
                    "    - [Tab management](#tab-management)",
                    "    - [Buffer/window management](#bufferwindow-management)",
                    "- [🎨 Highlights](#-highlights)",
                    "To conditionally activate plugins, the best solution is to use the",
                    "[LazyVim VSCode extra](https://www.lazyvim.org/extras/vscode)."
                    " However, `packer.nvim` and `lazy.nvim` have built-in",
                    "support for `cond = vim.g.vscode` and `vim-plug` has a",
                ],
                {2, 5},
            ],
            [
                [
                    {
                        "fragment": "\n| `<leader>uf` | Toggle format (global) |\n"
                        "| `<leader>uF` | Toggle format (buffer) |\n"
                        "| `<leader>us` | Toggle spelling |\n",
                        "matches": [{"indices": [74, 80], "text": "buffer"}],
                    },
                ],
                [
                    "| `<leader>uf` | Toggle format (global) |",
                    "| `<leader>uF` | Toggle format (buffer) |",
                    "| `<leader>us` | Toggle spelling |",
                ],
                {2},
            ],
            [
                [
                    {
                        "fragment": "\n\n\n1\n2\n3\n4",
                        "matches": [{"indices": [3, 4], "text": "1"}],
                    },
                ],
                [
                    "1",
                    "2",
                    "3",
                    "4",
                ],
                {1},
            ],
            [
                [
                    {
                        "fragment": "placeholder",
                        "matches": [],
                    },
                ],
                [
                    "placeholder",
                ],
                set(),
            ],
        ]
    )
    def test_code_extraction(self, code_matches, expected_code, expected_highlighted_lines):
        code, highlights = self.ghc.extract_code(code_matches=code_matches)
        self.assertEqual(code, expected_code)
        self.assertEqual(highlights, expected_highlighted_lines)

    def test_transforms_response(self):
        response = Mock()
        response.json.return_value = {
            "items": [
                {
                    "name": "TODO.md",
                    "path": "TODO.md",
                    "html_url": "https://github.com/folke/dot/blob/3140f4f5720c3cc6b5034c624eb7706f8533a82c/TODO.md",
                    "repository": {
                        "full_name": "folke/dot",
                        "html_url": "https://github.com/folke/dot",
                        "description": "☕️   My Dot Files",
                    },
                    "text_matches": [
                        {
                            "object_type": "FileContent",
                            "property": "content",
                            "fragment": "- [x] windows picker\n"
                            "- [x] toggle cwd / root (LazyVim)\n"
                            "- [x] dynamic workspace symbol",
                            "matches": [{"indices": [46, 53], "text": "LazyVim"}],
                        },
                        {
                            "object_type": "FileContent",
                            "property": "content",
                            "fragment": "- [x] smart stops working after custom\n"
                            "- [x] edit in empty buffer\n"
                            "- [x] support toggling line nr for preview",
                            "matches": [{"indices": [59, 65], "text": "buffer"}, {"indices": [89, 93], "text": "line"}],
                        },
                    ],
                }
            ]
        }
        response.status_code = 200
        results = self.ghc.response(response)
        expected_results = EngineResults()
        expected_results.add(
            expected_results.types.Code(
                url="https://github.com/folke/dot/blob/3140f4f5720c3cc6b5034c624eb7706f8533a82c/TODO.md",
                title="folke/dot · TODO.md",
                content="☕️   My Dot Files",
                repository="https://github.com/folke/dot",
                codelines=[
                    (1, "- [x] windows picker"),
                    (2, "- [x] toggle cwd / root (LazyVim)"),
                    (3, "- [x] dynamic workspace symbol"),
                    (4, "- [x] smart stops working after custom"),
                    (5, "- [x] edit in empty buffer"),
                    (6, "- [x] support toggling line nr for preview"),
                ],
                hl_lines={2, 5, 6},
                code_language="markdown",
                strip_whitespace=False,
                strip_new_lines=True,
                parsed_url=urlparse(
                    "https://github.com/folke/dot/blob/3140f4f5720c3cc6b5034c624eb7706f8533a82c/TODO.md"
                ),
            )
        )
        self.assertEqual(results, expected_results)
